import asyncio
import re
import socket
import sys
import threading
import argparse
import dotenv
from os import environ
from datetime import datetime
from pyrogram import Client, filters, idle

parser = argparse.ArgumentParser(description="HLBridge is a bot that forwards player messages from Telegram to the Half-Life server and vice versa.")
parser.add_argument("--oldengine", action='store_true', help="enable read old engine log")
args = parser.parse_args()

dotenv.load_dotenv("config.env", override=True)
REQUIRED_ENV_VARS = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'CHAT_ID', 'OWNER', 'LOG_PORT', 'SERVER_IP', 'SERVER_PORT', 'RCON_PASSWD', 'CONNECTIONLESS_ARGS']

for var in REQUIRED_ENV_VARS:
    if var not in environ:
        print("\033{var} variable is missing! Exiting now\033[0m\n")
        sys.exit()

api_id = int(environ["API_ID"])
api_hash = environ["API_HASH"]
bot_token = environ["BOT_TOKEN"]
chat_id = int(environ["CHAT_ID"])
owner = int(environ["OWNER"])
log_port = int(environ["LOG_PORT"])
ip = environ["SERVER_IP"]
port = int(environ["SERVER_PORT"])
rcon_passwd = environ["RCON_PASSWD"]
connectionless_args = environ["CONNECTIONLESS_ARGS"]

class HLServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.settimeout(5)

    @staticmethod
    def format_time(seconds):
        minutes = int(float(seconds)) // 60
        remaining_seconds = int(float(seconds)) % 60
        return f"{minutes}:{remaining_seconds:02}"

    def get_player_list(self):
        message = b'\xff\xff\xff\xff' + b'netinfo 48 0 3'
        self.sock.sendto(message, (self.ip, self.port))
        data = self.sock.recv(4048)
        data = data[16:]
        data = data.decode(errors='replace')
        data = "\\" + data.replace("'", ' ').replace('"', ' ').replace("'", ' ')
        data = data.split("\\")[2:]
        k = 4
        del data[k-1::k]
        player_list = []
        increment = len(data)
        while increment > 0:
            player_info = f"{self.format_time(data[increment - 1])} {data[increment - 2]} {data[increment - 3]}"
            player_list.append(player_info)
            increment -= 3

        return player_list

    def get_server_info(self):
        message = b'\xff\xff\xff\xff' + b'netinfo 48 0 4'
        self.sock.sendto(message, (self.ip, self.port))
        data = self.sock.recv(4048)
        data = data.decode(errors='replace')
        data = "\\" + data.replace("'", ' ').replace('"', ' ').replace("'", ' ')
        data = data.split("\\")[2:]

        server_info = []
        server_info.append(f"Server: {data[1]}\nMap: {data[9]}({data[5]}/{data[7]})")
        return server_info

class HLRcon:
    def __init__(self, ip, port, rcon_passwd:str, rcon_cmd:str):
        self.ip = ip
        self.port = port
        self.rcon_passwd = rcon_passwd
        self.rcon_cmd = rcon_cmd
        self.rcon_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rcon_sock.settimeout(5)

    def hlserver_rcon(self):
        message = b"\xFF\xFF\xFF\xFFrcon %b %b" % (self.rcon_passwd.encode(), self.rcon_cmd.encode())
        self.rcon_sock.sendto(message, (self.ip, self.port))
        data = self.rcon_sock.recv(65565)
        data = data.replace(bytes([0xff, 0xff, 0xff, 0xff, 0x70, 0x72, 0x69, 0x6e, 0x74]), b'').replace(bytes([0xff]), b'').replace(b'`', b'').replace(b'\n', b'\n').replace(b'\r', b'\n').replace(b'\r\r', b'\n')

        seen_lines = set()
        rcon = []

        while True:
            newdat = self.rcon_sock.recv(2048)

            if bytes([0xff, 0xff, 0xff, 0xff, 0x70, 0x72, 0x69, 0x6e, 0x74, 0x0a]) == newdat:
                break

            data += newdat

            lines = data.split(b'\n')
            for line in lines:
                if line not in seen_lines and line != b'\xff\xff\xff\xffprint':
                    seen_lines.add(line)
                    rcon.append(line.decode(errors='ignore'))
        return rcon

class Utils:
    @staticmethod
    def get_current_time():
        return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    @staticmethod
    def remove_color_tags(text):
        return re.sub(r'\^\d', '', text)

    @staticmethod
    def user_msg(message):
        return ' '.join(message.text.split(' ')[1:])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', log_port))

app = Client("HLBridge", api_id = api_id, api_hash = api_hash, bot_token = bot_token)

if args.oldengine:
    log_prefix = "log L"
else:
    log_prefix = "log"

saymatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" say "(.*)"')
entermatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" entered the game')
disconnectmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" disconnected')
suicidematch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" committed suicide with "(.*)"')
waskilledmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" committed suicide with "(.*)" \(.*\)')
killedmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" killed "(.*)<\d+><(.*)><\d+>" with "(.*)"')
kickmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: Kick: "(.*)<\d+><(.*)><>" was kicked by "(.*)" \(message "(.*)"\)')
changematch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" changed name to "(.*)"')

