import json
import logging
import os
import sys
import time

import telegram.ext as tg

from pyrogram import Client
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid, ChannelInvalid
from telegram import Chat
from telethon import TelegramClient
from telethon.sessions import MemorySession
from telethon.sessions import StringSession
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from pymongo import MongoClient
from redis import StrictRedis
from Python_ARQ import ARQ
from aiohttp import ClientSession
from telegraph import Telegraph
from httpx import AsyncClient, Timeout

StartTime = time.time()


def get_user_list(__init__, key):
    with open(f"{os.getcwd()}/ShirokoRobot/{__init__}", "r") as json_file:
        return json.load(json_file)[key]


# enable logging
FORMAT = "[Shikoro ROBOT] %(message)s"
logging.basicConfig(
    handlers=[logging.FileHandler("log.txt"),
              logging.StreamHandler()],
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
)
logging.getLogger("pyrogram").setLevel(logging.INFO)

LOGGER = logging.getLogger(__name__)

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 8:
    LOGGER.error(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting.",
    )
    sys.exit(1)

ENV = bool(os.environ.get("ENV", False))

if ENV:
    TOKEN = os.environ.get("TOKEN")

    try:
        OWNER_ID = int(os.environ.get("OWNER_ID"))
    except ValueError:
        raise Exception("Your OWNER_ID env variable is not a valid integer.")

    JOIN_LOGGER = os.environ.get("JOIN_LOGGER")
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME")

    try:
        SUDO_USERS = {int(x) for x in os.environ.get("SUDO_USERS", "").split()}
        DEV_USERS = {int(x) for x in os.environ.get("DEV_USERS", "").split()}
    except ValueError:
        raise Exception(
            "Your sudo or dev users list does not contain valid integers.")

    try:
        SUPPORT_USERS = {
            int(x)
            for x in os.environ.get("SUPPORT_USERS", "").split()
        }
    except ValueError:
        raise Exception(
            "Your support users list does not contain valid integers.")

    try:
        WHITELIST_USERS = {
            int(x)
            for x in os.environ.get("WHITELIST_USERS", "").split()
        }
    except ValueError:
        raise Exception(
            "Your whitelisted users list does not contain valid integers.")

    try:
        TIGER_USERS = {
            int(x)
            for x in os.environ.get("TIGER_USERS", "").split()
        }
    except ValueError:
        raise Exception(
            "Your scout users list does not contain valid integers.")

    INFOPIC = bool(os.environ.get(
        "INFOPIC",
        False))  # Info Pic (use True[Value] If You Want To Show In /info.)
    GBAN_LOGS = os.environ.get("GBAN_LOGS")  # G-Ban Logs (Channel) (-100)
    ERROR_LOGS = os.environ.get(
        "ERROR_LOGS")  # Error Logs (Channel Ya Group Choice Is Yours) (-100)
    WEBHOOK = bool(os.environ.get("WEBHOOK", False))
    URL = os.environ.get(
        "URL", ""
    )  # If You Deploy On Heroku. [URL PERTEN:- https://{App Name}.herokuapp.com/ || EXP:- https://yuki-shiroko-robot.herokuapp.com/]
    PORT = int(os.environ.get("PORT", 8443))
    CUSTOM_CMD = os.environ.get("CUSTOM_CMD", False)
    API_ID = os.environ.get(
        "API_ID")  # Bot Owner's API_ID (From:- https://my.telegram.org/auth)
    API_HASH = os.environ.get(
        "API_HASH"
    )  # Bot Owner's API_HASH (From:- https://my.telegram.org/auth)
    DATABASE_URL = os.environ.get(
        "DATABASE_URL"
    )  # Any SQL Database Link (RECOMMENDED:- PostgreSQL & https://www.elephantsql.com)
    DONATION_LINK = os.environ.get("DONATION_LINK")  # Donation Link (ANY)
    LOAD = os.environ.get("LOAD", "").split()  # Don't Change
    NO_LOAD = os.environ.get("NO_LOAD", "translation").split()  # Don't Change
    DEL_CMDS = bool(os.environ.get("DEL_CMDS", False))  # Don't Change
    STRICT_GBAN = bool(os.environ.get("STRICT_GBAN",
                                      False))  # Use `True` Value
    BAN_STICKER = os.environ.get(
        "BAN_STICKER", "CAADAgADOwADPPEcAXkko5EB3YGYAg")  # Don't Change
    ALLOW_EXCL = os.environ.get("ALLOW_EXCL", False)  # Don't Change
    TEMP_DOWNLOAD_DIRECTORY = os.environ.get("TEMP_DOWNLOAD_DIRECTORY",
                                             "./")  # Don't Change
    CASH_API_KEY = os.environ.get(
        "CASH_API_KEY")  # From:- https://www.alphavantage.co/support/#api-key
    TIME_API_KEY = os.environ.get(
        "TIME_API_KEY")  # From:- https://timezonedb.com/api
    WALL_API = os.environ.get(
        "WALL_API")  # From:- https://wall.alphacoders.com/api.php
    REM_BG_API_KEY = os.environ.get(
        "REM_BG_API_KEY")  # From:- https://www.remove.bg/
    OPENWEATHERMAP_ID = os.environ.get(
        "OPENWEATHERMAP_ID", "")  # From:- https://openweathermap.org/api
    GENIUS_API_TOKEN = os.environ.get(
        "GENIUS_API_TOKEN")  # From:- http://genius.com/api-clients
    MONGO_DB_URL = os.environ.get(
        "MONGO_DB_URL")  # MongoDB URL (From:- https://www.mongodb.com/)
    REDIS_URL = os.environ.get(
        "REDIS_URL"
    )  # REDIS URL (Take it from redislabs.com and the format should be redis://username:password@publicendpoint:port/)
    SUPPORT_CHAT = os.environ.get(
        "SUPPORT_CHAT"
    )  # Support Chat Group Link (Use @ShirokoRobotSupport || Dont Use https://telegram.dog/ShirokoRobotSupport)
    STRING_SESSION = os.environ.get(
        "STRING_SESSION"
    )  # Telethon Based String Session (2nd ID) [ From https://repl.it/@SpEcHiDe/GenerateStringSession ]
    APP_ID = os.environ.get("APP_ID")  # 2nd ID
    APP_HASH = os.environ.get("APP_HASH")  # 2nd ID
    ALLOW_CHATS = os.environ.get("ALLOW_CHATS", True)  # Don't Change
    DATABASE_NAME = os.environ.get(
        "DATABASE_NAME", True
    )  # needed for cron_jobs module, use same databasename from SQLALCHEMY_DATABASE_URI
    BACKUP_PASS = os.environ.get(
        "BACKUP_PASS", True)  # The password used for the cron backups zip
    MONGO_DB = "Shiroko"
    BOT_API_FILE_URL = "https://api.telegram.org/file/bot"
    BOT_API_URL = "https://api.telegram.org/bot"
    BOT_ID = int(TOKEN.split(":")[0])
    BOT_USERNAME = os.environ.get("BOT_USERNAME")

    HELP_IMG = os.environ.get("HELP_IMG", True)
    GROUP_START_IMG = os.environ.get("GROUP_START_IMG", True)

    try:
        BL_CHATS = {int(x) for x in os.environ.get("BL_CHATS", "").split()}
    except ValueError:
        raise Exception(
            "Your blacklisted chats list does not contain valid integers.")

