import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from io import BytesIO
import openai

# The setup function now accepts master_server_id
def image_commands(openai_client, tree: app_commands.CommandTree, master_server_id: int):
    # This command is now registered globally, but we'll add a check inside the function
    @tree.command(name="image", description="Generate an image using DALL·E 3")
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.user.id)
    async def image(interaction: discord.Interaction, prompt: str):
        # Check if the command is used in the master server
        #if interaction.guild_id != master_server_id:
        #    await interaction.response.send_message(
        #        f"🚫 This command can only be used in Crazy's main server!",
        #        ephemeral=True # Only the user who used the command will see this
        #    )
        #    return

        if not prompt:
            await interaction.response.send_message("Please provide a prompt for the image!", ephemeral=True)
            return

        await interaction.response.defer() # Defer the response as API calls can take time

        try:
            # Create image via DALL·E 3
            response = openai_client.images.generate(
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
                        await interaction.followup.send("Failed to download the image.")
                        return
                    data = await resp.read()
                    image_file = discord.File(BytesIO(data), filename="image.png")

                    embed = discord.Embed(title="Your AI-Generated Image", description=f"Prompt: {prompt}", color=0x3498DB)
                    embed.set_image(url="attachment://image.png")
                    await interaction.followup.send(file=image_file, embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error generating image: `{e}`")
            print(f"DALL·E error: {e}")
