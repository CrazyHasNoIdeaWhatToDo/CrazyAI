import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import aiohttp
import io
import textwrap
import emoji

def utility_commands(client):
    
    @client.group(name="help", invoke_without_command=True)
    async def help(ctx):
        embed = discord.Embed(title="Help Center ✨", color=0xF49726)
        embed.add_field(
            name="Command Categories:",
            value=(
                "👋 `hello :` says hello back\n"
                "🤖 `ask <character> :` Talk to a custom AI character\n"
                "🤖 `add_character :` Add an AI character\n"
                "🤖 `list_character :` List all available AI characters\n"
                "🖼️ `image :` Generate an image\n"
                "😂 `meme :` Gets a random meme from reddit\n"
                "📸 `screenshot :` Generate a screenshot\n"
                "⚔️ `SOSplay :` Play Siege of Six\n"
                "⚔️ `SOSrules :` Returns Rules for Siege of Six\n"
                "❓ `guess :` Play the guessing game\n"
                "❓ `guess_stats :` Gets the stats for the guessing game\n"
                "❓ `guess_left :` Gets the leftover numbers for the guessing game"
            ),
            inline=False
        )
        embed.set_footer(icon_url=ctx.author.avatar.url, text=f"Help requested by: {ctx.author.display_name}")
        await ctx.send(embed=embed)
        
    @client.command(help="Shows the bot's latency")
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def ping(ctx):
        await ctx.send(f'Ping! **{round(client.latency * 1000)}ms**')

    @client.command(help="Greets the user")
    async def hello(ctx):
        await ctx.send("Hello back! 👋")
        
    @client.command(name='echo')
    @commands.has_permissions(administrator=True)
    async def echo(ctx, *, text: str = None):
        if not text:
            await ctx.send("❗ Please provide a message to echo.")
            return

        # Echo the text
        await ctx.send(text)

        # Delete the user's command message
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")
            
    TWEMOJI_BASE_URL = "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/"

    async def render_text_with_emojis(draw, base_img, text, font, start_pos):
        x, y = start_pos
        for part in emoji.emoji_list(text):
            text = text.replace(part['emoji'], f" {part['emoji']} ")  # pad for split

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
            
    @client.command()
    async def screenshot(ctx):
        if not ctx.message.reference:
            await ctx.send("You need to reply to a message with `.screenshot`.")
            return

        msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)

        # Check if the replied-to message also has a reference (i.e., it's a reply itself)
        reply_snippet = None
        if msg.reference:
            try:
                original_msg = await ctx.channel.fetch_message(msg.reference.message_id)
                snippet_text = original_msg.content[:80] + ('...' if len(original_msg.content) > 80 else '')
                reply_snippet = {
                    'author': original_msg.author.display_name,
                    'text': snippet_text
                }
            except Exception:
                reply_snippet = {
                    'author': 'Unknown',
                    'text': '[Original message not found]'
                }

        # Fetch avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(msg.author.display_avatar.url) as resp:
                avatar_bytes = await resp.read()
        avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((40, 40))

        # Round avatar
        mask = Image.new("L", (40, 40), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 40, 40), fill=255)
        avatar_img.putalpha(mask)

        # Fonts
        username_font = ImageFont.truetype("arialbd.ttf", 16)
        content_font = ImageFont.truetype("arial.ttf", 15)
        timestamp_font = ImageFont.truetype("arial.ttf", 12)
        reply_font = ImageFont.truetype("ariali.ttf", 13)

        # Message text
        wrapper = textwrap.TextWrapper(width=70)
        wrapped_text = wrapper.wrap(msg.content)
        text_height = 20 * len(wrapped_text)

        # Handle attachment (image) in the message
        attachment_img = None
        attachment_height = 0

        for attachment in msg.attachments:
            if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            img_bytes = await resp.read()
                            original_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                            max_width = 450
                            ratio = min(max_width / original_img.width, 1)
                            new_size = (int(original_img.width * ratio), int(original_img.height * ratio))
                            attachment_img = original_img.resize(new_size, Image.Resampling.LANCZOS)
                            attachment_height = new_size[1] + 10
                break

        reply_height = 35 if reply_snippet else 0
        bubble_padding = 20
        height = max(60, text_height + bubble_padding + reply_height + attachment_height + 20)
        width = 600

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw bubble background
        bubble_color = (54, 57, 63)
        draw.rounded_rectangle([(0, 0), (width - 50, height)], radius=15, fill=bubble_color)

        # Paste avatar
        img.paste(avatar_img, (15, 15), avatar_img)

        # Timestamp
        time_str = msg.created_at.strftime("%H:%M UTC")

        # Role color or fallback
        role_color = (255, 255, 255)
        if isinstance(msg.author, discord.Member) and msg.author.top_role and msg.author.top_role.color.value:
            role_color = msg.author.top_role.color.to_rgb()

        # Author name + timestamp
        draw.text((65, 10), msg.author.display_name, font=username_font, fill=role_color)
        draw.text((65 + username_font.getlength(msg.author.display_name) + 10, 13), time_str, font=timestamp_font, fill=(163, 166, 170))

        y_cursor = 35

        # Draw reply snippet if exists
        if reply_snippet:
            reply_text = f"Replying to {reply_snippet['author']}: {reply_snippet['text']}"
            draw.text((65, y_cursor), reply_text, font=reply_font, fill=(200, 200, 200))
            y_cursor += 30

        # Message content
        for line in wrapped_text:
            await render_text_with_emojis(draw, img, line, content_font, (65, y_cursor))
            y_cursor += 22

        # Image attachment
        if attachment_img:
            img.paste(attachment_img, (65, y_cursor), attachment_img)
            y_cursor += attachment_img.height + 10

        # Send
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        await ctx.send(file=discord.File(buffer, "screenshot.png"))
