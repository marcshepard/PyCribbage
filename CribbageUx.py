import CribbageEngine as Cribbage
import pygame
import threading
from Cards import Card, Hand
from enum import Enum, auto
from typing import Tuple
from pygame.event import Event
from queue import Queue
from typing import Final
from sys import argv
from os import chdir, path, getcwd

SCREEN_WIDTH : Final = 800
SCREEN_HEIGHT : Final = 1000
CARD_HEIGHT : Final = SCREEN_HEIGHT//5
GAP : Final = 50
SCORE_Y : Final = GAP//2
DEALER_Y : Final = CARD_HEIGHT
CRIB_Y : Final = CARD_HEIGHT * 2 + GAP
INSTRUCTIONS_Y : Final = CARD_HEIGHT * 3 + GAP * 2
PLAYER_Y : Final = CARD_HEIGHT * 3 + GAP * 3
WHITE : Final = (255, 255, 255)
BLACK : Final = (0, 0, 0)

"""
PgCard - a card to display on the screen
"""
class PgCard(Card):
    _RANK_NAMES : Final = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"]
    _SUIT_NAMES : Final = ["clubs", "diamonds", "hearts", "spades"]
    _dict = {}

    def __init__(self, card: Card):
        if card is not None:
            super().__init__(card.suit, card.rank)
        self._card = card
        img_name = "images\\back.png"
        if card is not None:
            img_name = "images\\" + PgCard._RANK_NAMES[card.rank - 1] + "_of_" + PgCard._SUIT_NAMES[card.suit] + ".png"
        img = None
        if img_name not in self._dict.keys():
            img = pygame.image.load(img_name)
            self._dict[img_name] = img
        else:
            img = self._dict[img_name]
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
    LAY_AWAY    = auto()    # Player needs to discard two cards to the crib
    PLAY        = auto()    # Player needs to play a pegging card
    SCORE_HAND  = auto()    # Scoring the players hand
    SCORE_OPP_HAND = auto() # Scoring the opponents hand
    SCORE_CRIB  = auto()    # Scoring the crib
    GAME_OVER   = auto()    # Game is over
    OTHER       = auto()    # Will eventually change this to things like "cut", "select game", etc

