import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import random
from collections import deque

HUMOR_API_KEY = "Insert your key here"

# Keep last 20 meme URLs to avoid repeats
recent_memes = deque(maxlen=20)

SOURCES = [
    {"name": "meme-api", "url": "https://meme-api.com/gimme"},
    {"name": "imgflip", "url": "https://api.imgflip.com/get_memes"},
]

if HUMOR_API_KEY:
    SOURCES.append({
        "name": "humor",
        "url": "https://api.humorapi.com/memes/random",
        "headers": {"X-Api-Key": HUMOR_API_KEY}
    })

async def fetch_meme_from_source(session, source):
    try:
        if source["name"] == "meme-api":
            async with session.get(source["url"]) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return {
                    "title": data.get("title", "Meme"),
                    "url": data.get("url"),
                    "source": f"r/{data.get('subreddit', 'unknown')}"
                }

        elif source["name"] == "imgflip":
            async with session.get(source["url"]) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                memes = data.get("data", {}).get("memes", [])
                if not memes:
                    return None
                meme = random.choice(memes)
                return {
                    "title": meme.get("name", "Meme"),
                    "url": meme.get("url"),
                    "source": "imgflip"
                }

        elif source["name"] == "humor":
            async with session.get(source["url"], headers=source.get("headers", {})) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return {
                    "title": data.get("description", "Meme"),
                    "url": data.get("url"),
                    "source": "humorapi"
                }

    except Exception:
        return None

    return None


def is_new_meme(url):
    if url in recent_memes:
        return False
    recent_memes.append(url)
    return True


def get_random_source():
    return random.choice(SOURCES)


def remove_duplicates(results):
    seen = set()
    unique_results = []
    for r in results:
        if r and r["url"] not in seen:
            unique_results.append(r)
            seen.add(r["url"])
    return unique_results


def get_meme_safe(meme_list):
    # Return first meme that is new (not in recent_memes)
    for meme in meme_list:
        if meme and meme["url"] and is_new_meme(meme["url"]):
            return meme
    return None


def format_source_name(src):
    if src.startswith("r/"):
        return src
    else:
        return src.capitalize()


def fun_commands(tree: app_commands.CommandTree):
    @tree.command(name="meme", description="Get a random meme from multiple sources.")
    async def meme(interaction: discord.Interaction):
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            attempts = 0
            memes_found = []

            while attempts < 5:
                source = get_random_source()
                meme_data = await fetch_meme_from_source(session, source)
                if meme_data:
                    memes_found.append(meme_data)

                # Try to pick a meme that is not repeated
                meme = get_meme_safe(memes_found)
                if meme:
                    embed = discord.Embed(
                        title=meme["title"],
                        color=discord.Colour.random()
                    )
                    embed.set_image(url=meme["url"])
                    embed.set_footer(text=f"Source: {format_source_name(meme['source'])}")
                    await interaction.followup.send(embed=embed)
                    return

                attempts += 1

            # If here, no meme found or all were repeats
            await interaction.followup.send("⚠️ Couldn't find a new meme right now. Try again later!")
