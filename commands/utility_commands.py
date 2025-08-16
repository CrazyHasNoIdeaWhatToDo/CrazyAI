import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import aiohttp
import io
import textwrap
import emoji
import os
import json

def load_main_config():
    if not os.path.exists("data/config.json"):
        return {}
    with open("data/config.json", "r") as f:
        return json.load(f)
    
    
def utility_commands(tree: app_commands.CommandTree, config: dict, master_server: int):
    @tree.command(name="help", description="Shows the help center for the bot's commands.")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(title="Help Center ✨", color=0xF49726)
        embed.description = "Here's a list of all the commands you can use with this bot, categorized for easy navigation!"

        # General/Utility Commands
        embed.add_field(
            name="🛠️ General & Utility",
            value=(
                "👋 `/hello`: Says hello back!\n"
                "❓ `/help`: Shows this help message."
            ),
            inline=False
        )

        # AI & Character Commands
        embed.add_field(
            name="🤖 AI & Characters",
            value=(
                "`/ask <character>`: Talk to a custom AI character.\n"
                "`/add_character`: Add a new AI character.\n"
                "`/list_characters`: List all available AI characters."
            ),
            inline=False
        )

        # Image & Fun Commands
        embed.add_field(
            name="🖼️ Image & Fun",
            value=(
                "`/image`: Generate an image.\n"
                "`/meme`: Gets a random meme from Reddit.\n"
                "`/screenshot`: Generate a screenshot of a webpage."
            ),
            inline=False
        )

        # Game Commands (Siege of Six)
        embed.add_field(
            name="⚔️ Siege of Six",
            value=(
                "`/SOSplay`: Start a game of Siege of Six.\n"
                "`/SOSrules`: Returns the rules for Siege of Six."
            ),
            inline=False
        )

        # Game Commands (Blackjack)
        embed.add_field(
            name="♠️ Casino",
            value=(
                "`/blackjack <bet>`: Play a game of Blackjack with a bet.\n"
                "`/slots <bet>`: Play a game of Slots with a bet.\n"
                "`/roulette <bet>`: Play a game of Roulette with a bet.\n"
                "`/bank`: See the top 10 players with the most diamonds."
            ),
            inline=False
        )

        embed.set_footer(icon_url=interaction.user.avatar.url, text=f"Help requested by: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @tree.command(name="ping", description="Shows the bot's latency.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 10)
    async def ping_command(interaction: discord.Interaction):
        await interaction.response.send_message(f'Ping! **{round(interaction.client.latency * 1000)}ms**')

    @tree.command(name="hello", description="Greets the user.")
    async def hello_command(interaction: discord.Interaction):
        await interaction.response.send_message("Hello back! 👋")

    @tree.command(name='echo', description="Echos a message as the bot.")
    @app_commands.checks.has_permissions(administrator=True)
    async def echo_command(interaction: discord.Interaction, text: str):
        await interaction.response.send_message("Sending message...", ephemeral=True)
        try:
            await interaction.channel.send(text)
        except Exception as e:
            await interaction.followup.send(f"Failed to send message: {e}", ephemeral=True)

    @tree.command(name="counter", description="Shows the number of counters.")
    async def counter_command(interaction: discord.Interaction):
        if interaction.guild_id != master_server:
            await interaction.response.send_message("This command is not available in this server.", ephemeral=True)
            return
		
        counter_config = load_main_config()
        counter_value = counter_config.get("counter", 0)
        await interaction.response.send_message(f"The counter value is: {counter_value}")
