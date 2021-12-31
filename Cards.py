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

    @property
    def points(self) -> int:
        return self._rank if self._rank < 10 else 10

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
        self._played_cards = []

    def add_card(self, card : Card) -> None:
        return self._cards.append(card)

    def find_card(self, card_or_card_name) -> Card:
        for i in range(len(self._cards)):
            if str(self._cards[i]) == str(card_or_card_name):
                return self._cards[i]
        return None

    def play_card(self, card_or_card_name, to_crib : bool = False) -> Card:
        for i in range(len(self._cards)):
            if str(self._cards[i]) == str(card_or_card_name):
                card = self._cards.pop(i)
                if not to_crib:
                    self._played_cards.append(card)
                return card
        return None

    def push (self, index : int, card : Card) -> None:
        self._cards.insert (index, card)
    
    def pop (self, index : int) -> Card:
        return self._cards.pop(index)

    def sort(self) -> None:
        self._cards.sort()

    def reset(self) -> None:
        assert len(self._cards) == 0, "Reseting hand only happens at end of round when hand is empty"
        self._cards = self._played_cards
        self._played_cards = []
        self._cards.sort()

    def __getitem__(self, key) -> Card:
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

    @property
    def played_cards (self):
        return self._played_cards

"""
Discards - the cribbage discard pile(s)
"""
class Discards:
    def __init__(self):
        self._hand = Hand()
        self.sum = 0

    # Add a card to the discard pile
    def add_card (self, card : Card) -> None:
        points = card.points
        if points + self.sum > 31:
            raise ValueError ("Can't exceed 31 points on the discard pile")
        self._hand.add_card(card)
        self.sum += points

    # Start a new pile by discarding all the cards on the current pile
    def start_new_pile (self) -> None:
        while len(self._hand) > 0:
            self._hand.play_card(str(self._hand[0]))
        self.sum = 0

    def __len__(self):
        return len(self._hand)

    def __getitem__(self, key) -> Card:
        return self._hand[key]

    def __str__(self):
        s = "Current discard pile (" + str(self.sum) + "): " + str(self._hand)
        if len(self.older_discards) > 0:
            s += "\t\tOlder discards: "
            for card in self.older_discards:
                s += str(card) + " "
        return s.rstrip()

    @property
    def older_discards(self):
        return self._hand.played_cards
