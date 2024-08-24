import asyncio
import re
import socket
import threading
from pyrogram import Client, filters, idle
from os import environ
import dotenv

dotenv.load_dotenv("config.env", override=True)

api_id = environ.get("API_ID")
api_hash = environ.get("API_HASH")
bot_token = environ.get("BOT_TOKEN")
chat_id = int(environ.get("CHAT_ID"))
owner = int(environ.get("OWNER"))
log_port = int(environ.get("LOG_PORT"))
ip = environ.get("SERVER_IP")
port = int(environ.get("SERVER_PORT"))
rcon_passwd = environ.get("RCON_PASSWD")
connectionless_args = environ.get("CONNECTIONLESS_ARGS")

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

    def hlserver_rcon_say(self):
        message = b"\xFF\xFF\xFF\xFFrcon %b say %b" % (self.rcon_passwd.encode(), self.rcon_cmd.encode())
        self.rcon_sock.sendto(message, (self.ip, self.port))


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', log_port))

app = Client("HL_Bridge", api_id, api_hash, bot_token)

saymatch = re.compile(r'log L \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" say "(.*)"')
entermatch = re.compile(r'log L \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" entered the game')
disconnectmatch = re.compile(r'log L \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" disconnected')
suicidematch = re.compile(r'log L \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" committed suicide with "(.*)"')
waskilledmatch = re.compile(r'log L \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" committed suicide with "(.*)" \(.*\)')
killedmatch = re.compile(r'log L \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" killed "(.*)<\d+><(.*)><\d+>" with "(.*)"')
kickmatch = re.compile(r'log L \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: Kick: "(.*)<\d+><(.*)><>" was kicked by "(.*)" \(message "(.*)"\)')
changematch = re.compile(r'log L \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<\d+><(.*)><\d+>" changed name to "(.*)"')
colorsub = re.compile(r'\^\d')

def send_to_telegram():
    while True:
        try:
            l, _ = sock.recvfrom(1024)
            l = l[4:].decode(errors='replace').replace('\n', '')
            l = colorsub.sub('', l)

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
                    break
        except Exception as e:
            app.send_message(chat_id, e)

def remove_color_tags(text):
    return re.sub(r'\^\d', '', text)

def user_msg(message):
    return ' '.join(message.text.split(' ')[1:])

@app.on_message(filters.chat(chat_id) & ~filters.command(["status","rcon"]))
async def send_to_hl(client, message):
    msg = f"(telegram) {message.from_user.username}: {message.text}"
    query = b'\xff\xff\xff\xff%b %b\n' % (connectionless_args.encode(), msg.encode("utf8"))
    sock.sendto(query, (ip, port));

@app.on_message(filters.command("rcon") & filters.user(owner))
async def rcon(client, message):

    if len(message.command) == 1:
        await message.reply_text("/rcon [command]")
    try:
        rcon = HLRcon(ip, port, rcon_passwd, user_msg(message))
        cmd = '\n'.join(rcon.hlserver_rcon())
        msg = f"```{cmd}```"
        await message.reply_text(remove_color_tags(msg))
    except Exception as e:
        await message.reply_text(e)

@app.on_message(filters.command("status"))
async def status(client, message):
    try:
        status = HLServer(ip, port)
        server_info = '\n'.join(status.get_server_info())
        player_list = '\n'.join(status.get_player_list())
        msg = f"```{server_info}\nTime Frags Name\n\n{player_list}```"
        await message.reply_text(remove_color_tags(msg))
    except Exception as e:
        await message.reply_text(e)

if __name__ == "__main__":
    threading.Thread(target=send_to_telegram).start()
    app.run()
    idle()