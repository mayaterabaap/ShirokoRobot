import asyncio
from typing import Union

from future.utils import string_types
from telegram import Update
from telegram.constants import ParseMode, ChatType
from telegram.ext import CommandHandler, MessageHandler, CallbackContext
from telegram.helpers import escape_markdown
from ShirokoRobot import SHIROKO_PTB
from ShirokoRobot.modules.helper_funcs.handlers import CMD_STARTERS
from ShirokoRobot.modules.helper_funcs.misc import is_module_loaded
from ShirokoRobot.modules.helper_funcs.alternate import send_message
from ShirokoRobot.modules.connection import connected

CMD_STARTERS = tuple(CMD_STARTERS)

FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):
    from ShirokoRobot.modules.helper_funcs.chat_status import (
        is_user_admin, )
    from ShirokoRobot.modules.helper_funcs.anonymous import user_admin

    from ShirokoRobot.modules.sql import disable_sql as sql

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    class DisableAbleCommandHandler(CommandHandler):

        def __init__(self,
                     command,
                     callback,
                     block=False,
                     admin_ok=False,
                     **kwargs):
            super().__init__(command, callback, **kwargs)
            self.admin_ok = admin_ok
            if isinstance(command, string_types):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)

        def check_update(self, update):
            if not isinstance(update, Update) or not update.effective_message:
                return
            message = update.effective_message

            if message.text and len(message.text) > 1:
                fst_word = message.text.split(None, 1)[0]
                if len(fst_word) > 1 and any(
                        fst_word.startswith(start) for start in CMD_STARTERS):
                    args = message.text.split()[1:]
                    command = fst_word[1:].split("@")
                    command.append(message._bot.username)

                    if not (frozenset({command[0].lower()}) in self.commands
                            and command[1].lower()
                            == message._bot.username.lower()):
                        return None

                    if filter_result := self.filters.check_update(update):
                        chat = update.effective_chat
                        user = update.effective_user
                        # disabled, admincmd, user admin
                        if sql.is_command_disabled(chat.id,
                                                   command[0].lower()):
                            # check if command was disabled
                            is_ad = asyncio.ensure_future(
                                is_user_admin(update, user.id))
                            is_disabled = command[0] in ADMIN_CMDS and is_ad
                            return (args,
                                    filter_result) if is_disabled else None
                        return args, filter_result
                    return False

    class DisableAbleMessageHandler(MessageHandler):

        def __init__(self,
                     pattern,
                     callback,
                     block=False,
                     friendly="",
                     **kwargs):
            super().__init__(pattern, callback, **kwargs)
            DISABLE_OTHER.append(friendly or pattern)
            self.friendly = friendly or pattern

        def check_update(self, update: object):
            if isinstance(update, Update) and update.effective_message:
                chat = update.effective_chat
                return self.filters.check_update(
                    update) and not sql.is_command_disabled(
                        chat.id, self.friendly)

    @user_admin
    async def disable(update: Update, context: CallbackContext) -> None:
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user
        args = context.args

        conn = await connected(context.bot,
                               update,
                               chat,
                               user.id,
                               need_admin=True)
        if conn:
            chat = SHIROKO_PTB.bot.getChat(conn)
            chat_name = SHIROKO_PTB.bot.getChat(conn).title
        else:
            if update.effective_message.chat.type == ChatType.PRIVATE:
                send_message(
                    update.effective_message,
                    "This command meant to be used in group not in PM",
                )
                return ""
            chat = update.effective_chat
            chat_name = update.effective_message.chat.title

        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, disable_cmd)
                if conn:
                    text = f"Disabled the use of `{disable_cmd}` command in *{chat_name}*!"
                else:
                    text = f"Disabled the use of `{disable_cmd}` command!"
                send_message(
                    update.effective_message,
                    text,
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                send_message(update.effective_message,
                             "This command can't be disabled")

        else:
            send_message(update.effective_message, "What should I disable?")

    @user_admin
    async def enable(update: Update, context: CallbackContext) -> None:
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user
        args = context.args

        conn = await connected(context.bot,
                               update,
                               chat,
                               user.id,
                               need_admin=True)
        if conn:
            chat = SHIROKO_PTB.bot.getChat(conn)
            chat_id = conn
            chat_name = SHIROKO_PTB.bot.getChat(conn).title
        else:
            if update.effective_message.chat.type == ChatType.PRIVATE:
                send_message(
                    update.effective_message,
                    "This command is meant to be used in group not in PM",
                )
                return ""
            chat = update.effective_chat
            chat_id = update.effective_chat.id
            chat_name = update.effective_message.chat.title

        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                if conn:
                    text = f"Enabled the use of `{enable_cmd}` command in *{chat_name}*!"
                else:
                    text = f"Enabled the use of `{enable_cmd}` command!"
                send_message(
                    update.effective_message,
                    text,
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                send_message(update.effective_message,
                             "Is that even disabled?")

        else:
            send_message(update.effective_message, "What should I enable?")

    @user_admin
    async def list_cmds(update: Update, context: CallbackContext) -> None:
        if DISABLE_CMDS + DISABLE_OTHER:
            result = "".join(f" - `{escape_markdown(str(cmd))}`\n"
                             for cmd in set(DISABLE_CMDS + DISABLE_OTHER))

            await update.effective_message.reply_text(
                f"The following commands are toggleable:\n{result}",
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await update.effective_message.reply_text(
                "No commands can be disabled.")

    # do not async
    def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return "No commands are disabled!"

        result = "".join(f" - `{escape_markdown(cmd)}`\n" for cmd in disabled)
        return f"The following commands are currently restricted:\n{result}"

    async def commands(update: Update, context: CallbackContext) -> None:
        chat = update.effective_chat
        user = update.effective_user
        conn = await connected(context.bot,
                               update,
                               chat,
                               user.id,
                               need_admin=True)
        if conn:
            chat = SHIROKO_PTB.bot.getChat(conn)
            chat_id = conn
        else:
            if update.effective_message.chat.type == ChatType.PRIVATE:
                send_message(
                    update.effective_message,
                    "This command is meant to use in group not in PM",
                )
                return ""
            chat = update.effective_chat
            chat_id = update.effective_chat.id

        text = build_curr_disabled(chat.id)
        send_message(update.effective_message,
                     text,
                     parse_mode=ParseMode.MARKDOWN)

    def __import_data__(chat_id, data):
        disabled = data.get("disabled", {})
        for disable_cmd in disabled:
            sql.disable_command(chat_id, disable_cmd)

    def __stats__():
        return f"➛ {sql.num_disabled()} disabled items, across {sql.num_chats()} chats."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    def __chat_settings__(chat_id, user_id):
        return build_curr_disabled(chat_id)

    __mod_name__ = "Disabling"

    __help__ = """
  ➛ /cmds*:* check the current status of disabled commands
    *Admins only:*
  ➛ /enable <cmd name>*:* enable that command
  ➛ /disable <cmd name>*:* disable that command
  ➛ /enablemodule <module name>*:* enable all commands in that module
  ➛ /disablemodule <module name>*:* disable all commands in that module
  ➛ /listcmds*:* list all possible toggleable commands
    """

    SHIROKO_PTB.add_handler(CommandHandler(
        "disable", disable, block=False))  # , filters=filters.ChatType.GROUPS)
    SHIROKO_PTB.add_handler(CommandHandler(
        "enable", enable, block=False))  # , filters=filters.ChatType.GROUPS)
    SHIROKO_PTB.add_handler(
        CommandHandler(["cmds", "disabled"], commands,
                       block=False))  # , filters=filters.ChatType.GROUPS)
    SHIROKO_PTB.add_handler(
        CommandHandler("listcmds", list_cmds,
                       block=False))  # , filters=filters.ChatType.GROUPS)

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleMessageHandler = MessageHandler
