"""
Cards.py - based classes for card games
"""

from enum import IntEnum
from typing import Final
import random

# A suit
class Suit(IntEnum):
    CLUBS = 0
    DIAMODS = 1
    HEARTS = 2
    SPADES = 3

# A Card
class Card:
    _suit_short_names:Final = ["c", "d", "h", "s"]
    _rank_short_names:Final = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    sortRankFirst = True   # Alternatively sort suit first
    
    def __init__ (self, suit : Suit, rank : int):
        self._suit = suit
        self._rank = rank
        if rank < 1 or rank > 13:
            raise ValueError("Invalid rank - must be between 1 and 13")

    def __lt__ (self, other):
        if Card.sortRankFirst:
            return self.rank < other.rank or (self.rank == other.rank and self.suit < other.suit)
        else:
            return self.suit < other.suit or (self.suit == other.suit and self.rank < other.rank)

    @property
    def suit(self) -> Suit:
        return self._suit

    @property
    def rank(self) -> int:
        return self._rank

    def __str__(self):
        return Card._rank_short_names[self._rank - 1] + Card._suit_short_names[self._suit]
    
# A Deck of 52 cards
class Deck:
    def __init__ (self):
        self._cards = []
        for suit in [Suit.CLUBS, Suit.DIAMODS, Suit.HEARTS, Suit.SPADES]:
            for rank in range (1, 14):
                self._cards.append (Card(suit, rank))
    
    def shuffle(self) -> None:
        random.shuffle(self._cards)

    def draw(self) -> Card:
        return self._cards.pop(0)

    def cut_a_card(self) -> Card:
        return self._cards[random.randint(0, len(self._cards)) - 1]
    
    @property
    def __len__(self) -> int:
        return len(self._cards)

"""
Hand - a hand of cards (subset of the deck)
"""
class Hand:
    def __init__ (self):
        self._cards = []

    def add_card(self, card : Card) -> None:
        return self._cards.append(card)

    def find_card(self, card_name : str) -> bool:
        for i in range(len(self._cards)):
            if str(self._cards[i]) == card_name:
                return True
        return False

    def remove_card(self, card_name : str) -> Card:
        if not self.find_card(card_name):
            return None
        for i in range(len(self._cards)):
            if str(self._cards[i]) == card_name:
                return self._cards.pop(i)
        assert False, "Can't find card to remove even though we checked it was there"

    def sort(self) -> None:
        self._cards.sort()

    def __getitem__(self, key):
        return self._cards[key]
    
    def __iter__(self):
        return self._cards.__iter__()

    def __len__(self):
        return len(self._cards)

    def __str__(self):
        s = ""
        for card in self._cards:
            s += str(card) + " "
        return s.rstrip()

"""
Player - a player
"""
class Player:
    def __init__ (self):
        self.name = ""
        self.hand = None
        self.score = 0
"""
Players - an ordered collection of Player objects

Includes method to set/rotate dealers, and set/rotate whose turn it is to play within a deal
The first turn after the deal is the player right after the dealer
"""
class Players:
    def __init__ (self, players : list[Player]):
        if len(players) < 2:
            raise ValueError ("players list must have at least 2 elements")
        self._players = players
        self.set_dealer(players[0])

    @property
    def dealer(self) -> Player:
        return self._players[self._whose_deal]

    @property
    def turn(self) -> Player:
        return self._players[self._whose_turn]

    def rotate_turn(self) -> None:
        self._whose_turn += 1
        self._whose_turn %= len(self._players)
    
    def rotate_dealer(self) -> None:
        next_dealer = self._players[(self._whose_turn + 1) % len(self._players)]
        self.set_dealer (next_dealer)

    def set_dealer(self, player : Player) -> None:
        for i in range (len(self._players)):
            if self._players[i] == player:
                self._whose_deal = i
                self._whose_turn = (self._whose_deal + 1) % len(self._players)
                return
        raise ValueError("Player not found")

    def __len__ (self):
        return len(self._players)
    
    def __str__(self):
        s = ""
        for player in self._players:
            s += player.name + ", "
        return s.rstrip(", ")

    def __iter__(self):
        return self._players.__iter__()

def deal (deck, num_hands : int, num_cards : int) -> list[Hand]:
    hands = []
    for i in range (num_hands):
        hands.append(Hand())
    for i in range (num_cards):
        for hand_number in range (num_hands):
            hands[hand_number].add_card(deck.draw())
    return hands
