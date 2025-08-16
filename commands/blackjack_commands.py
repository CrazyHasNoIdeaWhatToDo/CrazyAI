from .bank import load_bank_data, save_bank_data, get_player_diamonds, update_player_diamonds
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

# --- Card Definitions and Game Logic ---

# Define card values for Blackjack
CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11  # Ace is initially 11, handled later for 1
}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['♠️', '♥️', '♦️', '♣️']  # Using emojis for suits for better display

class BlackjackGame:
    """Manages the state and logic of a single Blackjack game."""
    def __init__(self):
        self.deck = self._create_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        self.result = ""  # Stores the final outcome of the game

    def _create_deck(self):
        """Creates and shuffles a standard 52-card deck."""
        deck = [(rank, suit) for rank in RANKS for suit in SUITS]
        random.shuffle(deck)
        return deck

    def _deal_card(self, hand):
        """Deals a single card from the deck to the given hand."""
        if not self.deck:
            self.deck = self._create_deck()
        hand.append(self.deck.pop())

    def calculate_hand_value(self, hand):
        """Calculates the value of a hand, correctly handling Aces."""
        value = 0
        num_aces = 0
        for rank, _ in hand:
            value += CARD_VALUES[rank]
            if rank == 'A':
                num_aces += 1
        while value > 21 and num_aces > 0:
            value -= 10
            num_aces -= 1
        return value

    def start_game(self):
        """Initializes the game by dealing two cards to player and dealer."""
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        self.result = ""
        self._deal_card(self.player_hand)
        self._deal_card(self.dealer_hand)
        self._deal_card(self.player_hand)
        self._deal_card(self.dealer_hand)

    def player_hit(self):
        """Adds a card to the player's hand and checks for bust."""
        self._deal_card(self.player_hand)
        if self.calculate_hand_value(self.player_hand) > 21:
            self.game_over = True
            self.result = "Player busts! Dealer wins."

    def dealer_play(self):
        """Dealer hits until their hand is 17 or more, then determines winner."""
        if not self.game_over:
            while self.calculate_hand_value(self.dealer_hand) < 17:
                self._deal_card(self.dealer_hand)
            player_value = self.calculate_hand_value(self.player_hand)
            dealer_value = self.calculate_hand_value(self.dealer_hand)
            if dealer_value > 21:
                self.result = "Dealer busts! Player wins!"
            elif dealer_value > player_value:
                self.result = "Dealer wins!"
            elif player_value > dealer_value:
                self.result = "Player wins!"
            else:
                self.result = "It's a push!"
        self.game_over = True

    def get_hand_display(self, hand, hide_second_dealer_card=False):
        if hide_second_dealer_card and len(hand) == 2:
            return f"{hand[0][0]}{hand[0][1]} and one face down card"
        return " ".join([f"{rank}{suit}" for rank, suit in hand])

    def get_game_state_embed(self, show_dealer_full_hand=False, player_diamonds=None, bet_amount=None):
        embed = discord.Embed(title="♠️♥️♦️♣️ Blackjack! ♣️♦️♥️♠️", color=discord.Color.blue())
        player_cards_display = self.get_hand_display(self.player_hand)
        player_value = self.calculate_hand_value(self.player_hand)
        embed.add_field(name="Your Hand", value=f"{player_cards_display} (Value: {player_value})", inline=False)
        if show_dealer_full_hand:
            dealer_cards_display = self.get_hand_display(self.dealer_hand)
            dealer_value = self.calculate_hand_value(self.dealer_hand)
            embed.add_field(name="Dealer's Hand", value=f"{dealer_cards_display} (Value: {dealer_value})", inline=False)
        else:
            dealer_cards_display = self.get_hand_display(self.dealer_hand, hide_second_dealer_card=True)
            embed.add_field(name="Dealer's Hand", value=dealer_cards_display, inline=False)
        if bet_amount is not None:
            embed.add_field(name="Your Bet", value=f"💎 {bet_amount}", inline=True)
        if self.game_over:
            embed.add_field(name="Game Over!", value=self.result, inline=False)
            if "Player wins" in self.result:
                embed.color = discord.Color.green()
            elif "Dealer wins" in self.result or "Player busts" in self.result:
                embed.color = discord.Color.red()
            else:
                embed.color = discord.Color.gold()
            embed.set_footer(text="Thanks for playing!")
        else:
            embed.set_footer(text="Choose your next move!")
        if player_diamonds is not None:
            embed.add_field(name="Your Diamonds", value=f"💎 {player_diamonds}", inline=True)
        return embed

