import discord
from discord.ext import commands
import random
import nltk
from nltk.corpus import words, brown
import asyncio
from collections import Counter

nltk.download('words')
nltk.download('brown')

def siege_of_six_commands(config, client):
    @client.command()
    async def SOSrules(ctx):
        rules = (
            "**Siege of Six (SOS) Rules:**\n"
            "🧠 You have to guess a hidden 6-letter word.\n"
            "🔠 You are given 8 jumbled letters: 6 correct, 2 fake consonants.\n"
            "🎯 You have 6 attempts to guess the correct word.\n"
            "💡 On attempt 3, one fake letter is removed.\n"
            "💡 On attempt 5, both fake letters are removed.\n"
            "⚔️ Can you breach the Siege of Six?"
        )
        await ctx.send(rules)

    @client.command()
    async def SOSplay(ctx, difficulty: str = None):
        if difficulty is None:
            await ctx.send("❗ You must choose a difficulty level.\nUsage: `!SOSplay <easy|medium|hard|extreme>`")
            return

        difficulty = difficulty.lower()

        # Difficulty ranges: (min_freq, max_freq)
        difficulty_ranges = {
            "easy": (8, float("inf")),
            "medium": (4, 7),
            "hard": (2, 3),
            "extreme": (0, 1)
        }

        if difficulty not in difficulty_ranges:
            await ctx.send("⚠️ Invalid difficulty. Please choose from: `easy`, `medium`, `hard`, or `extreme`.")
            return

        min_freq, max_freq = difficulty_ranges[difficulty]

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
            await ctx.send("❌ No suitable words found for that difficulty. Try a different one.")
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

        await ctx.send(f"🧩 **Siege of Six** begins! Difficulty: **{difficulty.capitalize()}**\nGuess the original 6-letter word from these letters:")

        attempts = 6

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for attempt in range(1, attempts + 1):
            if attempt == 3 and extras[0] in jumbled:
                jumbled.remove(extras[0])
                await ctx.send("💡 Hint: One extra letter removed!")
            elif attempt == 5 and extras[1] in jumbled:
                jumbled.remove(extras[1])
                await ctx.send("💡 Hint: Both extra letters removed!")

            # Shuffle the letters before each attempt
            random.shuffle(jumbled)

            await ctx.send(f"**Attempt {attempt}:** `{' '.join(jumbled)}`")
            await ctx.send("Your guess:")

            try:
                # Wait 20 seconds first
                guess_msg = await client.wait_for('message', timeout=50.0, check=check)
            except asyncio.TimeoutError:
                # Warn user: only 10 seconds left
                await ctx.send("⏳ Warning: Only 10 seconds left to answer!")
                try:
                    # Wait remaining 10 seconds
                    guess_msg = await client.wait_for('message', timeout=10.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send("⌛ You took too long. Game over!")
                    return

            guess = guess_msg.content.strip().lower()

            if guess == original_word:
                await ctx.send("🎉 Correct! You breached the Siege of Six!")
                hint = config[f"{difficulty}_hint"]
                if attempt <= 2:
                    hint = config.get(f"{difficulty}_hint", "No hint available.")
                    try:
                        await ctx.author.send(f"🧠 You beat **{difficulty}** in {attempt} attempts!\nHere's your reward hint:\n> {hint}")
                    except discord.Forbidden:
                        await ctx.send("📪 You beat it fast, but I couldn't DM you the hint! Please check your privacy settings.")
                else:
                    await ctx.send("💡 If you beat the game within two attempts, you can win a secret hint for each difficulty! Try again!")
                return
            else:
                await ctx.send("❌ Incorrect.")

        await ctx.send(f"💀 Game Over! The correct word was: **{original_word}**")
