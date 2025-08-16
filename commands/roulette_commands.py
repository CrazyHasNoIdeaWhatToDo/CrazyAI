from .bank import load_bank_data, save_bank_data, get_player_diamonds, update_player_diamonds
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

# --- Roulette Game Constants ---
ROULETTE_NUMBERS = list(range(37))  # 0-36
ROULETTE_AMERICAN_NUMBERS = list(range(37)) + ['00']  # 0, 00, 1-36

# Dictionary mapping numbers to colors (0 and 00 are green)
NUMBER_COLORS = {
    0: 'green', '00': 'green',
    1: 'red', 2: 'black', 3: 'red', 4: 'black', 5: 'red', 6: 'black',
    7: 'red', 8: 'black', 9: 'red', 10: 'black', 11: 'black', 12: 'red',
    13: 'black', 14: 'red', 15: 'black', 16: 'red', 17: 'black', 18: 'red',
    19: 'red', 20: 'black', 21: 'red', 22: 'black', 23: 'red', 24: 'black',
    25: 'red', 26: 'black', 27: 'red', 28: 'black', 29: 'black', 30: 'red',
    31: 'black', 32: 'red', 33: 'black', 34: 'red', 35: 'black', 36: 'red',
}

# --- Roulette Game Logic ---
def get_payout(bet_type, winning_number):
    """
    Calculates the payout multiplier for a given bet type and winning number.
    Returns the multiplier (e.g., 2 for even money, 36 for straight up).
    """
    winning_color = NUMBER_COLORS.get(winning_number)
    winning_number_is_int = isinstance(winning_number, int)

    # Straight Up
    if isinstance(bet_type, int) and bet_type == winning_number:
        return 36
    if isinstance(bet_type, str) and bet_type == winning_number:  # For '00'
        return 36

    # Split
    if isinstance(bet_type, tuple) and winning_number in bet_type and len(bet_type) == 2:
        return 18
    
    # Street
    if isinstance(bet_type, tuple) and winning_number in bet_type and len(bet_type) == 3:
        return 12

    # Corner
    if isinstance(bet_type, tuple) and winning_number in bet_type and len(bet_type) == 4:
        return 9
    
    # Dozen
    if bet_type == '1st12' and 1 <= winning_number <= 12:
        return 3
    if bet_type == '2nd12' and 13 <= winning_number <= 24:
        return 3
    if bet_type == '3rd12' and 25 <= winning_number <= 36:
        return 3

    # Column
    if bet_type == 'col1' and winning_number_is_int and winning_number % 3 == 1:
        return 3
    if bet_type == 'col2' and winning_number_is_int and winning_number % 3 == 2:
        return 3
    if bet_type == 'col3' and winning_number_is_int and winning_number % 3 == 0 and winning_number != 0:
        return 3

    # High or Low
    if bet_type == 'low' and 1 <= winning_number <= 18:
        return 2
    if bet_type == 'high' and 19 <= winning_number <= 36:
        return 2

    # Red or Black
    if bet_type == winning_color:
        return 2

    # Odd or Even
    if bet_type == 'even' and winning_number_is_int and winning_number != 0 and winning_number % 2 == 0:
        return 2
    if bet_type == 'odd' and winning_number_is_int and winning_number % 2 != 0:
        return 2

    return 0

def format_bet_string(bet_type):
    """Returns a user-friendly string for the bet type."""
    if isinstance(bet_type, int):
        return f"a straight up bet on **{bet_type}**"
    if bet_type == '00':
        return f"a straight up bet on **{bet_type}**"
    if isinstance(bet_type, tuple):
        if len(bet_type) == 2: return f"a split bet on **{bet_type[0]} and {bet_type[1]}**"
        if len(bet_type) == 3: return f"a street bet on **{bet_type[0]}**'s row"
        if len(bet_type) == 4: return f"a corner bet on **{bet_type[0]}, {bet_type[1]}, {bet_type[2]}, and {bet_type[3]}**"
    if bet_type in ['red', 'black', 'green']: return f"a bet on **{bet_type}**"
    if bet_type in ['odd', 'even']: return f"a bet on **{bet_type}** numbers"
    if bet_type in ['low', 'high']: return f"a bet on **{bet_type}** numbers (1-18 or 19-36)"
    if bet_type in ['1st12', '2nd12', '3rd12']: return f"a bet on the **{bet_type.replace('12', ' 12 ')}**"
    if bet_type in ['col1', 'col2', 'col3']: return f"a bet on the **{bet_type.replace('col', 'column ')}**"
    return str(bet_type)

