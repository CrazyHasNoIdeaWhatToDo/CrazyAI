import discord
from discord.ext import commands
import aiohttp
from io import BytesIO

def image_commands(openai, client):        
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
