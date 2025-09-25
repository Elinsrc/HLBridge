# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

import yaml

def get_config() -> dict:
    with open("config.yml", "r") as f:
        return yaml.safe_load(f)

config = get_config()

API_ID = int(config["api_id"])
API_HASH = config["api_hash"]
BOT_TOKEN = config["bot_token"]
WORKERS = int(config["workers"])
