"""
Cribbage.py - Classes for the Cribbage engine

This module implements base classes for cards, deck, hands, discards, players, notifications, and the game itself

Player is an abstract base class; there are several subclasses implemented for various levels of automated play by
the computer; BeginerPlayer,IntermediatePlayer, and AdvancedPlayer (and a planned ProPlayer down the line).
In the CribbageUX.py file, a subclass is implemented in PyGames for an interactive player

The Game itself is a state machine (although unfortunately not formally implemented that way) that works like so:
* game = Game(player1, player1) is called to create a game between two concrete player classes
* game.play() is called to run the game - this method exits when the game is over
* game.players[0].score and game.players[1].score can be called to see who won

Game play itself it a state machine (unfortunately not implemented in a structured way) that goes through these phases:
1) Shuffles the deck
2) Players cut for deal; lowest cut goes first
3) Deals the hands
4) Asks players to select their discards to the crib (by calling player.select_lay_aways() for each player)
5) Cuts the starter card
6) Orchestrates alternative play between the players to discard to the pegging pile (calling player.select_play()
   for each player), while maintaining score
7) Notifying players of game events (calling player.notify()), such as score changes, cuts for deal or starter cards,
   discards to the pegging pile, etc
"""

from abc import abstractmethod
from enum import IntEnum, Enum, auto
from typing import List, Tuple, Final
from math import comb
from time import time
import random

# A suit
class Suit(IntEnum):
    CLUBS = 0
    DIAMODS = 1
    HEARTS = 2
    SPADES = 3

# A Card
class Card:
    _SUIT_NAMES:Final = ["clubs", "diamonds", "hearts", "spades"]
    _RANK_NAMES:Final = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"]
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
        return Card._RANK_NAMES[self._rank - 1] + " of " + Card._SUIT_NAMES[self._suit]
    
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
            s += str(card) + ", "
        return s.rstrip(", ")

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
"""
Player - a cribbage player
"""
class Player:
    def __init__ (self):
        self.name = ""
        self.reset()

    def reset (self):
        self.hand : Hand = None
        self.score = 0

    @abstractmethod
    def select_lay_aways(self, my_crib : bool) -> Tuple[Card, Card]:
        pass

    @abstractmethod
    def select_play(self, starter : Card, discards : Discards) -> Card:
        pass

    @abstractmethod
    def notify(self, notification) -> None:
        pass

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
        self._whose_deal += 1
        self._whose_deal %= len(self._players)
        self._whose_turn = self._whose_deal + 1
        self._whose_turn %= len(self._players)

    def set_dealer(self, player : Player) -> None:
        for i in range (len(self._players)):
            if self._players[i] == player:
                self._whose_deal = i
                self._whose_turn = (self._whose_deal + 1) % len(self._players)
                return
        raise ValueError("Player not found")

    def next_player (self, player : Player) -> Player:
        for i in range (len(self._players)):
            if self._players[i] == player:
                return self._players[(i + 1) % len(self._players)]
        raise ValueError("Player not found")

    def reset (self) -> None:
        for player in self._players:
            player.reset()

    def __len__ (self):
        return len(self._players)
    
    def __str__(self):
        s = ""
        for player in self._players:
            s += player.name + ", "
        return s.rstrip(", ")

    def __iter__(self):
        return self._players.__iter__()

    def __getitem__(self, key):
        return self._players[key]


# Type of notification; each type carries different data
class NotificationType(Enum):
    NEW_GAME     = auto()   # Start of a new game
    CUT_FOR_DEAL = auto()   # A player cut for deal
    DEAL         = auto()   # The dealer dealt the hands
    STARTER_CARD = auto()   # Starter card selected
    PLAY         = auto()   # A pegging card was played
    GO           = auto()   # Player said "go"
    SCORE_HAND   = auto()   # A hand was scored
    SCORE_CRIB   = auto()   # The crib was scored
    POINTS       = auto()   # Points were scored
    ROUND_OVER   = auto()   # A round has ended
    GAME_OVER    = auto()   # The game has ended

