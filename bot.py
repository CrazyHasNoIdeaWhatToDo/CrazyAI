import discord
from discord.ext import commands
import requests
import json
import google.generativeai as genai

#Use pyinstaller --noconsole --onefile gui_launcher.py to compile code for exe launcher

with open("config.json", "r") as f:
    config = json.load(f)
    
token = config["token"]
prefix = config["prefix"]
gemini_api_key = config["gemini_api_key"]

# Configure the Gemini API
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-pro') # You can choose other models if needed

#gemini-2.5-flash-lite

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix=prefix, intents=intents)
client.remove_command("help")  # Remove default help


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    activity = discord.Game(name="I'm working on it - Crazy_Desire on the 12th of July 2025")
    await client.change_presence(status=discord.Status.online, activity=activity)


# CUSTOM HELP COMMAND: .crazyhelp
@client.group(name="crazyhelp", invoke_without_command=True)
async def crazyhelp(ctx):
    embed = discord.Embed(title="Help Center ✨", color=0xF49726)
    embed.add_field(
        name="Command Categories:",
        value=(
            "😃 `hello :` says hello back\n"
            "🤖 `askcrazy :` Talk to CrazyAI\n"
            "👨🏿 `askallan :` Talk to AllanAI\n"
            "🙉 `askseb :` Talk to SebAI\n"
            "To view the commands of a category, send `.crazyhelp <category>`"
        ),
        inline=False
    )
    embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Help requested by: {ctx.author.display_name}")
    await ctx.send(embed=embed)


@crazyhelp.command()
async def memes(ctx):
    embed = discord.Embed(title="Help Center ✨", description="Commands of **memes**\n`.meme:` Memes", color=0xF49726)
    embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Command requested by: {ctx.author.display_name}")
    await ctx.send(embed=embed)

@crazyhelp.command()
async def utility(ctx):
    embed = discord.Embed(title="Help Center ✨", description="Commands of **utility**\n`.ping:` Latency", color=0xF49726)
    embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Command requested by: {ctx.author.display_name}")
    await ctx.send(embed=embed)

@crazyhelp.command()
async def ai(ctx): # New AI help command
    embed = discord.Embed(title="Help Center ✨", description="Commands of **AI**\n`.ask <query>:` Ask Google Gemini a question", color=0xF49726)
    embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Command requested by: {ctx.author.display_name}")
    await ctx.send(embed=embed)

# Display all commands at once
@client.command(help="Displays all available commands")
async def allcommands(ctx):
    embed = discord.Embed(title="All Commands 🧾", color=0xF49726)
    cmds = [f"`{prefix}{command.name}` - {command.help or 'No description'}" for command in client.commands if not command.hidden]
    embed.description = "\n".join(cmds)
    embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Requested by: {ctx.author.display_name}")
    await ctx.send(embed=embed)


# Handle command cooldown error
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"**Try again after {round(error.retry_after, 2)} seconds.**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"**Missing argument: {error.param.name}. Please provide the necessary information.**")
    else:
        print(f"Unhandled error: {error}") # For debugging other errors


# Meme command
@client.command(help="Sends a random meme")
@commands.cooldown(1, 10, commands.BucketType.channel)
async def meme(ctx):
    response = requests.get("https://meme-api.herokuapp.com/gimme/memes")
    m = response.json()

    embed = discord.Embed(title=m["title"], url=m["postLink"], color=0xF49726)
    embed.set_image(url=m["url"])
    embed.set_footer(text=f"👍 {m['ups']} | r/{m['subreddit']}")
    await ctx.send(embed=embed)


# Ping command
@client.command(help="Shows the bot's latency")
@commands.cooldown(1, 10, commands.BucketType.channel)
async def ping(ctx):
    await ctx.send(f'Ping! **{round(client.latency * 1000)}ms**')


# Hello command
@client.command(help="Greets the user")
async def hello(ctx):
    await ctx.send("Hello back! 👋")

