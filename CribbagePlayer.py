"""
Player - abstract base class for a cribbage player
"""
from enum import Enum, auto
import getpass
from typing import List, Tuple
import time

from pygame import display
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
PgCard - a card to display on the screen
"""
class PgCard(Card):
    _RANK_NAMES : Final = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"]
    _SUIT_NAMES : Final = ["clubs", "diamonds", "hearts", "spades"]

    def __init__(self, card: Card):
        if card is not None:
            super().__init__(card.suit, card.rank)
        self._card = card
        img_name = "images\\back.png"
        if card is not None:
            img_name = "images\\" + PgCard._RANK_NAMES[card.rank - 1] + "_of_" + PgCard._SUIT_NAMES[card.suit] + ".png"
        img = pygame.image.load(img_name)
        new_width = (CARD_HEIGHT * img.get_width()) //img.get_height()
        self.img = pygame.transform.scale(img, (new_width, CARD_HEIGHT))
        self.x = 0
        self.y = 0
        self.selected = False

    def contains_point (self, point : Tuple[int, int]) -> bool:
        if self.rect.collidepoint(point):
            return True
        return False
    
    def blit (self, screen):
        img = self.img
        if self.selected:
            new_height = img.get_height() * 1.2 // 1
            new_width = img.get_width() * 1.2 // 1
            img = pygame.transform.scale(img, (new_width, new_height))

        rect = img.get_rect()
        rect.x = self.x
        rect.y = self.y
        self.rect = rect
        screen.blit(img, rect)

    @property
    def centery(self):
        return self.y + CARD_HEIGHT//2

class PgPlayerState(Enum):
    LAY_AWAY = auto()   # Player needs to discard two cards to the crib
    PLAY     = auto()   # Player needs to play a pegging card
    OTHER    = auto()   # Will eventually change this to things like "cut", "select game", etc

"""
PgPlayer - PyGame GUID for the logged in user
"""
class PgPlayer(Cribbage.Player):
    def __init__(self):
        super().__init__()
        self.name = getpass.getuser()
        self.opponent_score = 0
        self.my_crib = True
        self.num_opp_cards = 6
        self.discards = Discards()
        self.state = PgPlayerState.OTHER
        self.last_scoring_msg = None

    def display_crib(self):
        pygame.draw.rect(self.screen, BLACK, (0, CRIB_Y, SCREEN_WIDTH, CARD_HEIGHT * 1.2))
        
        my_crib = self.my_crib
        pgCard = PgCard(None)
        pgCard.x = 50
        pgCard.y = CRIB_Y
        pgCard.blit(self.screen)
        if self.starter is not None and self.state != PgPlayerState.LAY_AWAY:
            pgCard = PgCard(self.starter)
            pgCard.x = 60
            pgCard.y = CRIB_Y
            pgCard.blit(self.screen)
        
        msg = ""
        if self.state == PgPlayerState.LAY_AWAY:
            if self.num_cards_selected == 2:
                msg = "Click HERE to confirm crib discards"
            else:
                msg = "Select two cards for " + ("your" if my_crib else "the opponents") + " crib"
        elif self.state == PgPlayerState.PLAY:
            if self.num_cards_selected == 1:
                msg = "Click in the crib area to confirm selection"
            else:
                msg = "Select a card to play - pegging count is " + str(self.discards.sum)
        font = pygame.font.Font(None, 32)
        text = font.render(msg, True, WHITE)
        textRect = text.get_rect()
        textRect.centery = pgCard.centery
        textRect.x = SCREEN_WIDTH//3
        if self.state == PgPlayerState.PLAY and len(self.discards) != 0:
            textRect.y = pgCard.y + CARD_HEIGHT + 10
            textRect.centerx = SCREEN_WIDTH//2
        
        self.screen.blit(text, textRect)

        if self.state != PgPlayerState.LAY_AWAY:
            x_inc = 70
            card_num = 0
            for card in self.discards:
                pg_card = PgCard(card)
                pg_card.x = SCREEN_WIDTH//3 + x_inc * card_num
                pg_card.y = CRIB_Y
                pg_card.blit(self.screen)
                card_num += 1
            
            x_inc = 30
            for card in self.discards.older_discards:
                pg_card = PgCard(card)
                pg_card.x = 3*SCREEN_WIDTH//4 + x_inc * card_num
                pg_card.y = CRIB_Y
                pg_card.blit(self.screen)
                card_num += 1

    def confirm_selection(self, pt):
        if self.state == PgPlayerState.LAY_AWAY:
            if self.num_cards_selected == 2 and pt[0] > SCREEN_WIDTH//3 and \
                pt[1] > CRIB_Y and pt[1] < CRIB_Y + CARD_HEIGHT:
                return True
            return False 
        elif self.state == PgPlayerState.PLAY:
            if self.num_cards_selected == 1 and pt[0] > SCREEN_WIDTH//3 and \
                pt[1] > CRIB_Y and pt[1] < CRIB_Y + CARD_HEIGHT:
                return True
            return False 
        else:
            return False

    @property
    def num_cards_selected(self) -> int:
        num_cards_selected = 0
        for card in self.hand:
            if card.selected:
                num_cards_selected += 1
        return num_cards_selected

    def display_scores(self):
        font = pygame.font.Font(None, 32)
        my_crib = self.my_crib

        pygame.draw.rect(self.screen, BLACK, (0, SCORE_Y, SCREEN_WIDTH, CARD_HEIGHT))
        
        text = font.render("Your score: " + str(self.score), True, WHITE)
        textRect = text.get_rect()
        textRect.y = SCORE_Y
        textRect.right = SCREEN_WIDTH//2
        self.screen.blit(text, textRect)

        text = font.render("Opponent score: " + str(self.opponent_score), True, WHITE)
        textRect = text.get_rect()
        textRect.y = SCORE_Y + text.get_height() + GAP//2
        textRect.right = SCREEN_WIDTH//2
        self.screen.blit(text, textRect)

        text = font.render("< crib", True, WHITE)
        textRect = text.get_rect()
        if my_crib:
            textRect.y = SCORE_Y
        else:
            textRect.y = SCORE_Y + text.get_height() + GAP//2
        textRect.x = SCREEN_WIDTH//2 + 50
        self.screen.blit(text, textRect)

        if self.last_scoring_msg is not None:
            text = font.render(self.last_scoring_msg, True, WHITE)
            textRect = text.get_rect()
            textRect.y = SCORE_Y + 2*text.get_height() + GAP
            textRect.centerx = SCREEN_WIDTH//2
            self.screen.blit(text, textRect)

    # Display the cards to the screen
    def display_cards(self):
        x_incr = SCREEN_WIDTH//6 if self.state == PgPlayerState.LAY_AWAY else SCREEN_WIDTH//4
        
        # Show dealers cards (face down) after first clearing out any older displays
        pygame.draw.rect(self.screen, BLACK, (0, DEALER_Y, SCREEN_WIDTH, CARD_HEIGHT * 1.2))
        for i in range(self.num_opp_cards):
            pgCard = PgCard(None)
            pgCard.x = i * x_incr
            pgCard.y = DEALER_Y
            pgCard.blit(self.screen)

        # Show players cards after first clearing out any older displays
        pygame.draw.rect(self.screen, BLACK, (0, PLAYER_Y, SCREEN_WIDTH, CARD_HEIGHT * 1.2))
        x_pos = 0
        for pgCard in self.hand:
            pgCard.x = x_pos
            pgCard.y = PLAYER_Y
            pgCard.blit(self.screen)
            x_pos += x_incr

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
                    self.state = PgPlayerState.LAY_AWAY
                    self.num_opp_cards = 6
                    self.q = event.q
                    pgHand = Hand()
                    for card in self.hand:
                        pgHand.add_card(PgCard(card))
                    self.hand = pgHand
                    #self.screen.fill(BLACK)
                    self.display_scores()
                    self.display_cards()
                    self.display_crib()
                if event.subtype=="play":
                    self.state = PgPlayerState.PLAY
                    self.q = event.q
                    self.display_scores()
                    self.display_cards()
                    self.display_crib()
                if event.subtype=="score":
                    self.display_scores()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pt = pygame.mouse.get_pos()
                if len(self.hand) > 0 and isinstance (self.hand[0], PgCard):
                    for pgCard in self.hand:
                        if pgCard.contains_point(pt):
                            if self.state == PgPlayerState.LAY_AWAY or \
                                    (self.state == PgPlayerState.PLAY and pgCard.points + self.discards.sum <= 31):
                                pgCard.selected = not pgCard.selected
                                self.display_cards()
                                self.display_crib()
                                break
                        if self.confirm_selection (pt):
                            if self.state == PgPlayerState.LAY_AWAY:
                                self.num_opp_cards = 4
                            self.state = PgPlayerState.OTHER
                            self.q.put(None)
       
            pygame.display.flip()

    def select_lay_aways(self, my_crib : bool):
        self.my_crib = my_crib
        q = Queue()
        event = pygame.event.Event(pygame.USEREVENT, subtype="layaway", q=q)
        pygame.event.post (event)
        data = q.get()
        cards = []
        for card in self.hand:
            if card.selected:
                cards.append(card)
        assert len(cards) == 2, "Layaways were confirmed - but there are not 2 selected"
        return self.hand.play_card(cards[0], True), self.hand.play_card(cards[1], True)

    def select_play(self, starter, discards):
        hand = self.hand
        self.discards = discards
        q = Queue()
        event = pygame.event.Event(pygame.USEREVENT, subtype="play", q=q)
        pygame.event.post (event)
        data = q.get()
        selected_card = None
        for card in self.hand:
            if card.selected:
                selected_card = card
        assert selected_card is not None, "No card selected for play"
        card = hand.play_card(selected_card)
        discards.add_card(card)
        return card            

    def notify(self, notification : Cribbage.Notification):
        if notification.type == Cribbage.NotificationType.PLAY and notification.player != self:
            self.num_opp_cards -= 1
            self.last_scoring_msg = "Opponent played the " + notification.data
            time.sleep(1)

        if notification.type == Cribbage.NotificationType.CUT_FOR_DEAL and notification.player == self:
            pass
        elif notification.type == Cribbage.NotificationType.STARTER_CARD and notification.player == self:
            pass
        else:
            pass

        if notification.type in [Cribbage.NotificationType.POINTS, Cribbage.NotificationType.SCORE_HAND, Cribbage.NotificationType.SCORE_CRIB]:
            if notification.player != self:
                self.opponent_score += notification.points
            self.last_scoring_msg = ("You " if notification.player == self else "Opponent") + \
                " scored +" + str(notification.points) + ": " + notification.data
            event = pygame.event.Event(pygame.USEREVENT, subtype="points")
            pygame.event.post (event)
            time.sleep(1)
        elif notification.type == Cribbage.NotificationType.NEW_GAME:
            self.opponent_score = 0

# Options for match play
# Let the AI's battle it out:
# play_match (EasyComputerPlayer(), StandardComputerPlayer(), 100)
# Best of 3 between a console-UX player and the easy AI
# play_match (ConsolePlayer(), EasyComputerPlayer(), 3)

# Single game between a PyGame player and the standard AI
#play_match (pgPlayer(), StandardComputerPlayer(), 1)

pg_player = PgPlayer()
game_engine_thread = threading.Thread(target=play_match, args = [pg_player, StandardComputerPlayer(), 1])
game_engine_thread.setDaemon(True) 
game_engine_thread.start()
pg_player.ux_event_loop()

