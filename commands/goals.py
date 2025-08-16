import discord
from discord import app_commands
import json
import os
import random
from .bank import load_bank_data, save_bank_data, get_player_diamonds, update_player_diamonds

GOALS_FILE = "data/goals.json"

def load_goals():
    if not os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(GOALS_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    return data

def save_goals(data):
    with open(GOALS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def format_progress(current, target):
    return f"{current} / {target}"

def get_goals_list(goals):
    goals_sorted = sorted(goals.items(), key=lambda x: x[0])
    return [(i+1, desc, progress[0], progress[1]) for i, (desc, progress) in enumerate(goals_sorted)]

def setup_goal_commands(tree: app_commands.CommandTree, master_server_id: int):

    @tree.command(name="goals", description="List all current goals and their progress.")
    async def goals(interaction: discord.Interaction):
        # Restrict to master server only
        if interaction.guild_id != master_server_id:
            await interaction.response.send_message(
                "🚫 This command can only be used in Crazy's main server!",
                ephemeral=True
            )
            return

        goals = load_goals()
        if not goals:
            await interaction.response.send_message("There are no active goals right now.")
            return

        goals_list = get_goals_list(goals)
        embed = discord.Embed(title="Current Goals", color=discord.Color.blue())
        for goal_id, desc, current, target in goals_list:
            embed.add_field(
                name=f"#{goal_id} - {desc}",
                value=f"Progress: {format_progress(current, target)} diamonds",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @tree.command(name="redeem_goals", description="Contribute diamonds to a goal.")
    @app_commands.describe(goal_id="The goal number to contribute to", diamonds="Amount of diamonds to spend")
    async def redeem_goals(interaction: discord.Interaction, goal_id: int, diamonds: int):
        # Restrict to master server only
        if interaction.guild_id != master_server_id:
            await interaction.response.send_message(
                "🚫 This command can only be used in Crazy's main server!",
                ephemeral=True
            )
            return

        if diamonds <= 0:
            await interaction.response.send_message("You must redeem a positive number of diamonds.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)
        player_id = str(interaction.user.id)

        goals = load_goals()
        goals_list = get_goals_list(goals)

        if goal_id < 1 or goal_id > len(goals_list):
            await interaction.response.send_message("Invalid goal ID. Use /goals to see goal numbers.", ephemeral=True)
            return

        _, goal_desc, current, target = goals_list[goal_id - 1]

        player_balance = get_player_diamonds(server_id, player_id)
        if player_balance < diamonds:
            await interaction.response.send_message(f"You don't have enough diamonds. Your balance: {player_balance}", ephemeral=True)
            return

        new_progress = min(current + diamonds, target)
        goals[goal_desc][0] = new_progress

        update_player_diamonds(server_id, player_id, -diamonds)
        save_goals(goals)

        await interaction.response.send_message(
            f"Successfully contributed {diamonds} diamonds to **{goal_desc}**! "
            f"Progress: {new_progress} / {target} diamonds."
        )

        if new_progress >= target:
            channel = interaction.channel
            await channel.send(f"🎉 Goal **{goal_desc}** has been completed! Congratulations everyone!")
            
    @tree.command(name="donate", description="Donate diamonds to another player.")
    @app_commands.describe( member="The member you want to donate diamonds to",diamonds="Amount of diamonds to donate")
    async def donate(interaction: discord.Interaction, member: discord.Member, diamonds: int):

        if diamonds <= 0:
            await interaction.response.send_message(
                "You must donate a positive number of diamonds.",
                ephemeral=True
            )
            return

        server_id = str(interaction.guild_id)
        donor_id = str(interaction.user.id)
        recipient_id = str(member.id)

        if donor_id == recipient_id:
            await interaction.response.send_message(
                "You can't donate diamonds to yourself.",
                ephemeral=True
            )
            return

        donor_balance = get_player_diamonds(server_id, donor_id)
        if donor_balance < diamonds:
            await interaction.response.send_message(
                f"You don't have enough diamonds. Your balance: {donor_balance}",
                ephemeral=True
            )
            return

        # Update both balances
        update_player_diamonds(server_id, donor_id, -diamonds)
        update_player_diamonds(server_id, recipient_id, diamonds * 1.1)

        await interaction.response.send_message( f"💎 {interaction.user.mention} donated **{diamonds} diamonds plus {diamonds * 0.1} diamonds (+10% charity boost)** to {member.mention}!")
        
    @tree.command(name="steal", description="Attempt to steal diamonds from another player.")
    @app_commands.describe(member="The member you want to steal from",diamonds="Amount of diamonds you want to steal")
    async def steal(interaction: discord.Interaction, member: discord.Member, diamonds: int):
        if diamonds <= 0:
            await interaction.response.send_message(
                "You must try to steal a positive number of diamonds.",
                ephemeral=True
            )
            return

        server_id = str(interaction.guild_id)
        stealer_id = str(interaction.user.id)
        victim_id = str(member.id)

        if stealer_id == victim_id:
            await interaction.response.send_message(
                "You can't steal from yourself. Nice try though. 😏",
                ephemeral=True
            )
            return

        stealer_balance = get_player_diamonds(server_id, stealer_id)
        victim_balance = get_player_diamonds(server_id, victim_id)

        if stealer_balance < diamonds:
            await interaction.response.send_message(
                f"You can't attempt to steal more diamonds than you have! Your balance: {stealer_balance}",
                ephemeral=True
            )
            return

        if victim_balance < diamonds:
            await interaction.response.send_message(
                f"{member.display_name} doesn't have {diamonds} diamonds to steal.",
                ephemeral=True
            )
            return

        # Roll two 6-sided dice
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)
        total_roll = roll1 + roll2

        result_message = f"🎲 You rolled **{roll1}** and **{roll2}** (total **{total_roll}**).\n"

        if total_roll >= 9:
            # Success
            update_player_diamonds(server_id, stealer_id, diamonds)
            update_player_diamonds(server_id, victim_id, -diamonds)
            result_message += f"✅ Success! You stole **{diamonds} diamonds** from {member.mention}!"
        elif total_roll <= 4:
            # Critical fail
            update_player_diamonds(server_id, stealer_id, -diamonds)
            result_message += f"❌ Critical fail! You lost **{diamonds} diamonds** to {member.mention}!"
        else:
            # Mild fail
            penalty = random.choice([0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35]) * diamonds
            penalty = min(penalty, stealer_balance)  # Can't lose more than you have
            update_player_diamonds(server_id, stealer_id, -penalty)
            result_message += f"⚠️ Fail! You lost **{penalty} diamonds** in the process."

        await interaction.response.send_message(result_message)
