import re
import asyncio
from .socket import Socket
from .utils import Utils

class HLServer:
    def __init__(self, ip, port, protocol, timeout):
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.timeout = timeout
        self.socket = Socket()

    async def get_players(self):
        message = b'\xff\xff\xff\xff' + b'netinfo %b 0 3' % str(self.protocol).encode()

        data = await self.socket.send_packet(self.ip, self.port, message, self.timeout)

        if not data:
            return {}

        data = data[16:]
        data = data.decode(errors='replace')
        data = "\\" + data.replace("'", ' ').replace('\n', '')
        data = data.split("\\")[1:]

        if data[-1] == '':
            data = data[:-1]

        players_list = {}

        # Check protocol version
        if self.protocol == 49:
            if 'players' in data:
                num_players = int(data[data.index('players') + 1])

                for i in range(num_players):
                    name = data[data.index(f"p{i}name") + 1]
                    frags = data[data.index(f"p{i}frags") + 1]
                    time = data[data.index(f"p{i}time") + 1]

                    players_list[i] = [
                        name,
                        frags,
                        time
                        ]
        else:
            for i in range(0, len(data), 4):
                if i + 3 < len(data):
                    index = data[i]
                    name = data[i + 1]
                    frags = data[i + 2]
                    time = data[i + 3]

                    players_list[index] = [
                        name,
                        frags,
                        time
                        ]

        players = []

        for index, player_info in players_list.items():
            players.append(f"{index} {Utils.remove_color_tags(player_info[0])} [{player_info[1]}] ({Utils.format_time(player_info[2])})\n")

        return players

    async def get_server_info(self):
        message = b'\xff\xff\xff\xff' + b'netinfo %b 0 4' % str(self.protocol).encode()

        data = await self.socket.send_packet(self.ip, self.port, message, self.timeout)
        data = data.decode(errors='replace')
        data = "\\" + data.replace("'", ' ').replace('"', ' ').replace("'", ' ')
        data = data.split("\\")[2:]

        server_info = []
        server_info.append(f"Server: {data[1]}\nMap: {data[9]}({data[5]}/{data[7]})")

        return server_info
