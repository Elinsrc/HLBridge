# Python Half-Life Bridge

* **HLBridge** is a bot that forwards player messages from **Telegram** to the **Half-life** or **CS16** servers and vice versa.

# Building server and setting it up

First you need to build metamod plugin, depending on your platform, from source [HLBridge_metamod](https://github.com/Elinsrc/HLBridge_metamod)

After building **hlbridge_mm_i386.so** or **hlbridge_mm_i386.dll**, move it to **gamedir**/dlls/addons/metamod

After that you need to edit **gamedir**/dlls/addons/metamod/plugins.ini and enable **hlbridge_mm_i386.so** or **hlbridge_mm_i386.dll**.

After that you need to edit **server.cfg** and add commands.

**Attention**, please specify different argument in **connectionless_args** and in **rcon_password**, do not write it the same as in the example.

Example:
```
logaddress 127.0.0.1 27000
rcon_password "password"
allow_connectionless 1
connectionless_args "chatsendmsg"
```

At this stage we have finished setting up the **Server**, you can start the server.

# configuration of Telegram bot

Create a bot via [@BotFather](https://t.me/botfather)

Create Telegram api id and hash, you can find out how to do this on the Internet.

Configure config.yml

Example:
```
api_id: 1234567890
api_hash: "qwertyuiopasdfghjklzxcvbnm",
bot_token: "1234567890:qwertyuiopasdfghjklzxcvbnm"
workers: 24

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

# Initial setup

After starting the bot, you need to invite it to a chat that has topics enabled.
Then enter the command `/setup` in any topic.
The bot will save the **chat_id** and **topic_id** to the database, and from now on, every time the bot starts, it will send a startup notification there.

* Important: the first time you use `/setup`, you will be set as the **owner** of the bot.

Next, you need to use `/add_server` and follow the instructions to add your game servers.
To get the full list of available commands, use `/help`.
