# Python Half-Life Bridge

* **HLBridge** is a bot that forwards player messages from **Telegram** to the **Half-life** server and vice versa.

# Building a Half-Life server and setting it up

First you need to build **hl.so** or **hl.dll**, depending on your platform, from source [hlsdk-portable branch hlbridge](https://github.com/Elinsrc/hlsdk-portable/tree/hlbridge/)

After building **hl.so** or **hl.dll**, move it to valve/dlls and replace the files.

After that you need to edit **server.cfg** and add commands.

**Attention**, specify a different argument in **connectionless_args**, do not write the same as in the example.

Example:
```
log on
logaddress 127.0.0.1 27000
allow_connectionless 1
connectionless_args "chatsendmsg"
```

At this stage we have finished setting up the **Half-Life Server**, you can start the server.

# configuration of Telegram bot

Create a bot via [@BotFather](https://t.me/botfather)

Create Telegram api id and hash, you can find out how to do this on the Internet.

Configure config.json

If "is_active": 0 then the server is ignored

**Attention**, if you use **Xash3D FWGS 0.19.x** or **GoldSrc** you need "oldengine": 1

example config.json:
```
{
    "servers": [
        {
            "is_active": 1,
            "oldengine": 0,
            "server_name": "server 1",
            "chat_id": -1234567890,
            "ip": "127.0.0.1",
            "port": 27015,
            "log_port": 27000,
            "connectionless_args": "chatsendmsg",
            "log_suicides": 0,
            "log_kills": 0
        },
        {
            "is_active": 0,
            "oldengine": 0,
            "server_name": "server 2",
            "chat_id": -1234567890,
            "ip": "127.0.0.1",
            "port": 27016,
            "log_port": 27001,
            "connectionless_args": "chatsendmsg",
            "log_suicides": 0,
            "log_kills": 0
        },
        {
            "is_active": 0,
            "oldengine": 0,
            "server_name": "Server 3",
            "chat_id": -1234567890,
            "ip": "127.0.0.1",
            "port": 27016,
            "log_port": 27002,
            "connectionless_args": "chatsendmsg",
            "log_suicides": 0,
            "log_kills": 0
        },
        {
            "is_active": 0,
            "oldengine": 0,
            "server_name": "Server 4",
            "chat_id": -1234567890,
            "ip": "127.0.0.1",
            "port": 27017,
            "log_port": 27003,
            "connectionless_args": "chatsendmsg",
            "log_suicides": 0,
            "log_kills": 0
        }
    ],
    "api_id": 1234567890,
    "api_hash": "qwertyuiopasdfghjklzxcvbnm",
    "bot_token": "1234567890:qwertyuiopasdfghjklzxcvbnm",
    "owner": 1234567890,
    "workers": 24
}

```


# Create venv and install requirements

```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

# Running a HLBridge

Example:
```
python3 -m hlbridge
```