class Notification:
    def __init__(self, type: NotificationType, player : Player, points : int, data : str = None):
        self.type = type
        self.player = player
        self.points = points
        self.data = data

    def __str__(self):
        if self.type == NotificationType.NEW_GAME:
            return "A new game has started between " + self.data
        if self.type == NotificationType.CUT_FOR_DEAL:
            return self.player.name + " cut the " + self.data
        elif self.type == NotificationType.DEAL:
            return "\n" + self.player.name + " dealt the cards and will have the crib"
        elif self.type == NotificationType.STARTER_CARD:
            return self.player.name + " cut the starter card " + self.data
        elif self.type == NotificationType.PLAY:
            return self.player.name + " played the " + self.data
        elif self.type == NotificationType.GO:
            return self.player.name + " said 'go'"
        elif self.type == NotificationType.POINTS:
            return self.player.name + ": " + self.data + " for " + str(self.points) + " (score = " + str(self.player.score) + ")"
        elif self.type == NotificationType.SCORE_HAND:
            return self.player.name + " hand scored " + str(self.points) + " (total score is now " + str(self.player.score) + ")\n" + self.data
        elif self.type == NotificationType.SCORE_CRIB:
            return self.player.name + " crib scored " + str(self.points) + " (total score is now " + str(self.player.score) + ")\n" + self.data
        elif self.type == NotificationType.ROUND_OVER:
            return "\nThe round has ended, it's time to cound the hands and the crib, with starter card " + self.data
        elif self.type == NotificationType.GAME_OVER:
            return "The game has ended, " + self.player.name + " won!\nFinal score: " + self.data
        else:
            return str(self.type) + " - " + self.player.name + ": " + self.data + " (+" + str(self.points) + " points)"

