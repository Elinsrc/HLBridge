# Python Half-Life Bridge

* **HLBridge** is a bot that forwards player messages from **Telegram** to the **Half-life** server and vice versa.

# Building a Half-Life server and setting it up

First you need to build **hl.so** or **hl.dll**, depending on your platform, from source [hlsdk-portable branch hlbridge](https://github.com/Elinsrc/hlsdk-portable/tree/hlbridge/)

After building **hl.so** or **hl.dll**, move it to valve/dlls and replace the files.

After that you need to edit **server.cfg** and add commands.

**Attention**, specify a different argument in **connectionless_args** and **rcon_password**, do not write the same as in the example.

Example:
```
allow_connectionless 1
connectionless_args "chatsendmsg"
logaddress 127.0.0.1 27000
rcon_password YOUR_PASSWORD
```

At this stage we have finished setting up the **Half-Life Server**, you can start the server.

# Installation and configuration of Telegram bot

Install the required libraries in requirements.txt

Also create a bot via [@BotFather](https://t.me/botfather)

Create Telegram api id and hash, you can find out how to do this on the Internet.

Configure config.env

Example:
```
API_ID = your_api_id
API_HASH = your_api_hash
BOT_TOKEN = your_bot_token
OWNER = your_user_id
CHAT_ID = your_chat_ID_from_where_messages_will_be_sent

# Your game logaddress port
LOG_PORT = 27000

# Your game server ip
SERVER_IP =

# Your game server port
SERVER_PORT = 27015

RCON_PASSWD = your_game_rcon_password

# Your game connectionless_args
CONNECTIONLESS_ARGS = chatsendmsg
```

# Running a bot

Example:
```
python3 hlbridge.py
```

**Attention**, if you use **Xash3D FWGS 0.19.x** or **Goldsrc** you need to add the **--oldengine** parameter

Example:
```
python3 hlbridge.py --oldengine
```
