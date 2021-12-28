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
        points += 2 * Cribbage.Game.get_counts (15, cards)

        # pairs
        points += 2 * Cribbage.Game.get_pair_count(cards)

        # runs
        run_len, multiplier = Cribbage.Game.get_run_count (cards)
        points += run_len * multiplier

        return points

    # Select discards resulting in the highest net points (card points +/- discard points)
    def select_lay_aways(self, my_crib : bool) -> Tuple[Card, Card]:
        max_points = 0
        card1 = None
        card2 = None
        crib = Hand()
        hand = self.hand
        expected_hand_value = 0
        expected_crib_value = 0
        points = 0

        # Find the discards that produces the highest score (hand +- crib) without regard to starter draw
        for i in range(len(hand) - 1):
            for j in range (i + 1, len(hand)):
                cardj = hand.pop(j)
                cardi = hand.pop(i)
                crib.add_card(cardi)
                crib.add_card(cardj)
                hand_value = StandardComputerPlayer.expected_hand_value (hand)
                crib_value = StandardComputerPlayer.expected_hand_value (crib)
                h = str(hand)
                c = str(crib)
                if my_crib:
                    points = hand_value + crib_value
                else:
                    points = hand_value - crib_value
                if points > max_points:
                    card1 = cardi
                    card2 = cardj
                    expected_crib_value = crib_value
                    expected_hand_value = hand_value
                    max_points = points
                hand.push(i, cardi)
                hand.push(j, cardj)
                crib.pop(0)
                crib.pop(0)

        # If all possible discards result in 0 expected value, discard highest cards (improves pegging)
        if card1 is None or card2 is None:
            card1 = hand[5]
            card2 = hand[4]

        #print ("MediumComputerPlayer discarding " + str(card1) + " and " + str(card2) + " from hand " + str(hand) + \
        #    " to " + ("my crib" if my_crib else "opponents crib"))
        #print ("Expected value = " + str(max_points) + ": " + str(expected_hand_value) + "(hand), " + str(expected_crib_value) + "(crib)")

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
player0_wins = 0
player1_wins = 0
player0_points = 0
player1_points = 0
num_games = 100
games_played = 0
print ("A match to " + str(num_games) + " between " + player0.name + " and " + str (player1.name))
while player0_wins + player1_wins < num_games:
    # Play a game
    game = Cribbage.Game([player0, player1])
    game.play()
    games_played += 1

    # Print the winner and score
    if player0.score > player1.score:
        assert player0.score == 121, "A player won with a score of " + player0.score
        player0_wins += 1
        if player1.score <= 90:
            player0_wins += 1
        #print (player0.name + " won " + str(player0.score) + " to " + str(player1.score))
    else:
        assert player1.score == 121, "A player won with a score of " + player1.score
        player1_wins += 1
        if player0.score <= 90:
            player1_wins += 1
        #print (player1.name + " won " + str(player1.score) + " to " + str(player0.score))
    player0_points += player0.score
    player1_points += player1.score
    #print ("Score: " + player0.name + " " + str(player0_wins) + "\t\t" + player1.name + " " + str(player1_wins) + "\n")

winner = player0.name if player0_wins > player1_wins else player1.name
print (winner + " won the match")
print ("Final score: " + player0.name + " " + str(player0_wins) + "\t\t" + player1.name + " " + str(player1_wins))
print ("Avg points/game: " + player0.name + " " + str(player0_points//games_played) + "\t\t" + player1.name + " " + str(player1_points//games_played))
