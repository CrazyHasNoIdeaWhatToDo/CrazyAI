import discord
from discord.ext import commands
import aiohttp
import random

def fun_commands(client):
    @client.command()
    async def meme(ctx):
        wholesome_subreddits = ["wholesomememes", "memes", "cleanmemes"]
        subreddit = random.choice(wholesome_subreddits)

        async with aiohttp.ClientSession() as session:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
            headers = {"User-Agent": "discord-family-friendly-meme-bot"}
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await ctx.send("⚠️ Couldn't fetch memes right now. Try again later!")
                    return

                data = await response.json()
                posts = data["data"]["children"]

                # Filter: not NSFW and has an image URL
                safe_posts = [
                    post for post in posts
                    if not post["data"]["over_18"] and post["data"]["url"].endswith(('.jpg', '.png', '.jpeg', '.gif'))
                ]

                if not safe_posts:
                    await ctx.send("🚫 No family-friendly memes found right now. Try again later!")
                    return

                meme = random.choice(safe_posts)
                title = meme["data"]["title"]
                image_url = meme["data"]["url"]

                await ctx.send(f"**{title}**\n{subreddit.capitalize()} 🔹 {image_url}")