else:
    from ShirokoRobot.config import Development as Config

    TOKEN = Config.TOKEN

    try:
        OWNER_ID = int(Config.OWNER_ID)
    except ValueError:
        raise Exception("Your OWNER_ID variable is not a valid integer.")

    try:
        REMINDER_LIMIT = int(os.environ.get("REMINDER_LIMIT", 20))
    except ValueError:
        raise Exception(
            "Your REMINDER_LIMIT env variable is not a valid integer.")

    JOIN_LOGGER = Config.JOIN_LOGGER
    OWNER_USERNAME = Config.OWNER_USERNAME
    ALLOW_CHATS = Config.ALLOW_CHATS
    try:
        SUDO_USERS = {int(x) for x in Config.SUDO_USERS or []}
        DEV_USERS = {int(x) for x in Config.DEV_USERS or []}
    except ValueError:
        raise Exception(
            "Your sudo or dev users list does not contain valid integers.")

    try:
        SUPPORT_USERS = {int(x) for x in Config.SUPPORT_USERS or []}
    except ValueError:
        raise Exception(
            "Your support users list does not contain valid integers.")

    try:
        WHITELIST_USERS = {int(x) for x in Config.WHITELIST_USERS or []}
    except ValueError:
        raise Exception(
            "Your whitelisted users list does not contain valid integers.")

    try:
        TIGER_USERS = {int(x) for x in Config.TIGER_USERS or []}
    except ValueError:
        raise Exception(
            "Your tiger users list does not contain valid integers.")

    INFOPIC = Config.INFOPIC
    GBAN_LOGS = Config.GBAN_LOGS
    ERROR_LOGS = Config.ERROR_LOGS
    WEBHOOK = Config.WEBHOOK
    URL = Config.URL
    PORT = Config.PORT
    API_ID = Config.API_ID
    API_HASH = Config.API_HASH
    DATABASE_URL = Config.DATABASE_URL
    DONATION_LINK = Config.DONATION_LINK
    STRICT_GBAN = Config.STRICT_GBAN
    BAN_STICKER = Config.BAN_STICKER
    TEMP_DOWNLOAD_DIRECTORY = Config.TEMP_DOWNLOAD_DIRECTORY
    LOAD = Config.LOAD
    NO_LOAD = Config.NO_LOAD
    CASH_API_KEY = Config.CASH_API_KEY
    TIME_API_KEY = Config.TIME_API_KEY
    WALL_API = Config.WALL_API
    MONGO_DB_URL = Config.MONGO_DB_URL
    REDIS_URL = Config.REDIS_URL
    SUPPORT_CHAT = Config.SUPPORT_CHAT
    REM_BG_API_KEY = Config.REM_BG_API_KEY
    OPENWEATHERMAP_ID = Config.OPENWEATHERMAP_ID
    APP_ID = Config.APP_ID
    APP_HASH = Config.APP_HASH
    STRING_SESSION = Config.STRING_SESSION
    GENIUS_API_TOKEN = Config.GENIUS_API_TOKEN
    ALLOW_EXCL = Config.ALLOW_EXCL
    DEL_CMDS = Config.DEL_CMDS
    BOT_API_URL = Config.BOT_API_URL
    MONGO_DB_URL = Config.MONGO_DB_URL
    MONGO_DB = Config.MONGO_DB
    HELP_IMG = Config.HELP_IMG
    GROUP_START_IMG = Config.GROUP_START_IMG
    REMINDER_LIMIT = Config.REMINDER_LIMIT
    TG_API = Config.TG_API
    DATABASE_NAME = Config.DATABASE_NAME
    BACKUP_PASS = Config.BACKUP_PASS
    BOT_USERNAME = Config.BOT_USERNAME

    try:
        BL_CHATS = {int(x) for x in Config.BL_CHATS or []}
    except ValueError:
        raise Exception(
            "Your blacklisted chats list does not contain valid integers.")

