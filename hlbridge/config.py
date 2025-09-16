import json

def get_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def parse_servers(servers):
    servers_config = []
    for server in servers:
        if server.get('is_active') == 1:
            servers_config.append({
                'oldengine': int(server['oldengine']),
                'server_name': server['server_name'],
                'chat_id': int(server['chat_id']),
                'ip': server['ip'],
                'port': int(server['port']),
                'log_port': int(server['log_port']),
                'connectionless_args': server['connectionless_args'],
                'log_suicides': int(server['log_suicides']),
                'log_kills': int(server['log_kills']),
            })
    return servers_config

config = get_config()

API_ID = int(config['api_id'])
API_HASH = config['api_hash']
BOT_TOKEN = config['bot_token']
OWNER = int(config['owner'])
WORKERS = int(config['workers'])
SERVERS = parse_servers(config['servers'])