# --- Discord UI View for Buttons ---

class BlackjackView(discord.ui.View):
    def __init__(self, game: BlackjackGame, original_interaction: discord.Interaction, server_id: str, player_id: str, bet_amount: int):
        super().__init__(timeout=180)
        self.game = game
        self.original_interaction = original_interaction
        self.game_message = None
        self.server_id = server_id
        self.player_id = player_id
        self.bet_amount = bet_amount

    async def on_timeout(self):
        if self.game_message:
            for item in self.children:
                item.disabled = True
            await self.game_message.edit(content="Game timed out! Please start a new game.", view=self)

    async def update_game_message(self, show_dealer_full_hand=False):
        current_diamonds = get_player_diamonds(self.server_id, self.player_id)
        embed = self.game.get_game_state_embed(show_dealer_full_hand, player_diamonds=current_diamonds, bet_amount=self.bet_amount)
        if self.game_message:
            await self.game_message.edit(embed=embed, view=self if not self.game.game_over else None)
        else:
            await self.original_interaction.followup.send(embed=embed, view=self if not self.game.game_over else None)

    async def finalize_game_outcome(self):
        if "Player wins" in self.game.result:
            update_player_diamonds(self.server_id, self.player_id, self.bet_amount * 2)
        elif "It's a push" in self.game.result:
            update_player_diamonds(self.server_id, self.player_id, self.bet_amount)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="➕")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        await interaction.response.defer()
        self.game.player_hit()
        if self.game.game_over:
            await self.finalize_game_outcome()
            for item in self.children:
                item.disabled = True
            await self.update_game_message(show_dealer_full_hand=True)
            self.stop()
        else:
            await self.update_game_message()

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red, emoji="🛑")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        await interaction.response.defer()
        self.game.dealer_play()
        await self.finalize_game_outcome()
        for item in self.children:
            item.disabled = True
        await self.update_game_message(show_dealer_full_hand=True)
        self.stop()

# --- Setup Function for the Bot ---

def setup_blackjack_commands(tree: app_commands.CommandTree):
    @tree.command(name="blackjack", description="Start a game of Blackjack!")
    @app_commands.describe(bet="The amount of diamonds you want to bet.")
    async def blackjack(interaction: discord.Interaction, bet: int):
        player_id = str(interaction.user.id)
        server_id = str(interaction.guild.id)
        current_diamonds = get_player_diamonds(server_id, player_id)

        # Bet validations
        if bet <= 0:
            await interaction.response.send_message("You must bet a positive amount of diamonds!", ephemeral=True)
            return
        if bet > 1000:
            await interaction.response.send_message("The maximum bet allowed is 💎 1000.", ephemeral=True)
            return
        if bet > current_diamonds:
            await interaction.response.send_message(f"You don't have enough diamonds! You have 💎 {current_diamonds}.", ephemeral=True)
            return

        update_player_diamonds(server_id, player_id, -bet)
        initial_display_diamonds = get_player_diamonds(server_id, player_id)
        game = BlackjackGame()
        game.start_game()

        player_value = game.calculate_hand_value(game.player_hand)
        dealer_value = game.calculate_hand_value(game.dealer_hand)

        if player_value == 21 and dealer_value == 21:
            game.result = "Both have Blackjack! It's a push."
            game.game_over = True
            update_player_diamonds(server_id, player_id, bet)
            embed = game.get_game_state_embed(show_dealer_full_hand=True, player_diamonds=get_player_diamonds(server_id, player_id), bet_amount=bet)
            await interaction.response.send_message(embed=embed)
            return
        elif player_value == 21:
            game.result = "Blackjack! Player wins!"
            game.game_over = True
            update_player_diamonds(server_id, player_id, bet * 2)
            embed = game.get_game_state_embed(show_dealer_full_hand=True, player_diamonds=get_player_diamonds(server_id, player_id), bet_amount=bet)
            await interaction.response.send_message(embed=embed)
            return
        elif dealer_value == 21:
            game.result = "Dealer has Blackjack! Dealer wins."
            game.game_over = True
            embed = game.get_game_state_embed(show_dealer_full_hand=True, player_diamonds=get_player_diamonds(server_id, player_id), bet_amount=bet)
            await interaction.response.send_message(embed=embed)
            return

        view = BlackjackView(game, interaction, server_id, player_id, bet)
        embed = game.get_game_state_embed(player_diamonds=initial_display_diamonds, bet_amount=bet)
        await interaction.response.send_message(embed=embed, view=view)
        view.game_message = await interaction.original_response()