# Game - a nice game of cribbage
class Game:
    def __init__(self, players : List[Players]):
        self.players = Players(players)
        self.starter = None

    # A helper method to notify all players when something happens
    def notify_all(self, notification : Notification) -> None:
        for player in self.players:
            player.notify (notification)

        # Is the game over (someone scored 121)?
    @property
    def game_over(self) -> bool:
        for player in self.players:
            if player.score >= 121:
                return True
        return False

    # Is the round over (either game over or all hands have been played)?
    @property
    def round_over(self):
        if self.game_over:
            return True
        for player in self.players:
            if len(player.hand) > 0:
                return False
        return True

    # Can anyone go? If not, we need to reset the discard pile
    @property
    def can_anyone_go(self) -> bool:
        for player in self.players:
            if len(player.hand) > 0 and player.hand[0].points + self.discards.sum <= 31:
                return True
        return False

    def add_points (self, player : Player, points : int, reason : str):
        player.score += points
        if player.score > 121:
            player.score = 121
        self.notify_all(Notification(NotificationType.POINTS, player, points, reason))

    # Start a new game; that means intros and cut for deal
    def start_game (self) -> None:
        # Reset the players scores for a new game
        self.players.reset()

        # Notify everyone of a new game
        self.notify_all (Notification (NotificationType.NEW_GAME, None, 0, str(self.players) + "\nYou must now cut for deal"))

        # Create a deck and cut for deal
        self.deck = Deck()
        self.deck.shuffle()
        dealer = None
        lowestCutRank = 15
        for player in self.players:
            card = self.deck.cut_a_card()
            while card.rank == lowestCutRank:
                card = self.deck.cut_a_card()
            self.notify_all (Notification (NotificationType.CUT_FOR_DEAL, player, 0, str(card)))
            if card.rank < lowestCutRank:
                lowestCutRank = card.rank
                dealer = player
        self.players.set_dealer(dealer)

    # Start a new round; deal, create crib, cut starter card 
    def start_round (self) -> None:
        # Deal the cards, convert the dealt Cards.hands into Cribbage.Hands and give a hand to each player
        self.deck = Deck()
        self.deck.shuffle()
        for player in self.players:
            player.hand = Hand()
        for i in range (6):
            for player in self.players:
                player.hand.add_card(self.deck.draw())
        for player in self.players:
            player.hand.sort()
        self.notify_all(Notification(NotificationType.DEAL, self.players.dealer, 0, self.players))

        # Create the crib by getting lay_away cards from each player
        crib = Hand()
        for player in self.players:
            for card in player.select_lay_aways (player == self.players.dealer):
                crib.add_card (card)
        self.crib = crib
        self.players.dealer.crib = crib
        assert len(crib) == 4, "Crib doesn't have 4 cards!"
        for player in self.players:
            assert len(player.hand) == 4, "Player " + player.name + " doesn't have 4 unplayed cards"
            assert len(player.hand.played_cards) == 0, "Player " + player.name + " doesn't have 0 played cards"

        # Draw the starter card
        self.starter = self.deck.draw();
        self.notify_all (Notification (NotificationType.STARTER_CARD, self.players.turn, 0, str(self.starter)))
        if self.starter.rank == 11:
            self.add_points(self.players.dealer, 2, "His Heels")

        # Set up the discard pile
        self.discards = Discards()
    
    # Let the current player take their turn
    def take_turn(self) -> None:
        player = self.players.turn

        # If the player has no cards left to play, then skip their turn
        if len(player.hand) == 0:
            return

        # If they can play, let the player play. Keep track of last_to_peg for last card
        if self.discards.sum + player.hand[0].points <= 31:
            num_cards_to_play = len(player.hand)
            discard_sum = self.discards.sum
            card = player.select_play(self.starter, self.discards)
            assert len(player.hand) == num_cards_to_play - 1, "Player didn't play a card!"
            assert discard_sum != self.discards.sum, "Player didn't put their play card on the discard pile!"
            self.last_to_peg = player
            self.notify_all(Notification(NotificationType.PLAY, self.players.turn, 0, str(card)))
            self.score_pegging_points()
            if self.discards.sum == 31:
                self.discards.start_new_pile()
                return
            if self.round_over:
                self.add_points(self.last_to_peg, 1, "Last card")
            return
        
        # Else they have cards, but can't play.
        # Notify with a "go"
        self.notify_all(Notification(NotificationType.GO, player, 0, "Go"))

        # If no one else can go, reset the discard pile and give the last pegger credit for last card
        if not self.can_anyone_go:
            self.add_points(self.last_to_peg, 1, "Go")
            self.discards.start_new_pile()
            while self.players.turn != self.last_to_peg:
                self.players.rotate_turn()
    
    # Score points for pegging after the current player has discarded
    def score_pegging_points(self) -> None:
        player = self.players.turn
        discards = self.discards
        card = discards[len(discards) - 1]
        reason = ""
        points = 0

        if discards.sum == 31:
            reason += "31 for 2\n"
            points += 2

        if discards.sum == 15:
            reason += "Fifteen for 2\n"
            points += 2

        in_a_row = 1           # How many cards in a row of the same rank?
        i = len(discards) - 2
        while i >= 0:
            if discards[i].rank == card.rank:
                in_a_row += 1
            else:
                break
            i -= 1
        if in_a_row > 1:
            points += 2 * comb(in_a_row, 2)
            if in_a_row == 2:
                reason += "Pair for 2\n"
            elif in_a_row == 3:
                reason += "Three of a kind for 6\n"
            elif in_a_row == 4:
                reason += "Four of a kind for 12\n"

        if len(discards) >= 3:
            for i in range (len(discards) - 2):
                check_for_run = []
                for j in range (i, len(discards)):
                    check_for_run.append(discards[j].rank)
                check_for_run.sort()
                is_run = True
                last_card = check_for_run[0]
                for k in range(1, len(check_for_run)):
                    if check_for_run[k] != last_card + 1:
                        is_run = False
                        break
                    last_card = check_for_run[k]
                if is_run:
                    run_size = len(check_for_run)
                    reason += "Run of " + str(run_size)
                    points += run_size
                    break
        
        if points > 0:
            self.add_points(player, points, reason)
    
    def score_hands(self) -> None:
        self.notify_all(Notification(NotificationType.ROUND_OVER, None, 0, str(self.starter)))
        starter = self.starter
        player = self.players.dealer
        for i in range (len(self.players)):
            if not self.game_over:
                player = self.players.next_player(player)
                cards = player.hand.played_cards
                cards.sort()
                score, reason = Game.get_hand_value(cards, starter)
                player.score += score
                self.notify_all(Notification(NotificationType.SCORE_HAND, player, score, reason))

        if not self.game_over:
            assert player == self.players.dealer, "Player should be dealer when scoring the crib"
            self.crib._cards.sort()
            score, reason = Game.get_hand_value(self.crib._cards, starter, is_crib = True)
            player.score += score
            self.notify_all(Notification(NotificationType.SCORE_CRIB, player, score, reason))

    # Get the value of a hand (4 cards + starter card)
    # Returns a tuple of score, text describing the score components
    def get_hand_value(cards : List[Card], starter : Card, is_crib : bool = False) -> Tuple[int, str]:
        score = 0       # Computed score
        reason = ""     # Computed reason for the score (e.g, fifteen 4, knobs for 1, etc)

        # Knobs
        for card in cards:
            if card.rank == 11 and card.suit == starter.suit:
                score += 1
                reason += "Knobs for 1\n"
        
        # Flush
        is_flush = True
        first_card = cards[0]
        for card in cards:
            if card.suit != first_card.suit:
                is_flush = False
                break
        if is_crib and cards[0].suit != starter.suit:
            is_flush = False
        if is_flush:
            flush_points = 5 if cards[0].suit == starter.suit else 4
            score += flush_points
            reason += "A flush for " + str (score) + "\n"

        # For pairs, runs and 15s, we don't care about the suit, so convert cards to just an array of int values
        # For pairs and runs, we need the rank
        # For 15s, we need the point values
        tmp = cards
        cards = [starter.rank]
        for card in tmp:
            cards.append(card.rank)
        cards.sort()

        # Pairs
        num_pairs = Game.get_pair_count(cards)
        if num_pairs > 0:
            pair_points = 2*num_pairs
            score += pair_points
            if num_pairs == 1:
                reason += "A pair for "
            elif num_pairs == 2:
                reason += "Two pair for "
            elif num_pairs == 3:
                reason += "Three of a kind for "
            elif num_pairs == 4:
                reason += "A pair and three of a kind for "
            elif num_pairs == 6:
                reason += "Four of a kind for "
            else:
                assert False, "It's not possible to score " + str(num_pairs) + " pairs"
            reason += str (pair_points) + "\n"

        # Runs
        run_len, multiplier = Game.get_run_count (cards)
        if run_len > 0:
            score += run_len * multiplier
            if multiplier == 1:
                reason += "A run of "
            else:
                reason += str(multiplier) + " runs of "
            reason += str(run_len) + " for " + str (run_len * multiplier) + "\n"

        # 15s
        num_15s = Game.get_counts (15, cards)
        if num_15s > 0:
            score += num_15s*2
            if num_15s == 1:
                reason += "Fifteen for 2\n"
            else:
                reason += str(num_15s) + " fifteens for " + str (num_15s*2) + "\n"

        return score, reason

    # Get the number of pair points in a sorted hand
    def get_pair_count (cards : List[int]) -> int:
        num_pairs = 0
        for i in range (len(cards) - 1):
            j = i + 1
            while j < len(cards):
                if cards[i] == cards[j]:
                    num_pairs += 1
                    j += 1
                else:
                    break
        return num_pairs

    # Get the number of run points in a sorted hand
    def get_run_count (cards : List[int]) -> Tuple[int, int]: 
        # Check for runs starting at card i in a sorted list
        i = 0
        while i < len(cards):
            run_len = 1
            multiplier = 1          # Can be 1, 2, 3, or 4 - depending on pairings in the list
            paired_card = 0         # First paired card detected (used to compute multiplier)

            first_card = cards[i]
            last_card = first_card
            j = i + 1
            while j < len(cards):
                if cards[j] > last_card + 1:    # No run starting at index 1, so break
                    break
                elif cards[j] == last_card + 1: # Might be a run, need to check the next card
                    last_card = cards[j]
                    run_len += 1
                else:                           # Pairs used to calculate multiplier
                    assert cards[j] == last_card, "The cards are supposed to be sorted"
                    if paired_card == 0:        # One pair means multiplier = 2
                        multiplier = 2
                        paired_card = last_card
                    elif paired_card == last_card: # Three of a kind means multiplier = 3
                        multiplier = 3
                    else:
                        multiplier = 4          # Two separate pairs means multiplier = 4
                j += 1
            
            if run_len >= 3:
                return run_len, multiplier
            i = j
        return 0, 0

    # Get the number of ways to make "count" points out of the sorted list "cards"
    def get_counts (count : int, cards : List[int]) -> int:
        num_ways = 0
        for i in range(len(cards)):
            card = cards[i] if cards[i] < 10 else 10
            if card > count:
                return num_ways
            if card == count:
                num_ways += 1
                continue
            if i == len(cards) - 1:
                continue
            cards_after = []
            for j in range (i+1, len(cards)):
                cards_after.append(cards[j])
            num_ways += Game.get_counts (count - card, cards_after)
        return num_ways
    
    # Calculate the pegging points that would be scored placing a given card on the discard pile
    def calculate_pegging_points (card_rank : int, discards : Discards) -> int:
        points = 0

        card_points = card_rank if card_rank < 10 else 10

        if discards.sum + card_points == 31:
            points += 2

        if discards.sum + card_points == 15:
            points += 2

        in_a_row = 1           # Check for pairs (# cards in a row of the same rank)
        i = len(discards) - 1
        while i >= 0:
            if discards[i].rank == card_rank:
                in_a_row += 1
            else:
                break
            i -= 1
        if in_a_row > 1:
            points += 2 * comb(in_a_row, 2)

        if len(discards) >= 2:
            for i in range (len(discards) - 1):
                check_for_run = [card_rank]
                for j in range (i, len(discards)):
                    check_for_run.append(discards[j].rank)
                check_for_run.sort()
                is_run = True
                last_card = check_for_run[0]
                for k in range(1, len(check_for_run)):
                    if check_for_run[k] != last_card + 1:
                        is_run = False
                        break
                    last_card = check_for_run[k]
                if is_run:
                    points += len(check_for_run)

        return points

    # The main loop to play a game
    def play (self):
        self.start_game()                   # Intros and cut for deal

        while not self.game_over:           # Deal new rounds until the game is over
            self.start_round()              # Deal, discard to crib, draw starter card, mark person to left of dealer for first turn

            while not self.round_over:      # Take turns until the round is over
                self.take_turn()            # Pegging by player whose turn it is
                self.players.rotate_turn()  # Rotate turns for round

            self.score_hands()              # Count the hands and the crib
            self.players.rotate_dealer()    # Rotate dealer after each round

        winner = None
        final_score = ""
        for player in self.players:
            if player.score >= 121:
                winner = player
                player.score = 121
            final_score += player.name + " " + str(player.score) + "\t\t"
        self.notify_all (Notification (NotificationType.GAME_OVER, winner, 0, final_score))


