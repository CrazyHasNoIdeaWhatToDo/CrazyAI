import json
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import openai
import time

# Import all command groups
from commands import gemini_commands, image_commands
from commands import utility_commands, fun_commands, siege_of_six, setup_screenshot
from commands.bank import get_player_diamonds, update_player_diamonds
from commands import blackjack_commands, slot_machine_commands, roulette_commands
from commands import goals, profile

# Load config
with open("data/config.json", "r") as f:
    config = json.load(f)
    
token = config["token"]
prefix = config["prefix"]
master_server = int(config["master_server"])
gemini_api_key = config["gemini_api_key"]
openai.api_key = config["openai_api_key"]

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-pro')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix=prefix, intents=intents)
client.remove_command("help") 

# --- All command registration happens here, before on_ready ---
gemini_commands.gemini_commands(model, client.tree)
image_commands.image_commands(openai, client.tree, master_server)
utility_commands.utility_commands(client.tree, config, master_server)
setup_screenshot.setup_screenshot(client.tree)
fun_commands.fun_commands(client.tree)
siege_of_six.siege_of_six_commands(config, client.tree)
slot_machine_commands.setup_slot_machine_commands(client.tree)
blackjack_commands.setup_blackjack_commands(client.tree)
roulette_commands.setup_roulette_commands(client.tree) 
goals.setup_goal_commands(client.tree, master_server)
profile.setup_profile_commands(client.tree, master_server)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    activity = discord.Game(name="Cooking up greatness")
    await client.change_presence(status=discord.Status.online, activity=activity)
    
    GUILD_ID = master_server
    
    try:
        guild = discord.Object(id=GUILD_ID)
        # Use only one sync call for a specific guild
        #synced = await client.tree.sync(guild=guild)
        await client.tree.sync()
        #print(f"Synced {len(synced)} slash commands to guild {GUILD_ID}.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
        
user_cooldowns = {}

COOLDOWN_SECONDS = 5 * 60  # 5 minutes
DIAMONDS_REWARD = 100

@client.event
async def on_message(message):
    # Ignore bots
    if message.author.bot:
        return

    user_id = str(message.author.id)
    server_id = str(message.guild.id) if message.guild else "dm"  # handle DMs if you want

    now = time.time()
    last_time = user_cooldowns.get(user_id, 0)

    if now - last_time >= COOLDOWN_SECONDS:
        # Give diamonds silently
        update_player_diamonds(server_id, user_id, DIAMONDS_REWARD)
        user_cooldowns[user_id] = now

    await client.process_commands(message)
        
        
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"**Try again after {round(error.retry_after, 2)} seconds.**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"**Missing argument: {error.param.name}. Please provide the necessary information.**")
    else:
        print(f"Unhandled error: {error}")

client.run(token)