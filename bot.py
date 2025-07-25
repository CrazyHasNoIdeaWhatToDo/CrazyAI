from commands import gemini_commands, guess_commands, image_commands, utility_commands, fun_commands, siege_of_six
import google.generativeai as genai
from discord.ext import commands
import discord
import openai
import json

with open("config.json", "r") as f:
    config = json.load(f)
    
token = config["token"]
prefix = config["prefix"]
gemini_api_key = config["gemini_api_key"]
openai.api_key = config["openai_api_key"]

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-pro')

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix=prefix, intents=intents)
client.remove_command("help") 

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    activity = discord.Game(name="I'm working on it - Crazy_Desire on the 12th of July 2025")
    await client.change_presence(status=discord.Status.online, activity=activity)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"**Try again after {round(error.retry_after, 2)} seconds.**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"**Missing argument: {error.param.name}. Please provide the necessary information.**")
    else:
        print(f"Unhandled error: {error}") 

gemini_commands.gemini_commands(model, client)    
image_commands.image_commands(openai, client)
utility_commands.utility_commands(client) 
guess_commands.game_commands(client)
fun_commands.fun_commands(client)
siege_of_six.siege_of_six_commands(config, client)

client.run(token)