"""
BeginerPlayer - automated computer opponent that makes simple-minded plays

Always discards it's highest cards to the crib
Always plays it's lowest card while pegging
"""
class BeginerPlayer(Player):
    def __init__(self):
        super().__init__()
        self.name = "Beginer"

    def select_lay_aways(self, my_crib : bool) -> Tuple[Card, Card]:
        return self.hand.play_card(str(self.hand[5]), True), self.hand.play_card(str(self.hand[4]), True)

    def select_play(self, starter, discards) -> Card:
        hand = self.hand
        card = hand.play_card(str(hand[0]))
        discards.add_card(card)
        return card

    def notify(self, notification : Notification) -> None:
        pass

"""
IntermediatePlayer - automated computer opponent that considers immediate points only

Discards to the crib keeping the cards with the highest net points (card points +/- discard points)
Plays the pegging card that will score the highest. If a tie, play the highest allowed card
"""
class IntermediatePlayer(Player):
    def __init__(self):
        super().__init__()
        self.name = "Intermediate"

    # Compute the expected value of a given hand of cards (without knowing the starter card)
    def expected_hand_value (hand : Hand) -> int:
        points = 0

        # knobs
        for card in hand:
            if card.rank == 11:
                points += .235  # 23.5% chance the starter card is the same suit

        # Flush points
        if len(hand) == 4 and hand[0].suit == hand[1].suit == hand[2].suit == hand[3].suit:
            points += 4.18   # 4 points for the flush, plus 18% chance the starter card is the same suit

        # For 15s, pairs, runs - first convert to simpler list of ranks
        cards = []
        for card in hand:
            cards.append(card.rank)

        # 15s
        points += 2 * Game.get_counts (15, cards)

        # pairs
        points += 2 * Game.get_pair_count(cards)

        # runs
        run_len, multiplier = Game.get_run_count (cards)
        points += run_len * multiplier

        return points

    # Select discards resulting in the highest net points (card points +/- discard points)
    def find_lay_aways(hand : Hand, my_crib : bool) -> Tuple[Card, Card]:
        max_points = 0
        card1 = None
        card2 = None
        crib = Hand()
        points = 0

        # Find the discards that produces the highest score (hand +- crib) without regard to starter draw
        for i in range(len(hand) - 1):
            for j in range (i + 1, len(hand)):
                cardj = hand.pop(j)
                cardi = hand.pop(i)
                crib.add_card(cardi)
                crib.add_card(cardj)
                hand_value = IntermediatePlayer.expected_hand_value (hand)
                crib_value = IntermediatePlayer.expected_hand_value (crib)
                h = str(hand)
                c = str(crib)
                if my_crib:
                    points = hand_value + crib_value
                else:
                    points = hand_value - crib_value
                if points > max_points:
                    card1 = cardi
                    card2 = cardj
                    max_points = points
                hand.push(i, cardi)
                hand.push(j, cardj)
                crib.pop(0)
                crib.pop(0)

        # If all possible discards result in 0 expected value, discard highest cards (improves pegging)
        if card1 is None or card2 is None:
            card1 = hand[5]
            card2 = hand[4]

        return card1, card2

    # Select discards resulting in the highest net points (card points +/- discard points)
    def select_lay_aways(self, my_crib : bool) -> Tuple[Card, Card]:
        card1, card2 = IntermediatePlayer.find_lay_aways (self.hand, my_crib)
        return self.hand.play_card(str(card1), True), self.hand.play_card(str(card2), True)

    # Do the pegging play that gives the highest score. If a tie, play the highest allowed card
    def select_play(self, starter : Card, discards : Discards) -> Card:
        hand = self.hand
        points_per_card = [-1]*len(hand)
        max_points = 0
        for i in range(len(hand) - 1, -1, -1):
            if discards.sum + hand[i].points > 31:
                points_per_card[i] = -1
                continue
            points_per_card[i] = Game.calculate_pegging_points(hand[i].rank, discards)
            if points_per_card[i] > max_points:
                max_points = points_per_card[i]

        for i in range(len(hand) - 1, -1, -1):
            if points_per_card[i] == max_points:
                card = hand.play_card(str(hand[i]))
                discards.add_card(card)
                return card
        assert False, "Couldn't select a card to play"

    def notify(self, notification : Notification) -> None:
        pass

