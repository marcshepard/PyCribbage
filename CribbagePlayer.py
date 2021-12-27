"""
Player - abstract base class for a cribbage player
"""
import getpass
from typing import List, Tuple
from Cards import Card
import Cribbage

"""
ComputerPlayer - the automated computer opponent
"""
class ComputerPlayer(Cribbage.Player):
    def __init__(self):
        super().__init__()
        self.name = "Computer"

    def select_lay_aways(self) -> Tuple:
        return self.hand.play_card(str(self.hand[5]), True), self.hand.play_card(str(self.hand[4]), True)

    def select_play(self, starter, discards) -> Card:
        hand = self.hand
        card = hand.play_card(str(hand[0]))
        discards.add_card(card)
        return card

    def notify(self, notification : Cribbage.Notification):
        pass

"""
ConsolePlayer - command line interface for the logged in user
"""
class ConsolePlayer(Cribbage.Player):
    def __init__(self):
        super().__init__()
        self.name = getpass.getuser()
        self.points = 0
        self.opponent_points = 0

    def select_lay_aways(self):
        hand = self.hand
        print()
        print ("Your hand: " + str(hand))
        while True:
            cards = input ("What (comma-separated) cards will you discard? ").replace(" ", "").split(",")
            if len(cards) != 2:
                print ("You need to type in exactly one comma")
                continue
            if cards[0] == cards[1]:
                print ("Cards must be unique")
                continue
            cards_found = True
            for card in cards:
                if not hand.find_card(card):
                    print ("Card " + str(card) + " is not one of your cards")
                    cards_found = False
            if not cards_found:
                continue

            selected = []
            for card in cards:
                selected.append(hand.play_card(card, True))
            return selected

    def select_play(self, starter, discards):
        hand = self.hand
        print()
        print ("Score: You " + str(self.points) + "\t\tOpponent " + str(self.opponent_points))
        print ("Starter card: " + str(starter))
        print (str(discards))
        print ("Your hand: " + str(hand))
        while True:
            card = input ("What card will you discard? ").strip()
            found = hand.find_card(card)
            if found is None:
                print ("Please enter a valid discard")
                continue
            if found.points + discards.sum > 31:
                print ("Invalid discard; the discard pile total must be <= 31")
                continue
            card = hand.play_card(card)
            discards.add_card(card)
            return card 

    def notify(self, notification : Cribbage.Notification):
        if notification.type == Cribbage.NotificationType.PLAY and notification.player != self:
            print()
    
        if notification.type == Cribbage.NotificationType.CUT_FOR_DEAL and notification.player == self:
            input ("Type anything to cut for deal: ")
            print ("You cut the " + str(notification.data))
        elif notification.type == Cribbage.NotificationType.STARTER_CARD and notification.player == self:
            input ("Type anything to cut for the starter card: ")
            print ("You cut the " + str(notification.data))
        else:
            print (str(notification).replace(self.name, "You", 1))

        if notification.type == Cribbage.NotificationType.POINTS:
            if notification.player == self:
                self.points += notification.points
            else:
                self.opponent_points += notification.points
            if self.show_scores:
                print ("Score: You " + str(self.points) + "\t\tOpponent " + str(self.opponent_points))
        elif notification.type == Cribbage.NotificationType.NEW_GAME:
            self.points = 0
            self.opponent_points = 0
            self.show_scores = True
        elif notification.type == Cribbage.NotificationType.GAME_OVER:
            print ("The game has ended")
            if self.points > self.opponent_points:
                print ("You won!")
            else:
                print ("You lost")
            print ("Final score: You " + str(self.points) + "\t\tOpponent " + str(self.opponent_points))
        elif notification.type == Cribbage.NotificationType.ROUND_OVER:
            self.show_scores = False

while True:
    # Create a new game, which includes initial cut to see who goes first
    game = Cribbage.Game([ComputerPlayer(), ConsolePlayer()])
    game.play()
    print ()
    if input ("Type e to exit, anything else to play a new game: ") == "e":
        break