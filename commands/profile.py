import discord
from discord import app_commands
import json
import os
import io
from PIL import Image, ImageDraw, ImageFont
from .bank import load_bank_data, save_bank_data, get_player_diamonds, update_player_diamonds

# Paths relative to this file
BASE_DIR = os.path.dirname(__file__)
BADGES_FILE = os.path.join(os.path.dirname(BASE_DIR), "data/badges.json") 
SHOP_FILE = os.path.join(os.path.dirname(BASE_DIR), "data/shop.json") 
ICONS_FOLDER = os.path.join(os.path.dirname(BASE_DIR), "icons")

def load_badges():
    if not os.path.exists(BADGES_FILE):
        return {}
    with open(BADGES_FILE, "r") as f:
        return json.load(f)

def load_shop():
    if not os.path.exists(SHOP_FILE):
        return {}
    with open(SHOP_FILE, "r") as f:
        return json.load(f)
    
def create_badge_strip(icon_paths, badge_size=(64, 64), padding=4):
    """
    Load each icon, resize to badge_size (if needed), and paste them
    horizontally with padding. Returns a BytesIO PNG or None if no icons.
    """
    imgs = []
    for p in icon_paths:
        try:
            img = Image.open(p).convert("RGBA")
            if img.size != badge_size:
                img = img.resize(badge_size, Image.LANCZOS)
            imgs.append(img)
        except Exception as e:
            # optionally log the error
            print(f"Failed to open {p}: {e}")

    if not imgs:
        return None

    total_w = sum(img.width for img in imgs) + padding * (len(imgs) - 1)
    max_h = max(img.height for img in imgs)
    strip = Image.new("RGBA", (total_w, max_h), (0, 0, 0, 0))

    x = 0
    for img in imgs:
        strip.paste(img, (x, (max_h - img.height) // 2), img)
        x += img.width + padding

    buf = io.BytesIO()
    strip.save(buf, format="PNG")
    buf.seek(0)
    return buf

def format_price(price: int) -> str:
    if price >= 1000:
        if price % 1000 == 0:
            return f"{price // 1000}k"
        return f"{price / 1000:.1f}k".rstrip("0").rstrip(".") + "k"
    return str(price)

def get_text_size(draw, text, font):
    """Return width, height of text using textbbox (Pillow 10+ safe)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def create_shop_grid(shop_items, badge_size=(64, 64), per_row=3, padding=20):
    def get_text_size(draw, text, font):
        """Return width, height of text using textbbox (Pillow 10+ safe)."""
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Path to your font inside assets/fonts
    font_path = "assets/fonts/ggsans-Normal.ttf"
    font_small = ImageFont.truetype(font_path, 18)
    font_large = ImageFont.truetype(font_path, 20)

    items = list(shop_items.items())
    rows = (len(items) + per_row - 1) // per_row

    cell_w = badge_size[0] + padding * 2
    cell_h = badge_size[1] + padding * 3 + 35  # space for top & bottom text

    img_w = cell_w * per_row
    img_h = cell_h * rows

    shop_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shop_img)

    for idx, (name, price) in enumerate(items):
        col = idx % per_row
        row = idx // per_row

        x0 = col * cell_w
        y0 = row * cell_h

        # Draw badge name (centered)
        text_w, text_h = get_text_size(draw, name, font_large)
        draw.text(
            (x0 + (cell_w - text_w) // 2, y0),
            name,
            fill="white",
            font=font_large
        )

        # Add extra space between badge name and icon
        space_between = 15  # Adjust this value for more or less space

        # Load badge image (lowercase filename to avoid case issues)
        badge_path = os.path.join(ICONS_FOLDER, f"{name.lower()}.png")
        if os.path.exists(badge_path):
            badge_img = Image.open(badge_path).convert("RGBA")
            badge_img = badge_img.resize(badge_size, Image.LANCZOS)
            shop_img.paste(badge_img, (x0 + padding, y0 + text_h + space_between), badge_img)
        else:
            print(f"Badge image not found: {badge_path}")

        # Draw price below (without diamond emoji)
        price_str = f"{format_price(price)}"
        pw, ph = get_text_size(draw, price_str, font_small)
        draw.text(
            (x0 + (cell_w - pw) // 2, y0 + text_h + badge_size[1] + space_between + 8),
            price_str,
            fill="white",
            font=font_small
        )

    buf = io.BytesIO()
    shop_img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def setup_profile_commands(tree: app_commands.CommandTree, master_server_id: int):

    @tree.command(name="profile", description="Show your profile picture, ranks, and badges.")
    async def profile(interaction: discord.Interaction, member: discord.Member = None):
        # restrict to master server only
        #if interaction.guild_id != master_server_id:
        #    await interaction.response.send_message(
        #        "🚫 This command can only be used in Crazy's main server!",
        #        ephemeral=True
        #   )
        #   return

        if member is None:
            member = interaction.user

        # roles (excluding @everyone)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles_display = ", ".join(roles) if roles else "No special roles"

        # build base embed
        embed = discord.Embed(
            title=f"{member.display_name}'s Profile",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Roles", value=roles_display, inline=False)

        # badges
        badges_data = load_badges()
        user_badges = badges_data.get(str(member.id), [])  # list of badge ids

        # build list of icon file paths (case-sensitive!)
        icon_paths = []
        for badge in user_badges:
            candidate = os.path.join(ICONS_FOLDER, f"{badge}.png")
            if os.path.exists(candidate):
                icon_paths.append(candidate)
            else:
                print(f"Badge icon not found: {candidate}")

        if icon_paths:
            buf = create_badge_strip(icon_paths, badge_size=(64, 64), padding=6)
            if buf:
                discord_file = discord.File(fp=buf, filename="badges.png")
                # We add an empty badges field (or names) and attach the compiled image
                embed.add_field(name="Badges", value=" ", inline=False)
                embed.set_image(url="attachment://badges.png")
                await interaction.response.send_message(embed=embed, file=discord_file)
                return

        # no badges or failed to create image
        badges_text = ", ".join(user_badges) if user_badges else "No badges yet"
        embed.add_field(name="Badges", value=badges_text, inline=False)
        await interaction.response.send_message(embed=embed)
        
    @tree.command(name="shop", description="View items available for purchase with diamonds.")
    async def shop(interaction: discord.Interaction):

        shop_items = load_shop()

        buf = create_shop_grid(shop_items)
        discord_file = discord.File(fp=buf, filename="shop_grid.png")

        embed = discord.Embed(
            title="🛒 Server Shop",
            description="Spend your diamonds 💎 to get exclusive badges!",
            color=discord.Color.gold()
        )
        embed.set_image(url="attachment://shop_grid.png")

        await interaction.response.send_message(embed=embed, file=discord_file)


    @tree.command(name="redeem_shop", description="Buy a badge from the shop with your diamonds.")
    @app_commands.describe(badge_name="The name of the badge you want to buy.")
    async def redeem_shop(interaction: discord.Interaction, badge_name: str):

        shop_items = load_shop()
        badge_name_lower = badge_name.lower()

        # Check if badge exists in the shop
        matched_badge = None
        for item, price in shop_items.items():
            if item.lower() == badge_name_lower:
                matched_badge = item
                badge_price = price
                break

        if matched_badge is None:
            await interaction.response.send_message(
                f"❌ Badge `{badge_name}` not found in the shop.",
                ephemeral=True
            )
            return

        # Load badges
        badges_data = load_badges()
        user_id_str = str(interaction.user.id)

        # If user has no entry yet, create one
        if user_id_str not in badges_data:
            badges_data[user_id_str] = []

        # Check if user already owns this badge
        if matched_badge in badges_data[user_id_str]:
            await interaction.response.send_message(
                f"⚠️ You already own the `{matched_badge}` badge.",
                ephemeral=True
            )
            return

        # Get diamond balance from bank
        server_id_str = str(interaction.guild_id)
        user_diamonds = get_player_diamonds(server_id_str, user_id_str)

        if user_diamonds < badge_price:
            await interaction.response.send_message(
                f"💎 You need {badge_price} diamonds to buy `{matched_badge}`, but you only have {user_diamonds}.",
                ephemeral=True
            )
            return

        # Deduct diamonds
        update_player_diamonds(server_id_str, user_id_str, -badge_price)

        # Save badge to user
        badges_data[user_id_str].append(matched_badge)
        with open(BADGES_FILE, "w") as f:
            json.dump(badges_data, f, indent=4)

        await interaction.response.send_message(
            f"✅ You successfully purchased the `{matched_badge}` badge for {badge_price} diamonds! 🎉"
        )