def setup_roulette_commands(tree: app_commands.CommandTree):
    """Sets up the Roulette slash command."""

    @tree.command(name="roulette", description="Play a game of roulette!")
    @app_commands.describe(bet="The amount of diamonds you want to bet.",
                           bet_type="The type of bet you want to make.",
                           value="For bets like split or straight up, provide numbers separated by dashes (e.g. '1-2').")
    @app_commands.choices(bet_type=[
        app_commands.Choice(name="Straight Up (Number 0-36)", value="straight_up"),
        app_commands.Choice(name="Split (e.g., '1-2')", value="split"),
        app_commands.Choice(name="Street (e.g., '1-2-3')", value="street"),
        app_commands.Choice(name="Corner (e.g., '1-2-4-5')", value="corner"),
        app_commands.Choice(name="Red", value="red"),
        app_commands.Choice(name="Black", value="black"),
        app_commands.Choice(name="Odd", value="odd"),
        app_commands.Choice(name="Even", value="even"),
        app_commands.Choice(name="Low (1-18)", value="low"),
        app_commands.Choice(name="High (19-36)", value="high"),
        app_commands.Choice(name="1st Dozen (1-12)", value="1st12"),
        app_commands.Choice(name="2nd Dozen (13-24)", value="2nd12"),
        app_commands.Choice(name="3rd Dozen (25-36)", value="3rd12"),
        app_commands.Choice(name="1st Column", value="col1"),
        app_commands.Choice(name="2nd Column", value="col2"),
        app_commands.Choice(name="3rd Column", value="col3"),
    ])
    async def roulette(interaction: discord.Interaction, bet: int, bet_type: app_commands.Choice[str], value: str = None):
        server_id = str(interaction.guild.id)
        player_id = str(interaction.user.id)
        current_diamonds = get_player_diamonds(server_id, player_id)

        # 1. Validate Bet
        if bet <= 0:
            await interaction.response.send_message("You must bet a positive amount of diamonds!", ephemeral=True)
            return
        if bet > current_diamonds:
            await interaction.response.send_message(f"You don't have enough diamonds! You have 💎 {current_diamonds}.", ephemeral=True)
            return

        # 2. Parse and Validate the Bet Type and Value
        parsed_bet = None
        if bet_type.value in ['red', 'black', 'odd', 'even', 'low', 'high', '1st12', '2nd12', '3rd12', 'col1', 'col2', 'col3']:
            parsed_bet = bet_type.value
        elif bet_type.value == 'straight_up':
            try:
                parsed_bet = int(value)
                if parsed_bet not in range(37):
                    await interaction.response.send_message("Straight Up bet must be a number between 0 and 36.", ephemeral=True)
                    return
            except (ValueError, TypeError):
                await interaction.response.send_message("For a Straight Up bet, please provide a number between 0 and 36.", ephemeral=True)
                return
        elif bet_type.value in ['split', 'street', 'corner']:
            try:
                numbers = tuple(int(x) for x in value.split('-'))
                if bet_type.value == 'split' and len(numbers) == 2:
                    parsed_bet = numbers
                elif bet_type.value == 'street' and len(numbers) == 3:
                    parsed_bet = numbers
                elif bet_type.value == 'corner' and len(numbers) == 4:
                    parsed_bet = numbers
                else:
                    await interaction.response.send_message(f"Invalid number of values for {bet_type.value} bet.", ephemeral=True)
                    return
                # Add basic validation here if needed (omitted for brevity)
            except Exception:
                await interaction.response.send_message(f"For a {bet_type.value} bet, provide numbers separated by dashes (e.g. '1-2').", ephemeral=True)
                return
        else:
            await interaction.response.send_message("Invalid bet type.", ephemeral=True)
            return

        # 3. Deduct the bet upfront
        update_player_diamonds(server_id, player_id, -bet)

        # 4. Spin the wheel
        winning_number = random.choice(ROULETTE_NUMBERS)  # For now, European roulette 0-36

        payout_multiplier = get_payout(parsed_bet, winning_number)
        winnings = bet * payout_multiplier

        # 5. Calculate and update diamonds if player won
        if payout_multiplier > 0:
            update_player_diamonds(server_id, player_id, winnings)

        # 6. Prepare result message
        embed = discord.Embed(title="🎰 Roulette Results 🎰", color=discord.Color.gold())
        embed.add_field(name="Your Bet", value=f"{format_bet_string(parsed_bet)} for 💎 {bet}", inline=False)
        embed.add_field(name="Winning Number", value=f"**{winning_number}** ({NUMBER_COLORS.get(winning_number, 'Unknown').capitalize()})", inline=False)
        if payout_multiplier > 0:
            embed.add_field(name="You Won!", value=f"Congratulations! You won 💎 {winnings}!", inline=False)
        else:
            embed.add_field(name="You Lost", value="Better luck next time!", inline=False)
        embed.set_footer(text=f"Your new balance: 💎 {get_player_diamonds(server_id, player_id)}")

        await interaction.response.send_message(embed=embed)

