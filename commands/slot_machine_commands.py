from .bank import load_bank_data, save_bank_data, get_player_diamonds, update_player_diamonds
import discord
from discord.ext import commands
from discord import app_commands
import random
import os

# --- Slot Machine Logic ---
def get_weighted_emoji():
    emojis = ['🍗', '🏦', '💰', '💲','🪙', '❌']
    weights = [0.02, 0.06, 0.15, 0.27, 0.40, 0.10]
    return random.choices(emojis, weights, k=1)[0]

def generate_grid():
    return [[get_weighted_emoji() for _ in range(3)] for _ in range(3)]

def format_grid_for_display(grid):
    grid_str = "```\n"
    for row in grid:
        grid_str += " | ".join(row) + "\n"
    grid_str += "```"
    return grid_str

def check_for_wins(grid):
    winning_emojis = []

    # Horizontal
    for row in grid:
        if row[0] == row[1] == row[2]:
            winning_emojis.append(row[0])

    # Vertical
    for col in range(3):
        if grid[0][col] == grid[1][col] == grid[2][col]:
            winning_emojis.append(grid[0][col])

    # Diagonals
    if grid[0][0] == grid[1][1] == grid[2][2]:
        winning_emojis.append(grid[0][0])
    if grid[0][2] == grid[1][1] == grid[2][0]:
        winning_emojis.append(grid[0][2])

    return winning_emojis

def calculate_payout(bet_amount, winning_emojis):
    payout_multipliers = {
        '❌': -1.0,  # Lose your bet again if ❌ matches
        '🪙': 1,
        '💲': 2,
        '💰': 4,
        '🏦': 8,
        '🍗': 20
    }
    return sum(bet_amount * payout_multipliers.get(emoji, 0) for emoji in winning_emojis)

# --- Command Setup ---
def setup_slot_machine_commands(tree: app_commands.CommandTree):
    @tree.command(name="slots", description="Play a game on the emoji slot machine!")
    @app_commands.describe(bet="The amount of diamonds you want to bet.")
    async def slots(interaction: discord.Interaction, bet: int):
        server_id = str(interaction.guild.id)
        player_id = str(interaction.user.id)

        current_diamonds = get_player_diamonds(server_id, player_id)

        # --- Bet validation ---
        if bet <= 0:
            await interaction.response.send_message("You must bet a positive amount of diamonds!", ephemeral=True)
            return
        if bet > 100:
            await interaction.response.send_message("The maximum bet allowed is 💎 100!", ephemeral=True)
            return
        if bet > current_diamonds:
            await interaction.response.send_message(f"You don't have enough diamonds! You have 💎 {current_diamonds}.", ephemeral=True)
            return

        # Take initial bet
        update_player_diamonds(server_id, player_id, -1 * bet)

        # Spin the machine
        grid = generate_grid()
        winning_emojis = check_for_wins(grid)
        total_winnings = calculate_payout(bet, winning_emojis)

        embed = discord.Embed(title="🎰 Emoji Slot Machine! 🎰", color=discord.Color.blue())
        embed.add_field(name="Your Spin", value=format_grid_for_display(grid), inline=False)

        if winning_emojis:
            if total_winnings > 0:
                embed.color = discord.Color.green()
                win_message = "Congratulations! You got winning combinations:\n"
                for emoji in winning_emojis:
                    win_message += f"- 3 x {emoji} match!\n"
                    
                total_winnings_with_bet = total_winnings + bet
                win_message += f"You won: 💎 {total_winnings_with_bet:.2f}!"
                embed.add_field(name="Result", value=win_message, inline=False)
                update_player_diamonds(server_id, player_id, total_winnings + bet)  # Win = payout + bet back
            elif total_winnings < 0:
                embed.color = discord.Color.red()
                loss_message = "Ouch! ❌ matched, and you lost even more!\n"
                for emoji in winning_emojis:
                    loss_message += f"- 3 x {emoji} match!\n"
                loss_message += f"Extra loss: 💎 {-total_winnings:.2f}!"
                embed.add_field(name="Result", value=loss_message, inline=False)
                update_player_diamonds(server_id, player_id, total_winnings)  # Extra loss (negative)
            else:
                embed.color = discord.Color.red()
                embed.add_field(name="Result", value=f"No winning combinations. You lost 💎 {bet:.2f}.", inline=False)
        else:
            embed.color = discord.Color.red()
            embed.add_field(name="Result", value=f"No winning combinations. You lost 💎 {bet:.2f}.", inline=False)

        # Show final balance
        final_diamonds = get_player_diamonds(server_id, player_id)
        embed.add_field(name="Your Diamonds", value=f"💎 {final_diamonds}", inline=True)
        embed.set_footer(text="Good luck on your next spin!")

        await interaction.response.send_message(embed=embed)

    @tree.command(name="bank", description="Shows the top 10 players with the most diamonds in this server")
    async def bank(interaction: discord.Interaction):
        server_id = str(interaction.guild.id)
        bank_data = load_bank_data()

        if server_id not in bank_data or not bank_data[server_id]:
            await interaction.response.send_message("No players found yet! Start playing slots to get on the leaderboard.")
            return

        leaderboard_entries = []
        for player_id, diamonds in bank_data[server_id].items():
            try:
                user = await interaction.client.fetch_user(int(player_id))
                leaderboard_entries.append({"name": user.display_name, "diamonds": diamonds})
            except discord.NotFound:
                leaderboard_entries.append({"name": f"Unknown User ({player_id})", "diamonds": diamonds})
            except Exception as e:
                print(f"Error fetching user {player_id}: {e}")
                leaderboard_entries.append({"name": f"Error User ({player_id})", "diamonds": diamonds})

        leaderboard_entries.sort(key=lambda x: x["diamonds"], reverse=True)

        embed = discord.Embed(
            title=f"💎 Top 10 Diamond Holders in {interaction.guild.name} 💎",
            color=discord.Color.gold()
        )

        description_lines = [
            f"**{i+1}. {entry['name']}**: 💎 {entry['diamonds']}"
            for i, entry in enumerate(leaderboard_entries[:10])
        ]
        embed.description = "\n".join(description_lines)

        await interaction.response.send_message(embed=embed)