##################################################################################################################  
@client.command(help="Ask Google Gemini a question and get an AI-generated response with a specific personality.")
@commands.cooldown(1, 15, commands.BucketType.user)
async def askcrazy(ctx, *, question: str):
    if not question:
        await ctx.send("Please provide a question for Gemini to answer! Example: `.ask What is the capital of France?`")
        return

    # Define the personality prefix
    # You can change this to any persona you like!
    personality_prefix = "Talk like a person who is british, who speaks fast, is a funny troll and is witty and yaps alot, he acts like he is great at everything but makes funny and comical excuses when he fails at something, his typical excuses are its AI edited or No proof or wasnt me it was Allan. Keep the reply relatively brief (2 paragraphs or less). "

    # Combine the personality prefix with the user's question
    full_query = personality_prefix + question

    try:
        async with ctx.typing():
            response = model.generate_content(full_query) # Send the modified query
            gemini_response_text = response.text

            if len(gemini_response_text) > 2000:
                await ctx.send(f"**Gemini's Response:**\n{gemini_response_text[:1900]}...\n(Response too long, truncated.)")
            else:
                embed = discord.Embed(
                    title="CrazyAI's Answer 🤖",
                    description=gemini_response_text,
                    color=0x4285F4
                )
                embed.set_footer(text=f"Question asked by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred while trying to get a response from Gemini. Please try again later. Error: `{e}`")
        print(f"Gemini API Error: {e}")
 
##################################################################################################################         
@client.command(help="Ask Google Gemini a question and get an AI-generated response with a specific personality.")
@commands.cooldown(1, 15, commands.BucketType.user)
async def askallan(ctx, *, question: str):
    if not question:
        await ctx.send("Please provide a question for Gemini to answer! Example: `.ask What is the capital of France?`")
        return

    # Define the personality prefix
    # You can change this to any persona you like!
    personality_prefix = "Talk like you are from the British hood and with ghanian vibes and you love chelsea fc, pretends to be gay but when you confront him, he denies it and says he is straight, are very lazy, who has a youtube channel where he plays minecraft, rocket league and friday night funking but barely uploads, likes to say phrases like sure man and wowwwww, and makes funny jokes and has friends who make racist jokes towards him and known to be a hacker. Keep the reply relatively brief (2 paragraphs or less)."

    # Combine the personality prefix with the user's question
    full_query = personality_prefix + question

    try:
        async with ctx.typing():
            response = model.generate_content(full_query) # Send the modified query
            gemini_response_text = response.text

            if len(gemini_response_text) > 2000:
                await ctx.send(f"**Gemini's Response:**\n{gemini_response_text[:1900]}...\n(Response too long, truncated.)")
            else:
                embed = discord.Embed(
                    title="AllanAI's Answer 👨🏿",
                    description=gemini_response_text,
                    color=0x4285F4
                )
                embed.set_footer(text=f"Question asked by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred while trying to get a response from Gemini. Please try again later. Error: `{e}`")
        print(f"Gemini API Error: {e}")

##################################################################################################################      
@client.command(help="Ask Google Gemini a question and get an AI-generated response with a specific personality.")
@commands.cooldown(1, 15, commands.BucketType.user)
async def askseb(ctx, *, question: str):
    if not question:
        await ctx.send("Please provide a question for Gemini to answer! Example: `.ask What is the capital of France?`")
        return

    # Define the personality prefix
    # You can change this to any persona you like!
    personality_prefix = "Talk like you are a norwegian young man who loves to play games all day, he gets all the achievements in each game he plays, loves rainbow six siege and hollow knight and the yakuza franchise (his favorite character is majima), likes making sexual remarks, who just randomly shows up and does questionable and mischievous things, he makes fun of his black friend Allan and british friend crazy. Keep the reply relatively brief (2 paragraphs or less). "

    # Combine the personality prefix with the user's question
    full_query = personality_prefix + question

    try:
        async with ctx.typing():
            response = model.generate_content(full_query) # Send the modified query
            gemini_response_text = response.text

            if len(gemini_response_text) > 2000:
                await ctx.send(f"**Gemini's Response:**\n{gemini_response_text[:1900]}...\n(Response too long, truncated.)")
            else:
                embed = discord.Embed(
                    title="SebAI's Answer 🙉",
                    description=gemini_response_text,
                    color=0x4285F4
                )
                embed.set_footer(text=f"Question asked by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred while trying to get a response from Gemini. Please try again later. Error: `{e}`")
        print(f"Gemini API Error: {e}")

client.run(token)