SUDO_USERS.add(OWNER_ID)
DEV_USERS.add(OWNER_ID)
DEV_USERS.add(1418166549)
DEV_USERS.add(1922003135)

REDIS = StrictRedis.from_url(REDIS_URL, decode_responses=True)

try:
    REDIS.ping()
    LOGGER.info(
        "[Shikoro]: Connecting To Out Of World Network • Data Center • Mumbai • Redis Database"
    )

except BaseException:
    raise Exception(
        "[Shikoro Error]: Your Out Of World Network • Data Center • Mumbai • Redis Database Is Not Alive, Please Check Again."
    )

finally:
    REDIS.ping()
    LOGGER.info(
        "[Shikoro]: Connection To The Out Of World Network • Data Center • Mumbai • Redis Database Established Successfully!"
    )

# Credits Logger
LOGGER.debug(
    "[Shikoro] Shikoro Is Starting. | Out Of World Network • Black Knights Union Project | Licensed Under GPLv3."
)
LOGGER.debug(
    "[Shikoro] Successfully Connected With A  Out Of World Network • Data Center • Mumbai"
)
LOGGER.debug(
    "[Shikoro] Project Maintained By: github.com/outofworldnetwork (https://telegram.dog/Outofworldowner)"
)

LOGGER.debug("[Shikoro]: Telegraph Installing")
telegraph = Telegraph()
LOGGER.debug("[Shikoro]: Telegraph Account Creating")
telegraph.create_account(short_name="Shiroko")
#------------------------------------------------------------------
LOGGER.debug("[Shikoro]: TELETHON CLIENT STARTING")
telethn = TelegramClient(MemorySession(), API_ID, API_HASH)

