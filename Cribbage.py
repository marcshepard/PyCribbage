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
        self.hand : Cards.Hand = None
        self.score = 0

    @abstractmethod
    def select_lay_aways(self) -> Tuple:
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
        next_dealer = self._players[(self._whose_turn + 1) % len(self._players)]
        self.set_dealer (next_dealer)

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

    def __len__ (self):
        return len(self._players)
    
    def __str__(self):
        s = ""
        for player in self._players:
            s += player.name + ", "
        return s.rstrip(", ")

    def __iter__(self):
        return self._players.__iter__()


# Type of notification; each type carries different data
class NotificationType(Enum):
    NEW_GAME     = auto()   # Start of a new game
    CUT_FOR_DEAL = auto()   # A player cut for deal
    FIRST_DEALER = auto()   # Initial dealer selected
    DEAL         = auto()   # The dealer dealt the hands
    STARTER_CARD = auto()   # Starter card selected
    PLAY         = auto()   # A pegging play was made
    GO           = auto()   # Player said "go"
    POINTS       = auto()   # Points were scored
    ROUND_OVER   = auto()   # A round has ended
    GAME_OVER    = auto()   # The game has ended

class Notification:
    def __init__(self, type: NotificationType, player : Player, points : int, data = None):
        self.type = type
        self.player = player
        self.points = points
        self.data = data

    def __str__(self):
        if self.type == NotificationType.NEW_GAME:
            return "A new game has started between " + self.data
        if self.type == NotificationType.CUT_FOR_DEAL:
            return self.player.name + " cut the " + self.data
        if self.type == NotificationType.FIRST_DEALER:
            return self.player.name + " will deal first"
        elif self.type == NotificationType.DEAL:
            s = "\n" + self.player.name + " dealt the cards\nScore: "
            for player in self.data:
                s += player.name + " " + str(player.score) + "\t\t"
            return s
        elif self.type == NotificationType.STARTER_CARD:
            return self.player.name + " cut the starter card " + self.data
        elif self.type == NotificationType.PLAY:
            return self.player.name + " played the " + self.data
        elif self.type == NotificationType.GO:
            return self.player.name + " said 'go'"
        elif self.type == NotificationType.POINTS:
            return self.player.name + ": " + self.data + " (+" + str(self.points) + " points)"
        elif self.type == NotificationType.ROUND_OVER:
            return "The round has ended, it's time to cound the hands and the crib"
        elif self.type == NotificationType.GAME_OVER:
            return "The game has ended, I hope you will play again"
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

    # Start a new game; that means intros and cut for deal
    def start_game (self) -> None:
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
        self.notify_all (Notification (NotificationType.FIRST_DEALER, dealer, 0))
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
            for card in player.select_lay_aways ():
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
            self.notify_all(Notification(NotificationType.POINTS, self.players.dealer, 2, "His Heels"))

        # Set up the discard pile
        self.discards = Cards.Discards()
    
    # Let the current player take their turn
    def take_turn(self) -> None:
        player = self.players.turn

        # If the player has no cards left to play, then skip their turn
        if len(player.hand) == 0:
            return

        # If they can play, let the player play. Keep track of last_to_peg for last card
        if self.discards.sum + player.hand[0].rank <= 31:
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
        
        # Else they have cards, but can't play.
        # Notify with a "go"
        self.notify_all(Notification(NotificationType.GO, player, 0, "Go"))

        # If no one else can go, reset the discard pile and give the last pegger credit for last card
        if not self.can_anyone_go:
            self.notify_all(Notification(NotificationType.POINTS, self.last_to_peg, 1, "Last card"))
            self.last_to_peg.score += 1
            self.discards.start_new_pile()
    
    # Score points for pegging after the current player has discarded
    def score_pegging_points(self) -> None:
        player = self.players.turn
        discards = self.discards
        card = discards[len(discards) - 1]

        if discards.sum == 31:
            self.notify_all(Notification(NotificationType.POINTS, player, 2, "31"))
            player.score += 2

        if discards.sum == 15:
            self.notify_all(Notification(NotificationType.POINTS, player, 2, "15"))
            player.score += 2

        in_a_row = 1           # How many cards in a row of the same rank?
        i = len(discards) - 2
        while i >= 0:
            if discards[i].rank == card.rank:
                in_a_row += 1
            i -= 1
        if in_a_row > 1:
            points = 2 * comb(in_a_row, 2)
            self.notify_all(Notification(NotificationType.POINTS, player, points, str(in_a_row - 1) + " card pair"))
            player.score += points

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
                self.notify_all(Notification(NotificationType.POINTS, player, run_size, "Run of " + str(run_size)))
                player.score += run_size
                break
    
    def score_hands(self) -> None:
        starter = self.starter
        player = self.players.dealer
        for i in range (len(self.players)):
            if not self.game_over:
                player = self.players.next_player(player)
                self.score_hand(player)

        if not self.game_over:
            self.score_crib()

    def score_hand(self, player : Player) -> None:
        starter = self.starter
        hand = player.hand.played_cards

        # Knobs
        for card in hand:
            if card.rank == 11 and card.suit == starter.suit:
                self.notify_all(Notification(NotificationType.POINTS, player, 1, "Knobs"))
                player.score += 1
                if player.score >= 121:
                    return
                break
        
        # Flush
        flush_points = 4
        first_card = hand[0]
        for card in hand:
            if card.suit != first_card.suit:
                flush_points = 0
                break
        if flush_points == 4:
            if starter.suit == card.suit:
                flush_points == 5
            self.notify_all(Notification(NotificationType.POINTS, player, flush_points, "Flush"))
            player.score += flush_points
            if player.score >= 121:
                player.score = 121
                return

        # For pairs and runs, first convert hand + starter to sorted list of card ranks
        tmp = hand
        hand = [starter.rank]
        for card in tmp:
            hand.append(card.rank)
        hand.sort()

        # Pairs
        num_pairs = 0
        for i in range (len(hand) - 1):
            j = i + 1
            while j < len(hand):
                if hand[i] == hand[j]:
                    num_pairs += 1
                    j += 1
                else:
                    break
        if num_pairs > 0:
            pair_points = 2*num_pairs
            self.notify_all(Notification(NotificationType.POINTS, player, pair_points, str(num_pairs) + " pair"))
            player.score += pair_points
            if player.score >= 121:
                player.score = 121
                return

        # Runs
        while len(hand) >= 3:
            first_card = hand[0]
            i = 1
            while i < len(hand):
                if hand[i] != hand[0] + i:
                    break
                i += 1
            if i >= 3:
                run_points = i
                self.notify_all(Notification(NotificationType.POINTS, player, run_points, "Run of " + str(run_points)))
                player.score += run_points
                if player.score >= 121:
                    player.score = 121
                    return
                break
            else:
                hand.pop(0)


    def score_crib(self) -> None:
        player = self.players.turn
        pass

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


