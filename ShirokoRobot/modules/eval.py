import ast
import io
import os
import sys
import textwrap
import traceback
from contextlib import redirect_stdout
from inspect import getfullargspec
from io import StringIO
from time import time

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler

from ShirokoRobot import DEV_USERS, LOGGER, SHIROKO_PTB
from ShirokoRobot import pgram
from ShirokoRobot.modules.helper_funcs.chat_status import dev_plus

Shikoro_PYRO_Eval = filters.command(["eval", "e"])
namespaces = {}


def namespace_of(chat, update, bot):
    if chat not in namespaces:
        namespaces[chat] = {
            "__builtins__": globals()["__builtins__"],
            "bot": bot,
            "effective_message": update.effective_message,
            "effective_user": update.effective_user,
            "effective_chat": update.effective_chat,
            "update": update,
        }
    return namespaces[chat]


def log_input(update):
    user = update.effective_user.id
    chat = update.effective_chat.id
    LOGGER.info(
        f"IN: {update.effective_message.text} (user={user}, chat={chat})")


async def send(msg, bot, update):
    if len(str(msg)) > 2000:
        with io.BytesIO(str.encode(msg)) as out_file:
            out_file.name = "output.txt"
            await bot.send_document(chat_id=update.effective_chat.id,
                                    document=out_file)
    else:
        LOGGER.info(f"OUT: '{msg}'")
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"`{msg}`",
            parse_mode=ParseMode.MARKDOWN,
        )


async def aexec(code, client, message):
    exec("async def __aexec(client, message): " +
         "".join(f"\n {a}" for a in code.split("\n")))
    return await locals()["__aexec"](client, message)


async def edit_or_reply(msg: Message, **kwargs):
    func = msg.edit_text if msg.from_user.is_self else msg.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items() if k in spec})


@dev_plus
async def execute(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    await send((await do(exec, bot, update)), bot, update)


def cleanup_code(code):
    if code.startswith("```") and code.endswith("```"):
        return "\n".join(code.split("\n")[1:-1])
    return code.strip("` \n")


async def do(func, bot, update):
    log_input(update)
    content = await update.message.text.split(" ", 1)[-1]
    body = cleanup_code(content)
    env = namespace_of(update.message.chat_id, update, bot)
    os.chdir(os.getcwd())
    with open(
            os.path.join(os.getcwd(),
                         "ShirokoRobot/modules/helper_funcs/temp.txt"),
            "w",
    ) as temp:
        temp.write(body)
    stdout = io.StringIO()
    to_compile = f'def func():\n{textwrap.indent(body, "  ")}'
    try:
        exec(to_compile, env)
    except Exception as e:
        return f"{e.__class__.__name__}: {e}"
    func = env["func"]
    try:
        with redirect_stdout(stdout):
            func_return = func()
    except Exception:
        value = stdout.getvalue()
        return f"{value}{traceback.format_exc()}"
    else:
        value = stdout.getvalue()
        result = None
        if func_return is None:
            if value:
                result = f"{value}"
            else:
                try:
                    result = f"{repr(ast.literal_eval(body, env))}"
                except:
                    pass
        else:
            result = f"{value}{func_return}"
        if result:
            return result


@pgram.on_message(Shikoro_PYRO_Eval & filters.user(DEV_USERS) &
                  (~filters.forwarded) & (~filters.via_bot))
@pgram.on_edited_message(Shikoro_PYRO_Eval)
async def executor(client, message):
    try:
        cmd = message.text.split(" ", maxsplit=1)[1]
    except IndexError:
        return await message.delete()
    t1 = time()
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, client, message)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    final_output = f"**OUTPUT**:\n```{evaluation.strip()}```"
    if len(final_output) > 4096:
        filename = "output.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(str(evaluation.strip()))
        t2 = time()
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="⏳",
                callback_data=f"runtime {t2-t1} Seconds",
            )
        ]])
        await message.reply_document(
            document=filename,
            caption=
            f"**INPUT:**\n`{cmd[:980]}`\n\n**OUTPUT:**\n`Attached Document`",
            quote=False,
            reply_markup=keyboard,
        )

        await message.delete()
        os.remove(filename)
    else:
        t2 = time()
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="⏳",
                callback_data=f"runtime {round(t2-t1, 3)} Seconds",
            )
        ]])
        await edit_or_reply(message, text=final_output, reply_markup=keyboard)


@pgram.on_callback_query(filters.regex(r"runtime"))
async def runtime_func_cq(_, cq):
    runtime = cq.data.split(None, 1)[1]
    await cq.answer(runtime, show_alert=True)


@dev_plus
async def clear(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    log_input(update)
    if update.message.chat_id in namespaces:
        del namespaces[update.message.chat_id]
    await send("Cleared locals.", bot, update)


SHIROKO_PTB.add_handler(
    CommandHandler(("x", "ex", "exe", "py"), execute, block=False))
SHIROKO_PTB.add_handler(CommandHandler("clearlocals", clear, block=False))

__mod_name__ = "Eval Module"