"""
AdvancedPlayer - automated computer opponent that considers probability of starter card and opponent pegging response

Discards to the crib consider the weighted probability of possible starter card draws, discarding the two cards
that result in highest net points (hand points +/- crib points) based on probability distribution

Pegging is done based on highest value of computer pegging points - expected player counter-pegging points,
where expected value assumes (naively) that player cards are random among unseen cards
"""
from bisect import bisect_left
class AdvancedPlayer(Player):
    def __init__(self):
        super().__init__()
        self.name = "Advanced"

    # Compute the expected value of splitting a deal into hand and crib cards
    # The algo uses a weighted probability of the starter card draw (but doesn't consider oppont crib cards)
    def expected_value (hand : Hand, crib : Hand, my_crib : bool) -> int:
        points = 0
        crib_points = 0
    
        # First compute knobs/flush values, which depend on the card suits. To do that we need variables that
        # let us compute probability that starter card is of a given suit
        num_cards = 52
        num_suits = {Suit.CLUBS : 13, Suit.DIAMODS : 13, Suit.HEARTS : 13, Suit.SPADES : 13}
        for card in hand:
            num_cards -= 1
            num_suits[card.suit] -= 1
        for card in hand:
            num_cards -= 1
            num_suits[card.suit] -= 1

        # Flush points
        if hand[0].suit == hand[1].suit == hand[2].suit == hand[3].suit:
            points += 4                                         # Flush
            points += (13 - num_suits[hand[0].suit])/num_cards  # Plus probability 5-card flush
        if crib[0].suit == crib[1].suit:
            n = 13 - num_suits[crib[0].suit]
            crib_points += n/num_cards * (n-1)/(num_cards-1) + (n-2)/(num_cards-2)        

        # Knobs points
        for card in hand:
            if card.rank == 11:
                prob_knobs = num_suits[card.suit]/num_cards
                points += prob_knobs
        for card in crib:
            if card.rank == 11:
                prob_knobs = num_suits[card.suit]/num_cards
                crib_points += prob_knobs

        # Now figure out the weighted avg non-suited value of 15s, pairs and runs depending on starter card draw
        # First let's translate the hand and crib into an array of int's (ranks) to make algo faster
        cards = []
        for card in hand:
            cards.append(card.rank)
        crib_cards = []
        for card in crib:
            crib_cards.append(card.rank)

        # Next, create variables to compute the starter will be of a given rank
        num_ranks = [4]*14
        num_ranks[0] = 0
        for card in hand:
            num_ranks[card.rank] -= 1
        for card in hand:
            num_ranks[card.rank] -= 1

        # Finally, let's compute the weighted points for each possible starter draw
        for starter_rank in range (1, 14):
            prob = num_ranks[starter_rank]/num_cards

            starter_card_ix = bisect_left(cards, starter_rank)
            cards.insert(starter_card_ix, starter_rank)
            points += prob * AdvancedPlayer.non_suited_value(cards)
            cards.pop(starter_card_ix)
            assert len(cards) == 4, "Hand length <> 4"
            assert cards[0] <= cards[1] <= cards[2] <= cards[3], "Cards no longer sorted"

            starter_card_ix = bisect_left(crib_cards, starter_rank)
            crib_cards.insert(starter_card_ix, starter_rank)
            crib_points += prob * AdvancedPlayer.non_suited_value(crib_cards)
            crib_cards.pop(starter_card_ix)
            assert len(crib_cards) == 2, "Crib discard length <> 2"
            assert crib_cards[0] <= crib_cards[1], "Crib cards no longer sorted"

        if my_crib:
            return points + crib_points
        else:
            return points - crib_points

    # non-suited value of a set of cards (cards = order list of ranks)
    def non_suited_value (cards : List[int]) -> int:
        points = 0
    
        # 15s
        points += 2 * Game.get_counts (15, cards)

        # pairs
        points += 2 * Game.get_pair_count(cards)

        # runs
        run_len, multiplier = Game.get_run_count (cards)
        points += run_len * multiplier

        return points

    # Find which cards are the best crib lay-aways (card points +/- discard points)
    def find_lay_aways(hand : Hand, my_crib : bool) -> Tuple[Card, Card]:
        crib = Hand()
        max_points = 0
        card1 = None
        card2 = None

        # Find the discards that produces the highest score (hand +- crib) without regard to starter draw
        for i in range(len(hand) - 1):
            for j in range (i + 1, len(hand)):
                cardj = hand.pop(j)
                cardi = hand.pop(i)
                crib.add_card(cardi)
                crib.add_card(cardj)
                points = AdvancedPlayer.expected_value(hand, crib, my_crib)
                h = str(hand)
                c = str(crib)
                if points >= max_points:
                    card1 = cardi
                    card2 = cardj
                    max_points = points
                hand.push(i, cardi)
                hand.push(j, cardj)
                crib.pop(0)
                crib.pop(0)
        
        return card1, card2

    # Select discards resulting in the highest net points (card points +/- discard points)
    def select_lay_aways(self, my_crib : bool) -> Tuple[Card, Card]:
        card1, card2 = AdvancedPlayer.find_lay_aways(self.hand, my_crib)
        return self.hand.play_card(str(card1), True), self.hand.play_card(str(card2), True)

    # Do the pegging play that gives the highest score. If a tie, play the highest allowed card
    def select_play(self, starter : Card, discards : Discards) -> Card:
        hand = self.hand
        points_per_card = [-1]*len(hand)
        max_points = 0
        for i in range(len(hand) - 1, -1, -1):
            if discards.sum + hand[i].points > 31:
                points_per_card[i] = -1
                continue
            points_per_card[i] = Game.calculate_pegging_points(hand[i].rank, discards)
            if points_per_card[i] > max_points:
                max_points = points_per_card[i]

        for i in range(len(hand) - 1, -1, -1):
            if points_per_card[i] == max_points:
                card = hand.play_card(str(hand[i]))
                discards.add_card(card)
                return card
        assert False, "Couldn't select a card to play"

    def notify(self, notification : Notification) -> None:
        pass

# Create an AI player object by level
def get_player(level : int) -> Player:
    if level < 0:
        return None
    elif level == 0:
        return BeginerPlayer()
    elif level == 1:
        return IntermediatePlayer()
    else:
        return IntermediatePlayer()

# A utility method to let two AIs battle each other
def play_match(player0 : Player, player1 : Player, num_games : int) -> None:
    print ("A match of " + str(num_games) + " between " + player0.name + " and " + player1.name)
    player0_wins = 0
    player1_wins = 0
    start_time = time()
    while num_games > player0_wins + player1_wins:
        game = Game([player0, player1])
        game.play()
        wins = 1
        if game.players[0].score <= 90 or game.players[0].score <= 90:
            wins += 1
        if game.players[0].score >= 121:
            player0_wins += wins
        else:
            player1_wins += wins

    total_time = (time() - start_time)
    print ("Final score: " + player0.name + " " + str(player0_wins) + "\t\t" + player1.name + " " + str(player1_wins))
    print ("The match took " + str(total_time) + " seconds (" + str(total_time/num_games) + " seconds/game)")

# Here's how to see the effectiveness of one AI against another
#play_match (CribbageEngine.AdvancedPlayer(), CribbageEngine.BeginerPlayer(), 50)
