import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import textwrap
import emoji

def setup_screenshot(tree: app_commands.CommandTree):
    TWEMOJI_BASE_URL = "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/"

    async def render_text_with_emojis(draw, base_img, text, font, start_pos):
        """Draw text and emojis together in correct order."""
        x, y = start_pos
        for part in emoji.emoji_list(text):
            text = text.replace(part['emoji'], f" {part['emoji']} ")
        segments = text.split()
        for segment in segments:
            if emoji.is_emoji(segment):
                codepoints = '-'.join(f'{ord(c):x}' for c in segment)
                emoji_url = TWEMOJI_BASE_URL + f"{codepoints}.png"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(emoji_url) as resp:
                            if resp.status == 200:
                                emoji_bytes = await resp.read()
                                emoji_img = Image.open(io.BytesIO(emoji_bytes)).convert("RGBA").resize((20, 20))
                                base_img.paste(emoji_img, (x, y), emoji_img)
                                x += 22
                except Exception as e:
                    print(f"Failed to render emoji {segment}: {e}")
            else:
                draw.text((x, y), segment + ' ', font=font, fill=(220, 221, 222))
                x += int(font.getlength(segment + ' '))

    @tree.command(name="screenshot", description="Creates a screenshot of the replied-to message.")
    @app_commands.guild_only()
    async def screenshot_command(interaction: discord.Interaction):
        if not interaction.channel:
            await interaction.response.send_message("This command can only be used in a channel.", ephemeral=True)
            return

        # Get replied message
        try:
            async for msg in interaction.channel.history(limit=5):
                if msg.reference and msg.reference.resolved and isinstance(msg.reference.resolved, discord.Message):
                    target_msg = msg.reference.resolved
                    break
            else:
                await interaction.response.send_message("You must reply to the target message before using `/screenshot`. I know its stupid but I don't know how to get past this.", ephemeral=True)
                return
        except Exception:
            await interaction.response.send_message("Could not fetch the replied-to message.", ephemeral=True)
            return

        await interaction.response.defer()

        # Fetch avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(target_msg.author.display_avatar.url) as resp:
                avatar_bytes = await resp.read()
        avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((48, 48))

        # Make avatar circular
        mask = Image.new("L", (48, 48), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 48, 48), fill=255)
        avatar_img.putalpha(mask)

        # Fonts
        username_font = ImageFont.truetype("assets/fonts/ggsans-Normal.ttf", 17)
        content_font = ImageFont.truetype("assets/fonts/ggsans-Normal.ttf", 16)
        timestamp_font = ImageFont.truetype("assets/fonts/ggsans-Normal.ttf", 12)

        # Wrap text dynamically
        wrapper = textwrap.TextWrapper(width=70)
        wrapped_text = wrapper.wrap(target_msg.content)
        line_height = 22
        text_height = line_height * len(wrapped_text)

        # Check for image attachment
        attachment_img = None
        if target_msg.attachments:
            first_attachment = target_msg.attachments[0]
            if first_attachment.content_type and "image" in first_attachment.content_type:
                async with aiohttp.ClientSession() as session:
                    async with session.get(first_attachment.url) as resp:
                        attachment_bytes = await resp.read()
                attachment_img = Image.open(io.BytesIO(attachment_bytes)).convert("RGBA")
                max_width = 500
                if attachment_img.width > max_width:
                    ratio = max_width / attachment_img.width
                    new_height = int(attachment_img.height * ratio)
                    attachment_img = attachment_img.resize((max_width, new_height))

        # Canvas size
        padding_x = 65
        padding_y = 15
        width = 600
        height = padding_y * 2 + 25 + text_height
        if attachment_img:
            height += attachment_img.height + 10

        img = Image.new("RGBA", (width, height), (54, 57, 63))
        draw = ImageDraw.Draw(img)

        # Paste avatar
        img.paste(avatar_img, (10, padding_y), avatar_img)

        # Username color
        role_color = (255, 255, 255)
        if isinstance(target_msg.author, discord.Member) and target_msg.author.top_role and target_msg.author.top_role.color.value:
            role_color = target_msg.author.top_role.color.to_rgb()

        # Username + timestamp
        draw.text((padding_x, padding_y), target_msg.author.display_name, font=username_font, fill=role_color)
        time_str = target_msg.created_at.strftime("%H:%M")
        draw.text((padding_x + username_font.getlength(target_msg.author.display_name) + 8, padding_y + 3),
                  time_str, font=timestamp_font, fill=(163, 166, 170))

        # Draw text content
        y_cursor = padding_y + 25
        for line in wrapped_text:
            await render_text_with_emojis(draw, img, line, content_font, (padding_x, y_cursor))
            y_cursor += line_height

        # Draw attachment below text
        if attachment_img:
            img.paste(attachment_img, (padding_x, y_cursor), attachment_img)

        # Send result
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        await interaction.followup.send(file=discord.File(buffer, "screenshot.png"))
