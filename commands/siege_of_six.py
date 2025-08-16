from .bank import get_player_diamonds, update_player_diamonds
import discord
from discord.ext import commands
from discord import app_commands
import random
import nltk
from nltk.corpus import words, brown
import asyncio
from collections import Counter

# NLTK downloads for word and frequency data
nltk.download('words')
nltk.download('brown')

def siege_of_six_commands(config, tree: app_commands.CommandTree):
    
    @tree.command(name="sosrules", description="Shows the rules for Siege of Six.")
    async def sosrules(interaction: discord.Interaction):
        rules = (
            "**Siege of Six (SOS) Rules:**\n"
            "🧠 You have to guess a hidden 6-letter word.\n"
            "🔠 You are given 8 jumbled letters: 6 correct, 2 fake consonants.\n"
            "🎯 You have 6 attempts to guess the correct word.\n"
            "💡 On attempt 3, one fake letter is removed.\n"
            "💡 On attempt 5, both fake letters are removed.\n"
            "⚔️ Can you breach the Siege of Six?"
        )
        await interaction.response.send_message(rules)

    @tree.command(name="sosplay", description="Starts a game of Siege of Six.")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard"),
        app_commands.Choice(name="Extreme", value="extreme"),
        app_commands.Choice(name="Impossible", value="impossible")
    ])
    async def sosplay(interaction: discord.Interaction, difficulty: app_commands.Choice[str]):
        difficulty = difficulty.value.lower()

        # Difficulty ranges: (min_freq, max_freq)
        difficulty_ranges = {
            "easy": (10, float("inf")),
            "medium": (5, 8),
            "hard": (3, 4),
            "extreme": (1, 2),
            "impossible" : (0,0)
        }

        min_freq, max_freq = difficulty_ranges[difficulty]

        await interaction.response.defer() # Defer the response as this can take time

        brown_words = [w.lower() for w in brown.words()]
        brown_freq = Counter(brown_words)

        word_list = [
            w.lower() for w in words.words()
            if (
                len(w) == 6 and w.isalpha() and
                min_freq <= brown_freq[w.lower()] <= max_freq
            )
        ]

        if not word_list:
            await interaction.followup.send("❌ No suitable words found for that difficulty. Try a different one.")
            return

        original_word = random.choice(word_list)

        vowels = set("aeiou")
        alphabet = [chr(i) for i in range(97, 123)]
        consonants = [c for c in alphabet if c not in vowels]

        extras = []
        while len(extras) < 2:
            letter = random.choice(consonants)
            if letter not in original_word and letter not in extras:
                extras.append(letter)

        jumbled = list(original_word + ''.join(extras))
        random.shuffle(jumbled)

        # Create the initial embed
        embed = discord.Embed(
            title="Siege of Six",
            description=f"**Difficulty:** {difficulty.capitalize()}\nGuess the original 6-letter word from these letters:",
            color=0x00FF00
        )
        embed.add_field(name="Current Letters:", value=f"`{' '.join(jumbled)}`", inline=False)
        embed.set_footer(text=f"Game started by {interaction.user.display_name}")

        # Send the initial embed and store the message object
        game_message = await interaction.followup.send(embed=embed)
        
        attempts = 6

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        for attempt in range(1, attempts + 1):
            hint_message = ""
            if attempt == 3 and extras[0] in jumbled:
                jumbled.remove(extras[0])
                hint_message = "💡 Hint: One fake letter has been removed!"
            elif attempt == 5 and extras[1] in jumbled:
                jumbled.remove(extras[1])
                hint_message = "💡 Hint: Both fake letters have been removed!"

            random.shuffle(jumbled)
            
            # Update the embed with the new attempt and letters
            embed.set_field_at(0, name=f"Attempt {attempt}/6:", value=f"`{' '.join(jumbled)}`", inline=False)
            
            # If there's a hint, add it to the embed's description
            if hint_message:
                embed.description += f"\n\n{hint_message}"
            
            # Edit the message with the updated embed
            await game_message.edit(embed=embed)

            # Wait for the user's guess
            try:
                guess_msg = await interaction.client.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await game_message.edit(
                    content=f"⌛ Game over! You took too long. The word was **{original_word}**",
                    embed=None
                )
                # Give 30 diamonds for losing by timeout
                server_id = str(interaction.guild.id) if interaction.guild else "global"
                player_id = str(interaction.user.id)
                update_player_diamonds(server_id, player_id, 30)
                await interaction.followup.send("💎 You earned 30 diamonds for participating!")
                return

            guess = guess_msg.content.strip().lower()
            await guess_msg.delete() # Delete the user's guess to keep the channel clean

            if guess == original_word:
                embed.description += f"\n\n🎉 Correct! You breached the Siege of Six!"
                embed.color = discord.Color.green()
                await game_message.edit(embed=embed)

                # Award diamonds based on difficulty
                diamond_rewards = {
                    "easy": 30,
                    "medium": 50,
                    "hard": 100,
                    "extreme": 200,
                    "impossible": 500
                }
                
                reward = diamond_rewards.get(difficulty, 30)  # default fallback 50
                reward = reward * (7 - attempt)
                
                # Update player diamonds
                server_id = str(interaction.guild.id) if interaction.guild else "global"
                player_id = str(interaction.user.id)
                update_player_diamonds(server_id, player_id, reward)

                await interaction.followup.send(f"💎 You earned {reward} diamonds for winning!")

                return
            else:
                embed.description += f"\n\n❌ Incorrect guess: `{guess}`"
                embed.color = discord.Color.red()
                await game_message.edit(embed=embed)
                # Reset the description color for the next round
                embed.color = discord.Color.blue() 
        
        # If all attempts are used up
        embed.description += f"\n\n💀 Game Over! The correct word was: **{original_word}**"
        embed.color = discord.Color.red()
        await game_message.edit(embed=embed)

        # Give 30 diamonds for losing
        server_id = str(interaction.guild.id) if interaction.guild else "global"
        player_id = str(interaction.user.id)
        update_player_diamonds(server_id, player_id, 30)

        await interaction.followup.send("💎 You earned 30 diamonds for participating!")
