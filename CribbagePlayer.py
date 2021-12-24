"""
Player - abstract base class for a cribbage player
"""
import getpass
from typing import Tuple
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
        return self.hand.lay_away(str(self.hand[4]), str(self.hand[5]))

    def select_play(self, starter, discards) -> Card:
        hand = self.hand
        card = hand.play(str(hand[0]))
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

    def select_lay_aways(self):
        hand = self.hand
        print()
        print ("Your hand: " + str(hand))
        while True:
            cards = input ("What (comma-separated) cards will you discard? ").split(",")
            if len(cards) != 2:
                print ("You need to type in exactly one comma")
                continue
            cards = hand.lay_away(cards[0].strip(), cards[1].strip())
            if cards is not None:
                return cards
            print ("Please select two unique cards that are in your hand")

    def select_play(self, starter, discards):
        hand = self.hand
        print()
        print ("Starter card: " + str(starter))
        print (str(discards))
        print ("Your hand: " + str(hand))
        while True:
            card = input ("What card will you discard? ").strip()
            card = hand.play(card)
            if card is None:
                print ("Please enter a valid discard")
                continue
            adjusted_rank = card.rank if card.rank < 10 else 10
            if adjusted_rank + discards.sum > 31:
                print ("Invalid discard; the discard pile must be < 31")
                hand.unplayed_cards.add_card(card)
                hand.uplayed_cards.sort()
                continue
            discards.add_card(card)
            return card 

    def notify(self, notification : Cribbage.Notification):
        if notification.type == Cribbage.NotificationType.CUT_FOR_DEAL and notification.player == self:
            input ("Type anything to cut for deal: ")
            print ("You cut the " + str(notification.data))
        elif notification.type == Cribbage.NotificationType.STARTER_CARD and notification.player == self:
            input ("Type anything to cut for the starter card: ")
            print ("You cut the " + str(notification.data))
        else:
            print (str(notification).replace(self.name, "You", 1))

while True:
    # Create a new game, which includes initial cut to see who goes first
    game = Cribbage.Game([ComputerPlayer(), ConsolePlayer()])
    game.play()
    print ()
    if input ("Type e to exit, anything else to play a new game: ") == "e":
        break