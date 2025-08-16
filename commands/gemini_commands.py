from .bank import get_player_diamonds, update_player_diamonds
import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CHARACTERS_PATH = "data/characters.json"

# Default characters for a new server
DEFAULT_CHARACTERS = {
    "bot_desc": "answer this question in a funny way and less than 1600 characters : "
}

# ------------------------
# File Handling Functions
# ------------------------
def load_characters():
    if not os.path.exists(CHARACTERS_PATH):
        with open(CHARACTERS_PATH, "w") as f:
            json.dump({}, f)
    with open(CHARACTERS_PATH, "r") as f:
        return json.load(f)

def save_characters(characters):
    with open(CHARACTERS_PATH, "w") as f:
        json.dump(characters, f, indent=4)

def get_server_characters(guild_id: int):
    characters = load_characters()
    gid = str(guild_id)
    if gid not in characters:
        characters[gid] = DEFAULT_CHARACTERS.copy()
        save_characters(characters)
    return characters[gid]

def update_server_characters(guild_id: int, new_data: dict):
    characters = load_characters()
    characters[str(guild_id)] = new_data
    save_characters(characters)

# ------------------------
# Main Gemini Commands
# ------------------------
def gemini_commands(model, tree: app_commands.CommandTree):

    async def character_autocomplete(interaction: discord.Interaction, current: str):
        server_chars = get_server_characters(interaction.guild.id)
        character_names = [key.replace("_desc", "") for key in server_chars.keys()]
        return [
            app_commands.Choice(name=name, value=name)
            for name in character_names if current.lower() in name.lower()
        ]

    async def handle_gemini_question(interaction: discord.Interaction, question: str, personality_key: str, title: str):
        server_chars = get_server_characters(interaction.guild.id)

        if personality_key not in server_chars:
            await interaction.followup.send(f"No description found for `{personality_key.replace('_desc', '')}`.")
            return

        full_query = server_chars[personality_key] + question.strip()

        try:
            response = model.generate_content(full_query)
            gemini_response_text = response.text

            embed = discord.Embed(
                title=title,
                color=0x4285F4
            )

            embed.add_field(name=f"{interaction.user.display_name} asked:", value=f"**{question}**", inline=False)

            if len(gemini_response_text) > 1024:
                await interaction.followup.send(
                    f"**Gemini's Response:**\n{gemini_response_text[:1900]}...\n(Response too long, truncated.)"
                )
            else:
                embed.add_field(name="Response:", value=gemini_response_text, inline=False)

            embed.set_footer(text=f"Asked by: {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error getting response from Gemini: `{e}`")
            print(f"Gemini Error: {e}")

    # ------------------------
    # /ask
    # ------------------------
    @tree.command(name="ask", description="Ask a question to a custom personality.")
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.user.id)
    @app_commands.autocomplete(name=character_autocomplete)
    async def ask_command(interaction: discord.Interaction, name: str, question: str):
        await interaction.response.defer()

        # Update player diamonds for using command
        server_id = str(interaction.guild.id) if interaction.guild else "global"
        player_id = str(interaction.user.id)
        update_player_diamonds(server_id, player_id, 100)
                
        key = f"{name.lower()}_desc"
        title = f"{name.capitalize()}'s Answer ✨"
        await handle_gemini_question(interaction, question, key, title)

    # ------------------------
    # /add_character
    # ------------------------
    @tree.command(name="add_character", description="Add a new personality.")
    async def add_character_command(interaction: discord.Interaction, name: str, description: str):
        await interaction.response.defer(ephemeral=True)

        name = name.lower()
        key = f"{name}_desc"

        server_chars = get_server_characters(interaction.guild.id)
        if key in server_chars:
            await interaction.followup.send(f"A character named `{name}` already exists. Try another name or delete it first.")
            return

        description_2 = (
            f"Talk like a person that fits the following description. {description}. "
            "Keep the reply relatively brief (2 paragraphs or less) and you dont have to mention every personality trait."
        )
        server_chars[key] = description_2
        update_server_characters(interaction.guild.id, server_chars)
        await interaction.followup.send(f"Character `{name}` added successfully!")

    # ------------------------
    # /delete_character
    # ------------------------
    @tree.command(name="delete_character", description="Delete a custom character.")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_character_command(interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)

        key = f"{name.lower()}_desc"
        server_chars = get_server_characters(interaction.guild.id)

        if key not in server_chars:
            await interaction.followup.send(f"No character named `{name}` found.")
            return

        del server_chars[key]
        update_server_characters(interaction.guild.id, server_chars)
        await interaction.followup.send(f"Character `{name}` has been deleted.")

    # ------------------------
    # /list_characters
    # ------------------------
    @tree.command(name="list_characters", description="List all available character personalities.")
    async def list_characters_command(interaction: discord.Interaction):
        await interaction.response.defer()

        server_chars = get_server_characters(interaction.guild.id)
        character_names = [key.replace("_desc", "") for key in server_chars.keys()]

        if not character_names:
            await interaction.followup.send("No characters are currently available.")
            return

        embed = discord.Embed(
            title="Available Characters",
            description="\n".join(f"- `{name}`" for name in sorted(character_names)),
            color=0x00FF99
        )
        await interaction.followup.send(embed=embed)