def send_to_telegram():
    print(f"\033[32m[{Utils.get_current_time()}] Half-Life: <<< Socket started! >>>\033[0m")
    while True:
        try:
            l, _ = sock.recvfrom(1024)
            l = l[4:].decode(errors='replace').replace('\n', '')
            l = Utils.remove_color_tags(l)

            matches = [
                (saymatch, lambda g: f'{g[0]}: {g[2]}'),
                (suicidematch, lambda g: f'"{g[0]}" committed suicide with {g[2]}'),
                (waskilledmatch, lambda g: f'"{g[0]}" committed suicide with {g[2]}'),
                (killedmatch, lambda g: f'"{g[0]}" killed {g[2]} with {g[4]}'),
                (kickmatch, lambda g: f'Player {g[0]} was kicked with message: "{g[3]}"'),
                (changematch, lambda g: f'Player "{g[0]}" changed name to: "{g[2]}"'),
                (entermatch, lambda g: f'Player "{g[0]}" has joined the game'),
                (disconnectmatch, lambda g: f'Player "{g[0]}" has left the game')
            ]

            for pattern, formatter in matches:
                m = pattern.match(l)
                if m:
                    g = m.groups()
                    text = formatter(g)
                    app.send_message(chat_id, text)
                    print(f"\033[37m[{Utils.get_current_time()}] Half-Life: <<< {text} >>>\033[0m")
                    break
        except Exception as e:
            print(f"\033[31m[{Utils.get_current_time()}] ERROR: <<< {e} >>>\033[0m")
            app.send_message(chat_id, e)
            sock.close()
            break

@app.on_message(filters.chat(chat_id) & ~filters.command(["status","rcon","id"]))
async def send_to_hl(client, message):
    msg = f"(telegram) {message.from_user.username}: {message.text}"
    query = b'\xff\xff\xff\xff%b %b\n' % (connectionless_args.encode(), msg.encode("utf8"))
    sock.sendto(query, (ip, port));
    print(f"\033[37m[{Utils.get_current_time()}] Telegram: <<< {message.from_user.username}: {message.text} >>>")

@app.on_message(filters.command("rcon") & filters.user(owner))
async def rcon(client, message):
    if len(message.command) == 1:
        await message.reply_text("/rcon [command]")
    try:
        rcon = HLRcon(ip, port, rcon_passwd, Utils.user_msg(message))
        cmd = '\n'.join(rcon.hlserver_rcon())
        msg = f"```{cmd}```"
        await message.reply_text(Utils.remove_color_tags(msg))
    except Exception as e:
        await message.reply_text(e)

@app.on_message(filters.command("status"))
async def status(client, message):
    try:
        status = HLServer(ip, port)
        server_info = '\n'.join(status.get_server_info())
        player_list = '\n'.join(status.get_player_list())
        msg = f"```{server_info}\nTime Frags Name\n\n{player_list}```"
        await message.reply_text(Utils.remove_color_tags(msg))
    except Exception as e:
        await message.reply_text(e)

@app.on_message(filters.command("id"))
async def get_id(client, message):
    try:
        msg = f"```Name ID\n{message.from_user.username}: {message.from_user.id}\n{message.chat.title}: {message.chat.id}```"
        await message.reply_text(msg)
    except Exception as e:
        await message.reply_text(e)

def cmd_input():
    print(f"\033[32m[{Utils.get_current_time()}] CmdInput: <<< Started! >>>\033[0m")
    while True:
        try:
            CmdInput = input()

            if CmdInput:
                msg = f"{app.me.first_name}: {CmdInput}"
                query = b'\xff\xff\xff\xff%b %b\n' % (connectionless_args.encode(), msg.encode("utf8"))
                sock.sendto(query, (ip, port));
                app.send_message(chat_id, CmdInput)
                print(msg)
        except Exception as e:
            print(f"\033[31m[{Utils.get_current_time()}] ERROR: <<< {e} >>>\033[0m")
            sock.close()
            break

def run_async_task(task):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(task())
    except Exception as e:
        print(f"\033[31m[{Utils.get_current_time()}] ERROR: <<< {e} >>>\033[0m")
    finally:
        loop.close()

async def start_bot():
    await app.start()
    print(f"\033[32m[{Utils.get_current_time()}] Telegram: <<< Bot started! >>>\033[0m")
    await idle()
    print(f"\033[31m[{Utils.get_current_time()}] Telegram: <<< Bot stopped! >>>\033[0m")


if __name__ == "__main__":
    threading.Thread(target=run_async_task, args=(send_to_telegram,), daemon=True).start()
    threading.Thread(target=run_async_task, args=(cmd_input,), daemon=True).start()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        print(f"\033[31m[{Utils.get_current_time()}] ERROR: <<< {e} >>>\033[0m")
    finally:
        app.stop()
        sock.close()
        print("\nPress enter to finish!")
