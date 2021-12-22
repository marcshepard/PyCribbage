"""
Cards.py - based classes for card games
"""

from enum import IntEnum
from typing import Final
import random

_suit_short_names:Final = ["c", "d", "h", "s"]
_rank_short_names:Final = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Suit class
class Suit(IntEnum):
    CLUBS = 0
    DIAMODS = 1
    HEARTS = 2
    SPADES = 3

# Card class - a card has a Suit and a rank (1-13), and implements a friendly __str__ method 
class Card:
    def __init__ (self, suit, rank):
        self._suit = suit
        self._rank = rank
        if rank < 1 or rank > 13:
            raise ValueError("Invalid rank - must be between 1 and 13")

    def __lt__ (self, other):
        return self.rank < other.rank

    @property
    def suit(self):
        return self._suit

    @property
    def rank(self):
        return self._rank

    def __str__(self):
        return _rank_short_names[self._rank - 1] + _suit_short_names[self._suit]
    

class Deck:
    def __init__ (self):
        self._cards = []
        for suit in [Suit.CLUBS, Suit.DIAMODS, Suit.HEARTS, Suit.SPADES]:
            for rank in range (1, 14):
                self._cards.append (Card(suit, rank))
    
    def shuffle(self):
        random.shuffle(self._cards)

    def draw(self):
        return self._cards.pop(0)

    def cut(self):
        """""" # No op for now (not really needed)

