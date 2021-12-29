"""
Cribbage.py - Classes for the Cribbage engine
"""

from abc import abstractmethod
from enum import Enum, auto
from typing import List, Tuple, get_origin
import Cards
from math import comb

"""
Player - a cribbage player
"""
class Player:
    def __init__ (self):
        self.name = ""
        self.reset()

    def reset (self):
        self.hand : Cards.Hand = None
        self.starter : Cards.Card = None
        self.score = 0

    @abstractmethod
    def select_lay_aways(self, my_crib : bool) -> Tuple[Cards.Card, Cards.Card]:
        pass

    @abstractmethod
    def select_play(self, starter : Cards.Card, discards : Cards.Discards) -> Cards.Card:
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
    PLAY         = auto()   # A pegging play was made
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
            return self.player.name + self.data
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
        self.deck = Cards.Deck()
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
        self.deck = Cards.Deck()
        self.deck.shuffle()
        for player in self.players:
            player.hand = Cards.Hand()
        for i in range (6):
            for player in self.players:
                player.hand.add_card(self.deck.draw())
        for player in self.players:
            player.hand.sort()
        self.notify_all(Notification(NotificationType.DEAL, self.players.dealer, 0, self.players))

        # Create the crib by getting lay_away cards from each player
        crib = Cards.Hand()
        for player in self.players:
            for card in player.select_lay_aways (player == self.players.dealer):
                crib.add_card (card)
        self.crib = crib
        assert len(crib) == 4, "Crib doesn't have 4 cards!"
        for player in self.players:
            assert len(player.hand) == 4, "Player " + player.name + " doesn't have 4 unplayed cards"
            assert len(player.hand.played_cards) == 0, "Player " + player.name + " doesn't have 0 played cards"

        # Draw the starter card
        self.starter = self.deck.draw();
        self.notify_all (Notification (NotificationType.STARTER_CARD, self.players.turn, 0, str(self.starter)))
        if self.starter.rank == 11:
            self.add_points(self.players.dealer, 2, "His Heels")
        for player in self.players:
            player.starter = self.starter

        # Set up the discard pile
        self.discards = Cards.Discards()
    
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
            self.notify_all(Notification(NotificationType.PLAY, self.players.turn, 0, \
                " played the " + str(card)))
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
            self.add_points(self.last_to_peg, 1, "Last card")
            self.discards.start_new_pile()
            while self.players.turn != self.last_to_peg:
                self.players.rotate_turn()
    
    # Score points for pegging after the current player has discarded
    def score_pegging_points(self) -> None:
        player = self.players.turn
        discards = self.discards
        card = discards[len(discards) - 1]

        if discards.sum == 31:
            self.add_points(player, 2, "31")

        if discards.sum == 15:
            self.add_points(player, 2, "Fifteen")

        in_a_row = 1           # How many cards in a row of the same rank?
        i = len(discards) - 2
        while i >= 0:
            if discards[i].rank == card.rank:
                in_a_row += 1
            else:
                break
            i -= 1
        if in_a_row > 1:
            points = 2 * comb(in_a_row, 2)
            msg = ""
            if in_a_row == 2:
                msg = "Pair"
            elif in_a_row == 3:
                msg = "Three of a kind"
            elif in_a_row == 4:
                msg = "Four of a kind"
            self.add_points(player, points, msg)

        if len(discards) < 3:
            return

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
                self.add_points (player, run_size, "Run of " + str(run_size))
                break
    
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
                hand_info = "Hand(plus starter) = "
                for card in cards:
                    hand_info += str(card) + " "
                hand_info += "(" + str(starter) + ")\n"
                reason = hand_info + reason
                self.notify_all(Notification(NotificationType.SCORE_HAND, player, score, reason))

        if not self.game_over:
            assert player == self.players.dealer, "Player should be dealer when scoring the crib"
            self.crib._cards.sort()
            score, reason = Game.get_hand_value(self.crib._cards, starter, is_crib = True)
            player.score += score
            hand_info = "Hand(plus starter) = "
            for card in self.crib:
                hand_info += str(card) + " "
            hand_info += "(" + str(starter) + ")\n"
            reason = hand_info + reason
            self.notify_all(Notification(NotificationType.SCORE_CRIB, player, score, reason))

    # Get the value of a hand (4 cards + starter card)
    # Returns a tuple of score, text describing the score components
    def get_hand_value(cards : List[Cards.Card], starter : Cards.Card, is_crib : bool = False) -> Tuple[int, str]:
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
    def calculate_pegging_points (card_rank : int, discards : Cards.Discards) -> int:
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



