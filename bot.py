import discord
from discord.ext import commands
import json
import google.generativeai as genai
import openai
import aiohttp
from io import BytesIO

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

async def handle_gemini_question(ctx, question: str, personality_key: str, title: str):
    if not question:
        await ctx.send("Please provide a question for Gemini to answer! Example: `.askcrazy What is the capital of France?`")
        return

    personality_prefix = config[personality_key]
    full_query = personality_prefix + question

    try:
        async with ctx.typing():
            response = model.generate_content(full_query)
            gemini_response_text = response.text

            if len(gemini_response_text) > 2000:
                await ctx.send(f"**Gemini's Response:**\n{gemini_response_text[:1900]}...\n(Response too long, truncated.)")
            else:
                embed = discord.Embed(
                    title=title,
                    description=gemini_response_text,
                    color=0x4285F4
                )
                embed.set_footer(text=f"Question asked by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred while trying to get a response from Gemini. Please try again later. Error: `{e}`")
        print(f"Gemini API Error: {e}")

@client.group(name="crazyhelp", invoke_without_command=True)
async def crazyhelp(ctx):
    embed = discord.Embed(title="Help Center ✨", color=0xF49726)
    embed.add_field(
        name="Command Categories:",
        value=(
            "😃 `hello :` says hello back\n"
            "👻 `askcustompersonality :` Talk to Custom personality AI\n"
            "🤖 `askai :` Ask AI a question\n"
            "🖼️ `image :` Generate an image\n"
            "To view the commands of a category, send `.crazyhelp <category>`"
        ),
        inline=False
    )
    embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Help requested by: {ctx.author.display_name}")
    await ctx.send(embed=embed)

@crazyhelp.command()
async def ai(ctx):
    embed = discord.Embed(title="Help Center ✨", description="Commands of **AI**\n`.ask <query>:` Ask Google Gemini a question", color=0xF49726)
    embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Command requested by: {ctx.author.display_name}")
    await ctx.send(embed=embed)
        
@client.command(name="askcrazy", help="Ask CrazyAI a question.")
@commands.cooldown(1, 15, commands.BucketType.user)
async def askcustompersonality(ctx, *, question: str = None):
    await handle_gemini_question(ctx, question, "crazy_desc", "CrazyAI's Answer 👻")
    
@client.command(help="Shows the bot's latency")
@commands.cooldown(1, 10, commands.BucketType.channel)
async def ping(ctx):
    await ctx.send(f'Ping! **{round(client.latency * 1000)}ms**')

@client.command(help="Greets the user")
async def hello(ctx):
    await ctx.send("Hello back! 👋")
    
@client.command(help="Displays all available commands")
async def allcommands(ctx):
    embed = discord.Embed(title="All Commands 🧾", color=0xF49726)
    cmds = [f"`{prefix}{command.name}` - {command.help or 'No description'}" for command in client.commands if not command.hidden]
    embed.description = "\n".join(cmds)
    embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Requested by: {ctx.author.display_name}")
    await ctx.send(embed=embed)
    
@client.command(name="image", help="Generate an image using DALL·E 3")
@commands.cooldown(1, 30, commands.BucketType.user)
async def image(ctx, *, prompt: str = None):
    if not prompt:
        await ctx.send("Please provide a prompt for the image!")
        return

    await ctx.send("🎨 Generating image... this might take a few seconds.")
    
    try:
        # Create image via DALL·E 3
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        image_url = response.data[0].url

        # Download image and send as file
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    await ctx.send("Failed to download the image.")
                    return
                data = await resp.read()
                image_file = discord.File(BytesIO(data), filename="image.png")

                embed = discord.Embed(title="Your AI-Generated Image", description=f"Prompt: {prompt}", color=0x3498DB)
                embed.set_image(url="attachment://image.png")
                await ctx.send(file=image_file, embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error generating image: `{e}`")
        print(f"DALL·E error: {e}")
        
client.run(token)
