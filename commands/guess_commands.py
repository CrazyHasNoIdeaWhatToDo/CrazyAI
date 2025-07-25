import discord
from discord.ext import commands
import time

# Store guessed numbers and user cooldowns
guessed_numbers = set()
user_cooldowns = {}

# New: Track user guess counts
user_guess_counts = {}

# Define joker numbers
joker_numbers = {}
game_locked = False
command_cooldown = 

def game_commands(client):
    @client.command()
    async def guess(ctx, number: str):
        global game_locked

        if game_locked:
            await ctx.send("🚫 Guessing game locked as the joker was hit.")
            return

        user_id = ctx.author.id
        current_time = time.time()

        if user_id in user_cooldowns:
            elapsed = current_time - user_cooldowns[user_id]
            if elapsed < command_cooldown:
                remaining = int(command_cooldown - elapsed)
                minutes = remaining // 60
                seconds = remaining % 60
                await ctx.send(f"🕒 You're on cooldown! Try again in {minutes}m {seconds}s.")
                return

        try:
            guess_number = int(number)
        except ValueError:
            await ctx.send("❌ Please enter a valid number.")
            return

        if guess_number < 0 or guess_number > 1000:
            await ctx.send("⚠️ Your guess must be between 0 and 1000.")
            return

        if guess_number in guessed_numbers:
            await ctx.send("🔁 That number has already been guessed. Try a different one!")
            return

        guessed_numbers.add(guess_number)
        user_cooldowns[user_id] = current_time

        # 🆕 Track number of guesses per user
        if user_id in user_guess_counts:
            user_guess_counts[user_id] += 1
        else:
            user_guess_counts[user_id] = 1

        if guess_number in joker_numbers:
            game_locked = True
            await ctx.send("💀 You hit a joker number! Guessing game locked.")
            return

        if guess_number == 145:
            await ctx.send("✅ Correct! You guessed the number and won 1k robux! Message Crazy with the Proof.")
        else:
            await ctx.send("❌ Wrong guess. Try again!")

    # 🆕 New stats command
    @client.command()
    async def guess_stats(ctx):
        total_guesses = len(guessed_numbers)

        if not user_guess_counts:
            await ctx.send("📊 No guesses have been made yet.")
            return

        # Sort leaderboard by guess count, descending
        sorted_users = sorted(user_guess_counts.items(), key=lambda x: x[1], reverse=True)

        leaderboard = ""
        for i, (user_id, count) in enumerate(sorted_users[:10], start=1):  # Top 10
            user = await client.fetch_user(user_id)
            leaderboard += f"**{i}.** {user.name} — `{count}` guesses\n"

        stats_message = (
            f"📈 **Guessing Game Stats**\n"
            f"🔢 Total unique guesses: `{total_guesses}`\n\n"
            f"🏆 **Top Guessers:**\n{leaderboard}"
        )
        await ctx.send(stats_message)
        
    # 🆕 New command to list remaining numbers
    @client.command()
    async def guess_left(ctx):
        remaining = [str(num) for num in range(0, 1001) if num not in guessed_numbers]

        if len(remaining) > 300:
            await ctx.send("📉 Too many numbers remaining to list. Try again later!")
            return

        chunk_size = 1900  # Discord message limit buffer
        message = "📋 **Remaining Numbers ({} left):**\n".format(len(remaining))
        remaining_text = ', '.join(remaining)

        # If too long for one message, split into chunks
        if len(remaining_text) + len(message) <= 2000:
            await ctx.send(message + remaining_text)
        else:
            await ctx.send(message)
            for i in range(0, len(remaining_text), chunk_size):
                await ctx.send(remaining_text[i:i+chunk_size])

