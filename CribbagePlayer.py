"""
Player - abstract base class for a cribbage player
"""
import getpass
from typing import List, Tuple
from Cards import Card, Discards, Hand, Suit
import Cribbage

"""
EasyComputerPlayer - the easy automated computer opponent

Always discards it's highest cards to the crib
Always plays it's lowest card while pegging
"""
class EasyComputerPlayer(Cribbage.Player):
    def __init__(self):
        super().__init__()
        self.name = "Easy"

    def select_lay_aways(self, your_crib : bool) -> Tuple[Card, Card]:
        return self.hand.play_card(str(self.hand[5]), True), self.hand.play_card(str(self.hand[4]), True)

    def select_play(self, starter, discards) -> Card:
        hand = self.hand
        card = hand.play_card(str(hand[0]))
        discards.add_card(card)
        return card

    def notify(self, notification : Cribbage.Notification) -> None:
        pass

"""
MediumComputerPlayer - a more typical automated computer opponent

Discards to the crib keeping the cards with the highest net points (card points +/- discard points)
Plays the card that will score the highest. If a tie, play the highest allowed card
"""
class StandardComputerPlayer(Cribbage.Player):
    def __init__(self):
        super().__init__()
        self.name = "Standard"

    def select_lay_aways(self, your_crib : bool) -> Tuple[Card, Card]:
        # TODO - implement algo to keep the cards with the highest net point value
        return self.hand.play_card(str(self.hand[5]), True), self.hand.play_card(str(self.hand[4]), True)

    def select_play(self, starter : Card, discards : Discards) -> Card:
        hand = self.hand
        points_per_card = [-1]*len(hand)
        max_points = 0
        for i in range(len(hand) - 1, -1, -1):
            if discards.sum + hand[i].points > 31:
                points_per_card[i] = -1
                continue
            points_per_card[i] = Cribbage.Game.calculate_pegging_points(hand[i].rank, discards)
            if points_per_card[i] > max_points:
                max_points = points_per_card[i]

        for i in range(len(hand) - 1, -1, -1):
            if points_per_card[i] == max_points:
                card = hand.play_card(str(hand[i]))
                discards.add_card(card)
                return card
        assert False, "Couldn't select a card to play"

    def notify(self, notification : Cribbage.Notification) -> None:
        pass

"""
ConsolePlayer - command line interface for the logged in user
"""
class ConsolePlayer(Cribbage.Player):
    def __init__(self):
        super().__init__()
        self.name = getpass.getuser()
        self.opponent_score = 0

    def select_lay_aways(self, your_crib : bool):
        hand = self.hand
        print()
        print ("Your hand: " + str(hand))
        while True:
            question = "What (comma-separated) cards will you discard to your crib?"
            if not your_crib:
                question = "What (comma-separated) cards will you discard to your opponents crib?"
            cards = input (question).replace(" ", "").split(",")
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
        print ("Score: You " + str(self.score) + "\t\tOpponent " + str(self.opponent_score))
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

        if notification.type in [Cribbage.NotificationType.POINTS, Cribbage.NotificationType.SCORE_HAND, Cribbage.NotificationType.SCORE_CRIB]:
            if notification.player != self:
                self.opponent_score += notification.points
        elif notification.type == Cribbage.NotificationType.NEW_GAME:
            self.opponent_score = 0


player0 = EasyComputerPlayer()
player1 = StandardComputerPlayer()
max_games = 10
player0_wins = 0
player1_wins = 0
print ("A match to " + str(max_games) + " between " + player0.name + " and " + str (player1.name))
while True:
    # Play a game
    game = Cribbage.Game([player0, player1])
    game.play()

    # Print the winner and score
    if player0.score > player1.score:
        player0_wins += 1
        print (player0.name + " won " + str(player0.score) + " to " + str(player1.score))
    else:
        player1_wins += 1
        print (player1.name + " won " + str(player1.score) + " to " + str(player0.score))
    print ("Score: " + player0.name + " " + str(player0_wins) + "\t\t" + player1.name + " " + str(player1_wins) + "\n")

    if player0_wins + player1_wins > max_games:
        break

print ("Match over")