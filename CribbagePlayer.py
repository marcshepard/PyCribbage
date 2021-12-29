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

    def select_lay_aways(self, my_crib : bool) -> Tuple[Card, Card]:
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

    def select_lay_aways(self, my_crib : bool):
        hand = self.hand
        print()
        print ("Your hand: " + str(hand))
        while True:
            question = "What (comma-separated) cards will you discard to your crib?"
            if not my_crib:
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

def play_match(player0: Cribbage.Player, player1 : Cribbage.Player, num_games : int) -> None:
    player0_wins = 0
    player1_wins = 0
    player0_points = 0
    player1_points = 0
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

import pygame
import threading
from queue import Queue
from typing import Final

SCREEN_WIDTH : Final = 800
SCREEN_HEIGHT : Final = 1000
CARD_HEIGHT : Final = SCREEN_HEIGHT//5
GAP : Final = 50
SCORE_Y : Final = GAP//2
DEALER_Y : Final = CARD_HEIGHT
CRIB_Y : Final = CARD_HEIGHT * 2 + GAP
PLAYER_Y : Final = CARD_HEIGHT * 3 + GAP * 2
WHITE : Final = (255, 255, 255)
BLACK : Final = (0, 0, 0)

"""
PyGameCard - a card to display on the screen
"""
class PyGameCard(Card):
    rank_names = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"]
    suit_names = ["clubs", "diamonds", "hearts", "spades"]
    cards = {}

    def get_card(card : Card):
        card_str = "face_down"
        if card is not None:
            card_str = str(card)
        if card_str in PyGameCard.cards.keys():
            return PyGameCard.cards[card_str]
        pgCard = PyGameCard(card)
        PyGameCard.cards[card_str] = pgCard
        return pgCard

    def __init__(self, card: Card):
        self._card = card
        img_name = "images\\back.png"
        if card is not None:
            img_name = "images\\" + PyGameCard.rank_names[card.rank - 1] + "_of_" + PyGameCard.suit_names[card.suit] + ".png"
        img = pygame.image.load(img_name)
        new_width = (CARD_HEIGHT * img.get_width()) //img.get_height()
        self.img = pygame.transform.scale(img, (new_width, CARD_HEIGHT))
        self.x = 0
        self.y = 0

    def contains_point (self, point : Tuple[int, int]) -> bool:
        if self.rect.collidepoint(point):
            return True
        return False

    def toggle_selected (self):
        new_width = new_height = 0
        if self.get_selected():
            new_height = CARD_HEIGHT
            new_width = (CARD_HEIGHT * self.img.get_width()) // self.img.get_height()
        else:
            new_height = self.img.get_height() * 1.2 // 1
            new_width = self.img.get_width() * 1.2 // 1
        
        self.img = pygame.transform.scale(self.img, (new_width, new_height))

    def get_selected (self):
        return self.img.get_height() != CARD_HEIGHT
    
    def blit (self, screen):
        rect = self.img.get_rect()
        rect.x = self.x
        rect.y = self.y
        self.rect = rect
        screen.blit(self.img, rect)

    @property
    def centery(self):
        return self.y + CARD_HEIGHT//2
"""
PyGamePlayer - PyGame GUID for the logged in user
"""
class PyGamePlayer(Cribbage.Player):
    def __init__(self):
        super().__init__()
        self.name = getpass.getuser()
        self.opponent_score = 0
        self.pgCards = []

    def display_crib(self, my_crib : bool):
        pgCard = PyGameCard(None)
        pgCard.x = 50
        pgCard.y = CRIB_Y
        pgCard.blit(self.screen)

        msg = "Your crib" if my_crib else "Opponents crib"
        font = pygame.font.Font(None, 32)
        text = font.render(msg + str(self.score), True, BLACK, WHITE)
        textRect = text.get_rect()
        textRect.centery = pgCard.centery
        textRect.x = SCREEN_WIDTH//2
        self.screen.blit(text, textRect)

    def display_scores(self):
        font = pygame.font.Font(None, 32)
        
        text = font.render("Your score: " + str(self.score), True, BLACK, WHITE)
        textRect = text.get_rect()
        textRect.y = SCORE_Y
        textRect.centerx = SCREEN_WIDTH//2
        self.screen.blit(text, textRect)

        text = font.render("Opponent score: " + str(self.opponent_score), True, BLACK, WHITE)
        textRect = text.get_rect()
        textRect.y = SCORE_Y + text.get_height() + GAP//2
        textRect.centerx = SCREEN_WIDTH//2
        self.screen.blit(text, textRect)

    # Display the cards to the screen, notify selected cards via q
    def display_cards(self, hand : Hand, q : Queue):
        x_inc = SCREEN_WIDTH//6

        # Show dealers cards (face down)
        for i in range(len(hand)):
            pgCard = PyGameCard(None)
            pgCard.x = x_inc * i
            pgCard.y = DEALER_Y
            pgCard.blit(self.screen)

        # Show players cards
        self.pgCards = []
        for i in range(len(hand)):
            pgCard = PyGameCard(hand[i])
            pgCard.x = x_inc * i
            pgCard.y = PLAYER_Y
            pgCard.blit(self.screen)
            self.pgCards.append(pgCard)

    # The main UX event loop
    def ux_event_loop(self):
        pygame.init()

        display = pygame.display
        self.screen = display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        display.set_caption("Cribbage")

        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.USEREVENT:
                if event.subtype=="layaway":
                    self.screen.fill(BLACK)
                    self.display_scores ()
                    self.display_cards (event.hand, event.q)
                    self.display_crib(event.my_crib)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pt = pygame.mouse.get_pos()
                for pgCard in self.pgCards:
                    if pgCard.contains_point(pt):
                        pgCard.toggle_selected()
                        pgCard.blit(self.screen)
                        break
       
            pygame.display.flip()

    def select_lay_aways(self, my_crib : bool):
        q = Queue()
        event = pygame.event.Event(pygame.USEREVENT, subtype="layaway", hand=self.hand, my_crib=my_crib, q=q)
        pygame.event.post (event)
        data = q.get()

        print ("Got some data: " + str(data))
        """
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
        """

    def select_play(self, starter, discards):
        hand = self.hand
        #print()
        #print ("Score: You " + str(self.score) + "\t\tOpponent " + str(self.opponent_score))
        #print ("Starter card: " + str(starter))
        #print (str(discards))
        #print ("Your hand: " + str(hand))
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
            pass
        if notification.type == Cribbage.NotificationType.CUT_FOR_DEAL and notification.player == self:
            pass
        elif notification.type == Cribbage.NotificationType.STARTER_CARD and notification.player == self:
            pass
        else:
            pass

        if notification.type in [Cribbage.NotificationType.POINTS, Cribbage.NotificationType.SCORE_HAND, Cribbage.NotificationType.SCORE_CRIB]:
            if notification.player != self:
                self.opponent_score += notification.points
        elif notification.type == Cribbage.NotificationType.NEW_GAME:
            self.opponent_score = 0

# Options for match play
# Let the AI's battle it out:
# play_match (EasyComputerPlayer(), StandardComputerPlayer(), 100)
# Best of 3 between a console-UX player and the easy AI
# play_match (ConsolePlayer(), EasyComputerPlayer(), 3)

# Single game between a PyGame player and the standard AI
#play_match (PyGamePlayer(), StandardComputerPlayer(), 1)

pygame_player = PyGamePlayer()
game_engine_thread = threading.Thread(target=play_match, args = [PyGamePlayer(), StandardComputerPlayer(), 1])
game_engine_thread.setDaemon(True) 
game_engine_thread.start()
pygame_player.ux_event_loop()