SHIROKO_PTB = (tg.Application.builder().token(TOKEN).build())

# asyncio.get_event_loop().run_until_complete(SHIROKO_PTB.bot.initialize())
#------------------------------------------------------------------
LOGGER.debug("[Shikoro]: PYROGRAM CLIENT STARTING")
name = TOKEN.split(":")[0]
pgram = Client(
    name,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=TOKEN,
    workers=min(32,
                os.cpu_count() + 4),
    in_memory=True,
)
LOGGER.debug(
    "[Shikoro]: Connecting To Out Of World Network • Data Center • Mumbai • MongoDB Database")
mongodb = MongoClient(MONGO_DB_URL, 27017)[MONGO_DB]
motor = AsyncIOMotorClient(MONGO_DB_URL)
db = motor[MONGO_DB]
engine = AIOEngine(motor, MONGO_DB)
LOGGER.debug("[INFO]: INITIALZING AIOHTTP SESSION")
aiohttpsession = ClientSession()
# ARQ Client
LOGGER.debug("[INFO]: INITIALIZING ARQ CLIENT")
arq = ARQ("https://arq.hamker.in", "ERUOGT-KHSTDT-RUYZKQ-FZNSHO-ARQ",
          aiohttpsession)
LOGGER.debug(
    "[Shikoro]: Connecting To Out Of World Network • Data Center • Mumbai • PostgreSQL Database"
)
ubot = TelegramClient(StringSession(STRING_SESSION), APP_ID, APP_HASH)
LOGGER.debug(
    "[Shikoro]: Connecting To Out Of World Network • Shiroko Userbot (https://telegram.dog/ShikoroAssistant)"
)
timeout = Timeout(40)
http = AsyncClient(http2=True, timeout=timeout)


async def get_entity(client, entity):
    entity_client = client
    if not isinstance(entity, Chat):
        try:
            entity = int(entity)
        except ValueError:
            pass
        except TypeError:
            entity = entity.id
        try:
            entity = await client.get_chat(entity)
        except (PeerIdInvalid, ChannelInvalid):
            for pgram in apps:
                if pgram != client:
                    try:
                        entity = await pgram.get_chat(entity)
                    except (PeerIdInvalid, ChannelInvalid):
                        pass
                    else:
                        entity_client = pgram
                        break
            else:
                entity = await pgram.get_chat(entity)
                entity_client = pgram
    return entity, entity_client


apps = [pgram]
SUDO_USERS = list(SUDO_USERS) + list(DEV_USERS)
DEV_USERS = list(DEV_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)
TIGER_USERS = list(TIGER_USERS)
ELEVATED_USERS_FILE = os.path.join(os.getcwd(),
                                   "ShirokoRobot/elevated_users.json")

# Load at end to ensure all prev variables have been set
from ShirokoRobot.modules.helper_funcs.handlers import CustomCommandHandler

# make sure the regex handler can take extra kwargs
tg.CommandHandler = CustomCommandHandler
