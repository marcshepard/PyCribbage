"""
Cribbage.py - Classes for the Cribbage engine
"""

from abc import abstractmethod
from enum import Enum, auto
from typing import List, Tuple, get_origin
import Cards

def card_points (card):
    return card.rank if card.rank < 9 else 10

"""
Hand - a cribbage hand
"""
class Hand:
    def __init__ (self, cards : Cards.Hand):
        assert len(cards) == 6, "cards must be a list of 6 Cards" 
        self.unplayed_cards = cards
        self.unplayed_cards.sort()
        self.played_cards = Cards.Hand()

    # discard two cards for the crib
    def lay_away (self, card1 : str, card2 : str) -> Tuple:
        assert len(self.unplayed_cards) == 6, "lay_away can only be called once"
        hand = self.unplayed_cards
        if card1 == card2 or not hand.find_card(card1) or not hand.find_card(card2):
            return None
        return hand.remove_card(card1), hand.remove_card(card2)

    # After lay_away, you can play a card for pegging
    def play(self, card : str) -> Cards.Card:
        assert len(self.unplayed_cards) + len(self.played_cards) == 4, "You must lay_away cards to the crib before you can play your hand"
        if not self.unplayed_cards.find_card(card):
            return None
        card = self.unplayed_cards.remove_card(card)
        self.played_cards.add_card(card)
        return card

    def __iter__(self):
        return self.unplayed_cards.__iter__()

    def __getitem__(self, key):
        return self.unplayed_cards[key]

    def __len__(self):
        return len(self.unplayed_cards)

    # Friendly version of the hand
    def __str__(self):
        return str(self.unplayed_cards)

"""
Discards - the cribbage discard pile(s)
"""
class Discards:
    def __init__(self):
        self.current_pile = Cards.Hand()
        self.older_discards = Cards.Hand()
        self.sum = 0

    # Add a card to the discard pile
    def add_card (self, card : Cards.Card) -> None:
        points = card_points(card)
        if points + self.sum > 31:
            raise ValueError ("Can't exceed 31 points on the discard pile")
        self.current_pile.add_card(card)
        self.sum += points

    # Start a new pile by moving cards on teh current pile to older discards
    def start_new_pile (self) -> None:
        self.sum = 0
        while len(self.current_pile) > 0:
            card = self.current_pile.remove_card(str(self.current_pile[0]))
            self.older_discards.add_card(card)

    def __str__(self):
        s = "Current discard pile: " + str(self.current_pile)
        if len(self.older_discards) > 0:
            s += "\t\tOlder discards: " + str(self.older_discards)
        return s

"""
Player - abstract base class for a cribbage player
"""
class Player(Cards.Player):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def select_lay_aways(self) -> Tuple:
        pass

    @abstractmethod
    def select_play(self, starter : Cards.Card, discards : Discards) -> Cards.Card:
        pass

    @abstractmethod
    def notify(self, notification) -> None:
        pass

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
    def __init__(self, type: NotificationType, player : Cards.Player, points : int, data : str = None):
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
            return "\n" + self.player.name + " dealt the cards"
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
    def __init__(self, players : List[Cards.Players]):
        self.players = Cards.Players(players)

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
            if len(player.hand) > 0 and card_points(player.hand[0]) + self.discards.sum <= 31:
                return True
        return False

    # Start a new game; that means intros and cut for deal
    def start_game (self):
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
    def start_round (self):
        # Deal the cards, convert the dealt Cards.hands into Cribbage.Hands and give a hand to each player
        self.deck = Cards.Deck()
        self.deck.shuffle()
        hands = Cards.deal(self.deck, len(self.players), 6)
        i = 0
        for player in self.players:
            player.hand = Hand(hands[i])
            i += 1
        self.notify_all(Notification(NotificationType.DEAL, self.players.dealer, 0))

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
        self.discards = Discards()
    
    # Let the current player take their turn
    def take_turn(self):
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
            if self.discards.sum == 31:
                self.notify_all(Notification(NotificationType.POINTS, player, 2, "31"))
                self.discards.start_new_pile()
            return
        
        # Else they have cards, but can't play.
        # Notify with a "go"
        self.notify_all(Notification(NotificationType.GO, player, 0, "Go"))

        # If no one else can go, reset the discard pile and give the last pegger credit for last card
        if not self.can_anyone_go:
            self.notify_all(Notification(NotificationType.POINTS, self.last_to_peg, 1, "Last card"))
            self.discards.start_new_pile()
    
    def count_hands(self):
        pass

    # The main loop to play a game
    def play (self):
        self.start_game()                   # Intros and cut for deal

        while not self.game_over:           # Deal new rounds until the game is over
            self.start_round()              # Deal, discard to crib, draw starter card, mark person to left of dealer for first turn

            while not self.round_over:      # Take turns until the round is over
                self.take_turn()            # Pegging by player whose turn it is
                self.players.rotate_turn()  # Rotate turns for round

            self.count_hands()              # Count the hands and the crib
            self.players.rotate_dealer()    # Rotate dealer after each round

