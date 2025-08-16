import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os

# --- Constants ---
BANK_FILE = 'data/bank.json'
STARTING_DIAMONDS = 50

# --- Bank Management Functions ---
def load_bank_data():
    """Loads diamond data from bank.json, migrating old flat format if needed."""
    try:
        with open(BANK_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        with open(BANK_FILE, 'w') as f:
            json.dump({}, f)
        return {}
    except json.JSONDecodeError:
        print(f"Warning: {BANK_FILE} is empty or corrupted. Starting with an empty bank.")
        return {}

    # --- Migration: flat {user_id: amount} -> {server_id: {user_id: amount}} ---
    if data and all(isinstance(v, (int, float)) for v in data.values()):
        print("Migrating old bank.json format to server-based format...")
        migrated = {}
        migrated["global"] = {uid: amt for uid, amt in data.items()}
        save_bank_data(migrated)
        return migrated

    return data

def save_bank_data(data):
    """Saves diamond data to bank.json."""
    with open(BANK_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_player_diamonds(server_id: str, player_id: str):
    """Gets or initializes a player's diamonds for a specific server."""
    bank_data = load_bank_data()

    if server_id not in bank_data:
        bank_data[server_id] = {}

    if player_id not in bank_data[server_id] or bank_data[server_id][player_id] <= 0:
        bank_data[server_id][player_id] = STARTING_DIAMONDS
        save_bank_data(bank_data)

    return bank_data[server_id][player_id]

def update_player_diamonds(server_id: str, player_id: str, amount: int):
    """Updates a player's diamond balance in a specific server."""
    bank_data = load_bank_data()

    if server_id not in bank_data:
        bank_data[server_id] = {}

    bank_data[server_id][player_id] = bank_data[server_id].get(player_id, STARTING_DIAMONDS) + amount
    save_bank_data(bank_data)