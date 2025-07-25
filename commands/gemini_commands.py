import discord
from discord.ext import commands
import json
import os

CHARACTERS_PATH = "characters.json"

def load_characters():
    with open(CHARACTERS_PATH, "r") as f:
        return json.load(f)

def save_characters(characters):
    with open(CHARACTERS_PATH, "w") as f:
        json.dump(characters, f, indent=4)

def gemini_commands(model, client):
    config = load_characters()

    async def handle_gemini_question(ctx, question: str, personality_key: str, title: str):
        user_input = question or ""

        if ctx.message.reference:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            combined_question = (user_input + " " + replied_message.content).strip()
        else:
            combined_question = user_input.strip()

        if not combined_question:
            await ctx.send("Please provide a question. Example: `/ask allan What is love?`")
            return

        # Reload config each time to get updates
        config = load_characters()

        if personality_key not in config:
            await ctx.send(f"No description found for `{personality_key}`.")
            return

        full_query = config[personality_key] + combined_question

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
                    embed.set_footer(text=f"Asked by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
                    await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error getting response from Gemini: `{e}`")
            print(f"Gemini Error: {e}")

    @client.command(name="ask", help="Ask a question to a custom personality. Usage: /ask <name> <question>")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def ask(ctx, name: str, *, question: str = None):
        key = f"{name.lower()}_desc"
        title = f"{name.capitalize()}'s Answer ✨"
        await handle_gemini_question(ctx, question, key, title)

    @client.command(name="add_character", help="Add a new personality. Usage: /add_character <name> <description>")
    async def add_character(ctx, name: str, *, description: str):
        name = name.lower()
        key = f"{name}_desc"
        
        config = load_characters()
        if key in config:
            await ctx.send(f"A character named `{name}` already exists. Try another name or delete it first.")
            return

        config[key] = description
        save_characters(config)
        await ctx.send(f"Character `{name}` added successfully!")

    @client.command(name="delete_character", help="Delete a custom character. Usage: /delete_character <name>")
    @commands.has_permissions(administrator=True)
    async def delete_character(ctx, name: str):
        key = f"{name.lower()}_desc"
        characters = load_characters()

        if key not in characters:
            await ctx.send(f"No character named `{name}` found.")
            return

        del characters[key]
        save_characters(characters)
        await ctx.send(f"Character `{name}` has been deleted.")
        
    @client.command(name="list_characters", help="List all available character personalities.")
    async def list_characters(ctx):
        characters = load_characters()
        character_names = [key.replace("_desc", "") for key in characters.keys()]

        if not character_names:
            await ctx.send("No characters are currently available.")
            return

        embed = discord.Embed(
            title="Available Characters",
            description="\n".join(f"- `{name}`" for name in sorted(character_names)),
            color=0x00FF99
        )
        await ctx.send(embed=embed)
