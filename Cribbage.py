"""
Cribbage.py - Classes for Cribbage engine and console interface
"""

import Cards
import math

"""
Hand - a cribbage hand

Properties:
* dealt_cards; the 6 initial cards (passed to the constructor), sorted
* unplayed_cards; populated by lay_away to the 4 cards remaining after crib cards are selected and removed
* played_cards; the play() method removes cards from the unplayed list and adds them to the played list

Methods:
* lay_away; must be called only once, to remove cards for the crib
* play; removes a card from the unplayed list and adds to the played list
* __str__; friendly string - initially the dealt_cards, then becomes unplayed_cards after the lay_away
"""
class Hand:
    def __init__ (self, cards):
        if len(cards) != 6 or not isinstance(cards[0], Cards.Card):
            raise ValueError("cards must be a list of 6 Cards") 
        self._dealt_cards = cards
        self._dealt_cards.sort()
        self._unplayed_cards = []
        self._played_cards = []

    @property
    def dealt_cards(self):
        return tuple(self._dealt_cards)

    @property
    def unplayed_cards(self):
        return tuple(self._unplayed_cards)
    
    @property
    def played_cards(self):
        return tuple(self._played_cards)

    # Must lay away 2 of the dealth cards to start, card1_ix must be smaller than card2_ix
    def lay_away (self, card1_ix, card2_ix):
        if len(self._unplayed_cards) + len(self._played_cards) != 0:
            raise RuntimeError ("lay_away can only be called once")
        if not 0 <= card1_ix < card2_ix <= 5:
            raise ValueError ("card1_ix must be less than card2_ix, and both must be between 0 and 5")
        self._unplayed_cards = self._dealt_cards.copy()
        card2 = self._unplayed_cards.pop(card2_ix)
        card1 = self._unplayed_cards.pop(card1_ix)
        return card1, card2

    # After lay_away, you can play a card for pegging
    def play(self, unplayed_card_ix):
        if len(self._unplayed_cards) + len(self._played_cards) != 4:
            raise RuntimeError ("You must lay_away cards to the crib before you can play your hand")
        card = self._unplayed_cards.pop(unplayed_card_ix)
        self._played_cards.append(card)
        return card

    # Friendly version of the hand
    def __str__(self):
        s = ""
        list = self._dealt_cards if len(self._unplayed_cards) + len(self._played_cards) == 0 else self._unplayed_cards
        for card in list:
            s += str(card) + " "
        return s.rstrip()

"""
Discards - the discard pile for the current hand

Properties:
* current_pile - the current pile of discards, which has total value <= 31
* older_discards - discards that happened before the last time all players had to "go"

Method:
add_card; add a card to the discard pile
start_new_pile; called after all players do a "go"
__str__; show the pile
"""
class Discards:
    def __init__(self):
        self._current_pile = []
        self._older_discards = []
        self.sum = 0

    def __str__(self):
        return _rank_short_names[self._rank - 1] + _suit_short_names[self._suit]

    @property
    def current_pile(self):
        return tuple(self._current_pile)

    @property
    def older_discards(self):
        return tuple(self._older_discards)

    def add_card (self, card):
        if type(card) is not Cards.Card:
            raise ValueError ("card must be of type Card")
        if card.rank + self.sum > 31
            raise ValueError ("Can't exceed 31 points on the discard pile")
        self._current_pile.append(card)

    def start_new_pile (self):
        self.sum = 0
        self._older_discards.append(self._current_pile)
        self._current_pile = []

    def __str__(self):
        s = "Current pile: "
        for card in self._current_pile:
            s += str(card) + " "
        if len(self._older_discards) > 0:
            s += "\nOlder discards: "
            for card in self._older_discards:
                s += str(card) + " "
        return s.rstrip()


"""
Player # Default player is interactive player
* name
* type (Enum)   # Current user, computer
* ix1, ix2 select_lay_aways (Hand hand)
* card_ix select_play(Game game, Hand hand)

Game
* Player[] players
* Hand[] hands
* int[] scores
* Card starter
* Discards discards
* Deck _deck
* int _whose_turn  # Whose turn is it for the current hand?
* int _whose_deal  # Whose deal is it?
* __init__(Player[] players):
    * create new deck, shuffle
    * cut for deal, set whose_deal (-1 from who wins the cut)
* deal():
    * whose_deal += 1 % num_players
    * whose_turn = whose_deal + 1 % num_players
    * Reset players hands, crib, discard piles
    * Create new deck and shuffle it
    * deal hands
    * whose_turn gets to cut the deck
    * select starter card
* create_crib():
    * each player selects 2 cards to transfer to the crib
        * option to get recommended_crib_discard - returns array of (card[], min, max, expected) value of discards, sorted by expected
    * next player cuts deck, starter card drawn, his heals scored
        might generate game_over event
* play():
    * if the person whose turn it is has >= 121, no-op
    * else, the person whose turn it is makes a play; either select a card to discard or say "go" (engine provides allowed options)
        * option to get recommended_play - returns array of (card[], min, max, expected) value of discards, sorted by expected
        * if go and no one else can go, then last_pegger gets a point and create new discard pile, and turn = last_pegger + 1
        * if card is played, update score (any of these might generate game_over event)
            * update player score for n-of-a-kind or runs
            * update player score for 15 or 31
            * update score for last card if this was the final card in all hands. If so, then score_hands()
            * update player score for last card if no one else can play
* score_hand(player_number):
    * score the players hand - default just auto-score; ideally config option to allow for manual score and also for muggins
    * if player_number = -1, score the whose_deal player crib
* score_hands():
    * for each player, starting at whose_deal + 1, score_hand(player_number)
    * score_hand (-1) to score the crib


Session:
* __init__:
    * Get user sign-in info
    * create Player for signed-in user
* Player
* GameResults[] history
* GameResultsStatistics statistics
* run():
    * If no signed-in user, provide option to sign-in
    * If signed in, provide options to:
        * Play new game (against the computer, one level)
        * View history
        * View statistics
        * Edit profile
        * quit

Main code:
* Create Session
* Session.run
"""