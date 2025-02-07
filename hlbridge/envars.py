import sys
import dotenv
import os
from os import environ

dotenv.load_dotenv("config.env", override=True)
REQUIRED_ENV_VARS = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'CHAT_ID', 'OWNER', 'LOG_PORT', 'SERVER_IP', 'SERVER_PORT', 'RCON_PASSWD', 'CONNECTIONLESS_ARGS']

for var in REQUIRED_ENV_VARS:
    if var not in environ:
        print("{var} variable is missing! Exiting now!\n")
        sys.exit(1)

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])
OWNER = int(os.environ["OWNER"])
LOG_PORT = int(os.environ["LOG_PORT"])
SERVER_IP = os.environ["SERVER_IP"]
SERVER_PORT = int(os.environ["SERVER_PORT"])
RCON_PASSWD = os.environ["RCON_PASSWD"]
CONNECTIONLESS_ARGS = os.environ["CONNECTIONLESS_ARGS"]
