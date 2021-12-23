"""
Cribbage.py - Classes for the Cribbage engine
"""

from abc import abstractmethod
from enum import IntEnum
import Cards

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
Discards - the cribbage discard pile

Properties:
* current_pile - the current pile of discards, which has total value <= 31
* older_discards - discards that happened before the last time all players had to "go"

Methods:
add_card; add a card to the discard pile
start_new_pile; called after all players do a "go"
__str__; show the pile
"""
class Discards:
    def __init__(self):
        self._current_pile = []
        self._older_discards = []
        self._sum = 0

    @property
    def current_pile(self):
        return tuple(self._current_pile)

    @property
    def sum (self):
        return self._sum;

    @property
    def older_discards(self):
        return tuple(self._older_discards)

    def add_card (self, card):
        if type(card) is not Cards.Card:
            raise ValueError ("card must be of type Card")
        if card.rank + self.sum > 31:
            raise ValueError ("Can't exceed 31 points on the discard pile")
        self._current_pile.append(card)
        self._sum += card.rank

    def start_new_pile (self):
        self._sum = 0
        self._older_discards += self._current_pile
        self._current_pile = []

    def __str__(self):
        s = "Current discard pile: "
        for card in self._current_pile:
            s += str(card) + " "
        if len(self._older_discards) > 0:
            s += "\t\tOlder discards: "
            for card in self._older_discards:
                s += str(card) + " "
        return s.rstrip()

import CribbagePlayer

class Game:
    def __init__(self, players):
        self._players = players
        self._scores = [0, 0]

    # Generate an event for a player, increasing that players score by points
    def _event (self, player_ix, points, message):
        for i in range (0, 3):
            self._players[i].get_event(player_ix == i, points, message)

    # Create a new game, printe welcome message, cut for who goes first
    def _cut_for_deal (self):
        self._deck = Cards.Deck()
        self._deck.shuffle()
        draw_cards = [self._deck.draw(), self._deck.draw()]
        while draw_cards[0].rank == draw_cards[1].rank:
            draw_cards = [self._deck.draw(), self._deck.draw()]
        if draw_cards[0].rank < draw_cards[1].rank:
            self._whose_deal = 0
            self._whose_turn = 1
        else:
            self._whose_deal = 1
            self._whose_turn = 0
        for i in range(0, 2):
            self._players[i].new_game_welcome(self._players[1-i].name)
            self._players[i].cut_for_deal(draw_cards[i], draw_cards[1-i])

    # Deal cards, create crib, draw starter card
    def _deal(self):
        deck = Cards.Deck()
        deck.shuffle()
        cards = [[],[]]
        for i in range(0, 6):
            cards[0].append(deck.draw())
            cards[1].append(deck.draw())
        self._deck = deck
        self._hands = [Hand(cards[0]), Hand(cards[1])]
        self._starter_card = deck.draw()
        self._discard = Discards()

    # Create the crib
    def _create_crib(self):
        crib = []
        for i in range(0, 2):
            card1_ix, card2_ix = self._players[i].select_lay_aways(self._hands[i])
            card1, card2 = self._hands[i].lay_away(card1_ix, card2_ix)
            crib.append(card1)
            crib.append(card2)
        self._crib = crib

    # Draw starter card
    def _draw_starter_card(self):
        self._starter_card = self._deck.draw()
        for i in range(0, 2):
            self._players[i].draw_starter(self._starter_card, self._whose_turn == i)
        if self._starter_card.rank == 11:
            self._event(self._whose_deal, 2, "His Heels")

    # Is the game over (someone scored 121)?
    @property
    def game_over(self):
        return self._scores[0] >= 121 or self._scores[1] >= 121

    # Is the round over (all hands have been played)?
    @property
    def round_over(self):
        return len(self._hands[0].unplayed_cards) == 0 and len(self._hands[1].unplayed_cards) == 0

    # Can player_ix play?
    def _can_play(self, player_ix):
        if len(self._hands[player_ix].unplayed_cards) > 0 and self._hands[player_ix].unplayed_cards[0].rank + self._discard.sum() <= 31:
            return True
        return False

    # Can anyone play?
    def _can_anyone_play(self):
        for i in range (0, 2):
            if self._can_play(i):
                return True
        return False

    # Let the whose_turn player make a pegging play
    def _pegging_play (self):
        player = self._players[self._whose_turn]
        card_ix = player.select_play(self._hands[self._whose_turn], self._starter_card, self._discard)

        # If they can play, see if it scores points and recard they were the last to play
        if card_ix != -1:
            card = self._hands[self._whose_turn].play(card_ix)
            self._discard.add_card (card)
            score = 0   # TODO - figure out the score properly
            self._event (self._whose_turn, score, "Played the " + str(card))
            self._last_played = self._whose_turn
            return

        # If they can't play ("go"), but were the last to play, then they get a point for last card and we start a new discard pile
        assert not self._can_play(self._whose_turn), "Player said go, but had a play"
        if self._last_played == self._whose_turn:
            self._event (self._whose_turn, 1, "Last card")
            self._discard.start_new_pile()
            return

        # Else it's just a normal go, and someone else will play
        self._event (self._whose_turn, 0, "Go")

    # Score all the hands and the crib at the end of each round
    def _score_hands (self):
        pass

    # The main game loop
    def play(self):
        self._cut_for_deal()
        while not self.game_over:
            self._deal()
            self._create_crib()
            self._draw_starter_card()
            while not self.game_over and not self.round_over:
                self._pegging_play()
                self._whose_turn = 1 - self._whose_turn
            if not self.game_over:
                self._score_hands()
            self._whose_deal = 1 - self._whose_deal
    
while True:
    # Create a new game, which includes initial cut to see who goes first
    game = Game([CribbagePlayer.ComputerPlayer(), CribbagePlayer.ConsolePlayer()])
    game.play()
    print ()
    if input ("Type e to exit, anything else to play a new game: ") == "e":
        break