"""
PgPlayer - PyGame GUID for the logged in user
"""
class PgPlayer(Cribbage.Player):
    def __init__(self):
        super().__init__()
        self.name = "You"
        self.state = PgPlayerState.OTHER
        self.last_scoring_msg = None
        self.made_play = False
        self.event = threading.Event()
        pygame.init()

    # Play a game, or start a new game
    def play(self, level : int = 1):
        self.start_new_game(level)
        self.ux_event_loop()

    # Start another game
    def start_new_game(self, level : int = 1):
        # Reset some state
        super().reset()
        self.state = PgPlayerState.OTHER
        self.last_scoring_msg = None
        self.made_play = False
        
        # Select opponent
        opponent = None
        if level == 0:
            opponent = Cribbage.EasyComputerPlayer()
        else:
            opponent = Cribbage.StandardComputerPlayer()

        # Create a game, and launch as a daemon thread so it exits if the main UI exits
        game = Cribbage.Game([self, opponent])
        self.game = game
        game_engine_thread = threading.Thread(target=game.play)
        game_engine_thread.setDaemon(True)
        game_engine_thread.start()

    @property
    def starter(self):
        return self.game.starter

    @property
    def discards(self):
        return self.game.discards

    @property
    def my_crib(self):
        return self.game.players.dealer == self

    @property
    def my_turn(self):
        return self.game.players.turn == self

    @property
    def num_opp_cards(self):
        return len(self.game.players[1].hand)

    @property
    def opponent_score(self):
        return self.game.players[1].score if self.game.players[1].score < 121 else 121

    def post_event(self, event : Event, delay : int) -> None:
        pygame.event.post (event)
        self.event.wait(delay)
    
    def display_crib(self):
        # Pile and cut card on the left   
        pgCard = PgCard(None)
        pgCard.x = 10
        pgCard.y = CRIB_Y
        pgCard.blit(self.screen)
        if self.starter is not None and self.state != PgPlayerState.LAY_AWAY:
            pgCard = PgCard(self.starter)
            pgCard.x = 20
            pgCard.y = CRIB_Y
            pgCard.blit(self.screen)

        # Discard pile (or crib during crib scoring) on the right
        if self.state == PgPlayerState.PLAY:
            x_inc = 40
            card_num = 0
            for card in self.discards:
                pg_card = PgCard(card)
                pg_card.x = SCREEN_WIDTH//4 + x_inc * card_num
                pg_card.y = CRIB_Y
                pg_card.blit(self.screen)
                card_num += 1        
            
            x_pos = 2*SCREEN_WIDTH//3
            if x_pos < 10 + SCREEN_WIDTH//4 + x_inc * len(self.discards):
                x_pos = 10 + SCREEN_WIDTH//4 + x_inc * len(self.discards)
            x_inc = 20
            for card in self.discards.older_discards:
                pg_card = PgCard(card)
                pg_card.x = x_pos
                pg_card.y = CRIB_Y
                pg_card.blit(self.screen)
                x_pos += x_inc

        elif self.state == PgPlayerState.SCORE_CRIB:
            x_inc = 150
            card_num = 0
            for card in self.crib:
                pg_card = PgCard(card)
                pg_card.x = SCREEN_WIDTH//4 + x_inc * card_num
                pg_card.y = CRIB_Y
                pg_card.blit(self.screen)
                card_num += 1
                
    def display_message(self):          
        # Any message for the user on what to do next below that
        msg = ""
        if self.state == PgPlayerState.LAY_AWAY:
            if self.num_cards_selected == 2:
                msg = "Click anywhere above to confirm crib discards"
            else:
                msg = "Select two cards for " + ("your" if self.my_crib else "the opponents") + " crib"
        elif self.state == PgPlayerState.PLAY and self.my_turn and not self.made_play:
            if self.num_cards_selected == 1:
                msg = "Click anywhere above to confirm selection"
            elif len(self.hand) == 0:
                msg = "Your cards are played - we'll count hands in a moment"
            else:
                msg = "Select a card to play - pegging count is " + str(self.discards.sum)
        elif self.state in [PgPlayerState.SCORE_OPP_HAND, PgPlayerState.SCORE_HAND, PgPlayerState.SCORE_CRIB]:
            msg = ""
            if self.state == PgPlayerState.SCORE_CRIB:
                msg += "Your" if self.my_crib else "Your opponents"
                msg += " crib was scored - click anywhere above to continue"
            elif self.state == PgPlayerState.SCORE_HAND:
                msg += "Your hand was scored - click anywhere above to continue"
            else:
                msg += "Your opponents hand was scored - click anywhere above to continue"
        elif self.state == PgPlayerState.PLAY and len(self.hand) == 0 and self.num_opp_cards == 0:
            msg = "The cards are all played - we'll count hands in a moment"
        elif self.state == PgPlayerState.GAME_OVER:
            msg = "You" if self.score > self.game.players[1].score else "Your opponent"
            msg += " won! Click anywhere above to play again"
        font = pygame.font.Font(None, 32)
        text = font.render(msg, True, WHITE)
        textRect = text.get_rect()
        textRect.y = INSTRUCTIONS_Y
        textRect.centerx = SCREEN_WIDTH//2
        self.screen.blit(text, textRect)

    def confirm_selection(self, pt):
        right_area = pt[1] < INSTRUCTIONS_Y
        right_state = (self.state == PgPlayerState.LAY_AWAY and self.num_cards_selected == 2) or \
            (self.state == PgPlayerState.PLAY and self.num_cards_selected == 1) or \
            (self.state in [PgPlayerState.SCORE_CRIB, PgPlayerState.SCORE_HAND, PgPlayerState.SCORE_OPP_HAND]) or \
            (self.state == PgPlayerState.GAME_OVER)
        if right_area and right_state:
            return True
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

        pygame.draw.rect(self.screen, BLACK, (0, SCORE_Y, SCREEN_WIDTH, CARD_HEIGHT))
        
        if self.score > 121:
            self.score = 121
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
        if self.my_crib:
            textRect.y = SCORE_Y
        else:
            textRect.y = SCORE_Y + text.get_height() + GAP//2
        textRect.x = SCREEN_WIDTH//2 + 50
        self.screen.blit(text, textRect)

        text = font.render("< turn", True, WHITE)
        textRect = text.get_rect()
        if self.my_turn:
            textRect.y = SCORE_Y
        else:
            textRect.y = SCORE_Y + text.get_height() + GAP//2
        textRect.x = SCREEN_WIDTH//2 + 150
        self.screen.blit(text, textRect)

        if self.last_scoring_msg is not None and self.state != PgPlayerState.LAY_AWAY:
            msg = self.last_scoring_msg
            msg = msg.replace("\n",", ")
            msg = msg.rstrip(", ")
            text = font.render(msg, True, WHITE)
            textRect = text.get_rect()
            textRect.y = SCORE_Y + 2*text.get_height() + GAP
            textRect.centerx = SCREEN_WIDTH//2
            self.screen.blit(text, textRect)

    # Display the cards to the screen
    def display_cards(self):
        if self.hand is None or len(self.hand) > 0 and not isinstance (self.hand[0], PgCard):
            return

        x_incr = SCREEN_WIDTH//6 if self.state == PgPlayerState.LAY_AWAY else SCREEN_WIDTH//4
        
        # Show dealers cards
        if self.state == PgPlayerState.SCORE_OPP_HAND:
            for i in range(len(self.opponent_hand)):
                pgCard = PgCard(self.opponent_hand[i])
                pgCard.x = i * x_incr
                pgCard.y = DEALER_Y
                pgCard.blit(self.screen)
        else:
            for i in range(self.num_opp_cards):
                pgCard = PgCard(None)
                pgCard.x = i * x_incr
                pgCard.y = DEALER_Y
                pgCard.blit(self.screen)

        # Show players cards
        if self.state not in [PgPlayerState.SCORE_OPP_HAND, PgPlayerState.SCORE_CRIB]:
            x_pos = 0
            for pgCard in self.hand:
                pgCard.x = x_pos
                pgCard.y = PLAYER_Y
                pgCard.blit(self.screen)
                x_pos += x_incr

    # The main UX event loop
    def ux_event_loop(self):
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
                    self.q = event.q
                    pgHand = Hand()
                    for card in self.hand:
                        pgHand.add_card(PgCard(card))
                    self.hand = pgHand
                elif event.subtype=="select_play":
                    self.state = PgPlayerState.PLAY
                    self.q = event.q
                elif event.subtype in ["points", "play"]:
                    self.last_scoring_msg = event.msg
                elif event.subtype == "score_hand":
                    self.last_scoring_msg = event.msg
                    if event.player == self:
                        self.hand.reset()   # Reset pegging discards so hand can be shown
                        for card in self.hand:
                            card.selected = False
                        self.state = PgPlayerState.SCORE_HAND
                    else:
                        self.opponent_hand = event.player.hand
                        self.opponent_hand.reset()
                        self.state = PgPlayerState.SCORE_OPP_HAND
                    self.q = event.q
                elif event.subtype == "score_crib":
                    self.last_scoring_msg = event.msg
                    self.crib = event.player.crib
                    self.q = event.q
                    self.state = PgPlayerState.SCORE_CRIB
                elif event.subtype == "game_over":
                    self.state = PgPlayerState.GAME_OVER

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pt = pygame.mouse.get_pos()
                if len(self.hand) > 0 and isinstance (self.hand[0], PgCard):
                    for pgCard in self.hand:
                        if pgCard.contains_point(pt):
                            if self.state == PgPlayerState.LAY_AWAY or \
                                    (self.state == PgPlayerState.PLAY and pgCard.points + self.discards.sum <= 31):
                                pgCard.selected = not pgCard.selected
                if self.confirm_selection (pt):
                    if self.state == PgPlayerState.PLAY:
                        self.made_play = True
                    elif self.state == PgPlayerState.LAY_AWAY:
                        self.state = PgPlayerState.PLAY
                    elif self.state == PgPlayerState.GAME_OVER:
                        self.start_new_game()
                    if self.state != PgPlayerState.GAME_OVER:
                        self.q.put(None)

            self.screen.fill(BLACK)
            self.display_scores()
            if self.state == PgPlayerState.GAME_OVER:
                pass
            else:
                self.display_cards()
                self.display_crib()
            self.display_message()
            pygame.display.flip()

    def select_lay_aways(self, my_crib : bool):
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
        self.made_play = False
        hand = self.hand
        q = Queue()
        event = pygame.event.Event(pygame.USEREVENT, subtype="select_play", q=q)
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
        if notification.type == Cribbage.NotificationType.PLAY:
            msg = ""
            if notification.player == self:
                msg = "You played the " + notification.data
            else:
                msg = "Opponent played the " + notification.data
            if notification.points > 0:
                msg += " for " + str(notification.points)
            self.post_event(pygame.event.Event(pygame.USEREVENT, subtype="points", msg=msg), 2)
        elif notification.type in [Cribbage.NotificationType.POINTS, Cribbage.NotificationType.SCORE_HAND, Cribbage.NotificationType.SCORE_CRIB]:
            msg = ("You " if notification.player == self else "Opponent") + " scored +" + str(notification.points) + ": " + notification.data
            subtype = str(notification.type).lower().replace("notificationtype.", "")
            if subtype == "points":
                self.post_event(pygame.event.Event(pygame.USEREVENT, subtype=subtype, player=notification.player, msg=msg), 2)
            else:
                q = Queue()
                self.post_event(pygame.event.Event(pygame.USEREVENT, subtype=subtype, player=notification.player, msg=msg, q=q), 2)
                q.get()
        elif notification.type == Cribbage.NotificationType.GO:
            msg = "You said 'go'" if notification.player == self else "Opponent said 'go'"
            self.post_event(pygame.event.Event(pygame.USEREVENT, subtype="points", msg=msg), 2)
        elif notification.type == Cribbage.NotificationType.GAME_OVER:
            self.post_event(pygame.event.Event(pygame.USEREVENT, subtype="game_over"), 0)
        elif notification.type == Cribbage.NotificationType.CUT_FOR_DEAL:
            pass    # TODO - implement GUI for this
            #  TODO - also implement home screen that includes logic to pick opponent level
            

# Play the game
player = PgPlayer()
player.play()