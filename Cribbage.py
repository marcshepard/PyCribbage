"""
py - The entry point for the cribbage game

The main logic for cribbage play is in CribbageEngine.py, which orchestrates play between two Players (it supplies
player classes for various levels of AI play).

This module implements a subclass of CribbageEngine.Player for the interactive player, and provides that player
a GUI written in PyGames.

It is multi-threaded, where the UX event loop runs in the foreground and the engine itself runs as a daemon background
thread. This design allows for
* The engine to run without causing the UX to become non-responsive
* The app to exit gracefully when the UX is closed, regardless of the state of the engine

Some interactions between game and engine are synchronous; in particualr, we don't want the engine to continue until
the user has had time to review and acknolege the computed hand scores. Others are asynch but with a delay; e.g., pegging
score notifications should not block game play but should be displayed in the UX for a couple of seconds
Both use PyGames USERDEFINED events for the engine to send info to the GUI.
* In the former case, the event also includes a Queue that the engine blocks on; the UX puts a message in the queue to
  unblock the engine thread when the user is ready to continue.
* In the later case, the engine thread simply waits a couple of seconds after sending the event 
"""

import threading
import pygame
from pygame.constants import K_0, K_1, K_2
from pygame.event import Event
from CribbageEngine import AdvancedPlayer, Card, Hand, Player, Notification, NotificationType, Game, get_player
from enum import Enum, auto
from typing import Tuple
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

To improve performance, a dictionary is used to ensure a given card image is loaded at most once
"""
class PgCard(Card):
    _dict = {}  # Dictionary of already-loaded card images; initially empty

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
            new_height = int(img.get_height() * 1.2 // 1)
            new_width = int(img.get_width() * 1.2 // 1)
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
    NEW_GAME    = auto()    # New game started
    CUT_FOR_DEAL = auto()   # Cut for deal
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
class PgPlayer(Player):
    def __init__(self):
        super().__init__()
        self.name = "You"
        self.event = threading.Event()
        self.ai_level = 2
        self.play_hints = False
        self.game = None
        pygame.init()

    # Play a game, or start a new game
    def play(self, level : int = 1):
        self.state = PgPlayerState.NEW_GAME
        self.ux_event_loop()

    # Start another game
    def start_new_game(self):
        # Reset some state
        super().reset()
        self.state = PgPlayerState.OTHER
        self.last_scoring_msg = None
        self.made_play = False
        self.cut_card = None
        self.opponent_cut_card = None
        self.last_selected_card_ix = -1
        self.last_selected_layaways = ""

        # Get previous dealer, if there was one
        previous_dealer = self.game.initial_dealer if self.game is not None else None

        # Create a game, and launch as a daemon thread so it exits if the main UI exits
        opponent = get_player(self.ai_level)
        self.game = Game([self, opponent])
        game_engine_thread = None
        if previous_dealer is not None:   # Rotate dealer if there was a previous game
            args = [opponent if previous_dealer == self else self]
            game_engine_thread = threading.Thread(target=self.game.play, args=args)
        else:
            game_engine_thread = threading.Thread(target=self.game.play)
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
                if self.play_hints:
                    msg += self.comment_on_layaway_selection() + " "
                msg += "Click anywhere above to confirm crib discards"
            else:
                msg = "Select two cards for " + ("your" if self.my_crib else "the opponents") + " crib"
        elif self.state == PgPlayerState.PLAY and self.my_turn and not self.made_play:
            if self.num_cards_selected == 1:
                if self.play_hints:
                    msg += self.comment_on_play_selection() + " "
                msg += "Click anywhere above to confirm selection"
            elif len(self.hand) == 0:
                msg = "Your cards are played - we'll count hands in a moment"
            else:
                msg = "Select a card to play - pegging count is " + str(self.discards.sum)
        elif self.state in [PgPlayerState.SCORE_OPP_HAND, PgPlayerState.SCORE_HAND, PgPlayerState.SCORE_CRIB]:
            msg = ""
            if self.state == PgPlayerState.SCORE_CRIB:
                msg += "Your" if self.my_crib else "Your opponents"
                msg += " crib was scored - click anywhere to continue"
            elif self.state == PgPlayerState.SCORE_HAND:
                msg += "Your hand was scored - click anywhere to continue"
            else:
                msg += "Your opponents hand was scored - click anywhere to continue"
        elif self.state == PgPlayerState.PLAY and len(self.hand) == 0 and self.num_opp_cards == 0:
            msg = "The cards are all played - we'll count hands in a moment"
        elif self.state == PgPlayerState.GAME_OVER:
            msg = "You" if self.score > self.game.players[1].score else "Your opponent"
            msg += " won! Click anywhere to play again"
        font = pygame.font.Font(None, 32)
        text = font.render(msg, True, WHITE)
        textRect = text.get_rect()
        textRect.y = INSTRUCTIONS_Y
        textRect.centerx = SCREEN_WIDTH//2
        self.screen.blit(text, textRect)

    def confirm_selection(self, pt):
        right_area = pt[1] < INSTRUCTIONS_Y
        right_state = (self.state == PgPlayerState.LAY_AWAY and self.num_cards_selected == 2) or \
            (self.state == PgPlayerState.PLAY and self.num_cards_selected == 1)
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

    def display_new_game_message(self):
        font = pygame.font.Font(None, 32)

        y = CRIB_Y
        msgs = ["Welcome to Cribbage.py!",
                "Difficulty level = " + str(self.ai_level), 
                "Play hints = " + str(self.play_hints),
                "Click anywhere to continue", 
                "", "", "", "",
                "Type 0, 1, or 2 to adjust the difficulty level (0 = easiest)",
                "Type h to toggle hint"]

        for msg in msgs:
            text = font.render(msg, True, WHITE)
            textRect = text.get_rect()
            textRect.y = y
            textRect.centerx = SCREEN_WIDTH//2
            self.screen.blit(text, textRect)
            y += text.get_height() + GAP//2

    def display_cut_for_deal_message(self):
        font = pygame.font.Font(None, 32)

        y = SCORE_Y
        msgs = ["Cut for deal"]
        if self.opponent_cut_card is not None and self.cut_card is not None:
            if self.cut_card.rank < self.opponent_cut_card.rank:
                msgs.append("You drew the lower card so get the first crib")
            else:
                msgs.append("Your opponent drew the lower card so gets the first crib")
            msgs.append ("Click anywhere to continue")

        for msg in msgs:
            text = font.render(msg, True, WHITE)
            textRect = text.get_rect()
            textRect.y = y
            textRect.centerx = SCREEN_WIDTH//2
            self.screen.blit(text, textRect)
            y += text.get_height() + GAP//2
    
    def display_scores(self):
        font = pygame.font.Font(None, 32)
        
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

    # Display the dealer and player cards to the screen
    def display_cards(self):
        x_incr = SCREEN_WIDTH//6 if self.state == PgPlayerState.LAY_AWAY else SCREEN_WIDTH//4

        # No need to display anything if we are scoring the crib
        if self.state == PgPlayerState.SCORE_CRIB:
            return

        pg_hands_initialized = self.hand is not None and len(self.hand) > 0 and isinstance (self.hand[0], PgCard)
        
        # Show dealers cards
        if self.state == PgPlayerState.CUT_FOR_DEAL and self.cut_card is not None:
            pgCard = PgCard(self.opponent_cut_card)
            pgCard.x = SCREEN_WIDTH//4
            pgCard.y = DEALER_Y
            pgCard.blit(self.screen)
        elif self.state == PgPlayerState.SCORE_OPP_HAND:
            for i in range(len(self.opponent_hand)):
                pgCard = PgCard(self.opponent_hand[i])
                pgCard.x = i * x_incr
                pgCard.y = DEALER_Y
                pgCard.blit(self.screen)
        elif self.state != PgPlayerState.SCORE_HAND and pg_hands_initialized:
            for i in range(self.num_opp_cards):
                pgCard = PgCard(None)
                pgCard.x = i * x_incr
                pgCard.y = DEALER_Y
                pgCard.blit(self.screen)

        # Show players cards
        if self.state == PgPlayerState.CUT_FOR_DEAL and self.cut_card is not None:
            pgCard = PgCard(self.cut_card)
            pgCard.x = SCREEN_WIDTH//4
            pgCard.y = PLAYER_Y
            pgCard.blit(self.screen)
        elif self.state not in [PgPlayerState.SCORE_OPP_HAND, PgPlayerState.SCORE_CRIB] and pg_hands_initialized:
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
                if event.subtype == "cut_for_deal":
                    self.q = event.q
                    assert self.state == PgPlayerState.CUT_FOR_DEAL, "Got a cut_for_deal user event when not in CUT_FOR_DEAL state"
                elif event.subtype=="layaway":
                    self.state = PgPlayerState.LAY_AWAY
                    self.last_scoring_msg = ""
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
                # A user click in the NEW_GAME state starts a new game
                if self.state in [PgPlayerState.NEW_GAME, PgPlayerState.GAME_OVER]:
                    self.start_new_game()
                    self.state = PgPlayerState.CUT_FOR_DEAL
                # A user click in one of these states continues program execution
                elif self.state in [PgPlayerState.CUT_FOR_DEAL, PgPlayerState.SCORE_HAND, PgPlayerState.SCORE_OPP_HAND, PgPlayerState.SCORE_CRIB]:
                    self.q.put(None)
                # A click on one of these states might either be card selection, or confirmation of selected cards
                elif self.state in [PgPlayerState.PLAY, PgPlayerState.LAY_AWAY]:
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
                        self.q.put(None)
   
            elif self.state == PgPlayerState.NEW_GAME and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_0:
                    self.ai_level = 0
                elif event.key == pygame.K_1:
                    self.ai_level = 1
                elif event.key == pygame.K_2:
                    self.ai_level = 2
                elif event.key == pygame.K_h:
                    self.play_hints = not self.play_hints

            self.screen.fill(BLACK)
            if self.state == PgPlayerState.NEW_GAME:
                self.display_new_game_message()
            elif self.state == PgPlayerState.CUT_FOR_DEAL:
                self.display_cut_for_deal_message()
                self.display_cards()
                self.display_crib()
            elif self.state == PgPlayerState.GAME_OVER:
                self.display_scores()
                self.display_message()
            else:
                self.display_scores()
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

    def select_play(self, starter, discards, num_opp_cards):
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

    def notify(self, notification : Notification):
        if notification.type == NotificationType.PLAY:
            msg = ""
            if notification.player == self:
                msg = "You played the " + notification.data
            else:
                msg = "Opponent played the " + notification.data
            if notification.points > 0:
                msg += " for " + str(notification.points)
            self.post_event(pygame.event.Event(pygame.USEREVENT, subtype="points", msg=msg), 2)
        elif notification.type in [NotificationType.POINTS, NotificationType.SCORE_HAND, NotificationType.SCORE_CRIB]:
            msg = ("You " if notification.player == self else "Opponent") + " scored +" + str(notification.points) + ": " + notification.data
            subtype = str(notification.type).lower().replace("notificationtype.", "")
            if subtype == "points":
                self.post_event(pygame.event.Event(pygame.USEREVENT, subtype=subtype, player=notification.player, msg=msg), 2)
            else:
                q = Queue()
                self.post_event(pygame.event.Event(pygame.USEREVENT, subtype=subtype, player=notification.player, msg=msg, q=q), 0)
                q.get()
        elif notification.type == NotificationType.GO:
            msg = "You said 'go'" if notification.player == self else "Opponent said 'go'"
            self.post_event(pygame.event.Event(pygame.USEREVENT, subtype="points", msg=msg), 2)
        elif notification.type == NotificationType.GAME_OVER:
            self.post_event(pygame.event.Event(pygame.USEREVENT, subtype="game_over"), 0)
            # TODO - make sure deal rotates in the next game
        elif notification.type == NotificationType.CUT_FOR_DEAL:
            if notification.player == self:
                self.cut_card = notification.data
            else:
                self.opponent_cut_card = notification.data
            if self.cut_card is not None and self.opponent_cut_card is not None:
                q = Queue()
                self.post_event(pygame.event.Event(pygame.USEREVENT, subtype="cut_for_deal", q=q), 0)
                q.get()

    # Figure out what cards the advanced AI player would play, compare to player selection, and return a hint
    def comment_on_layaway_selection(self):
        comment = "Nice choice."
        
        # Find out which cards the user selected, and what hand they would have left
        last_selected_layaways = ""
        crib = []
        hand = Hand()
        for card in self.hand:
            if card.selected:
                crib.append(card)
                last_selected_layaways += str(card) + ", "
            else:
                hand.add_card(card)

        if self.last_selected_layaways == last_selected_layaways:
            return self.last_selected_layaways_comment

        # Find out what cards the AI would have selected
        card1, card2, expected_value = AdvancedPlayer.find_lay_aways (self.hand, self.my_crib)

        # Compare the scores of the two
        selected_value = AdvancedPlayer.expected_value(hand, crib, self.my_crib)
        if selected_value < expected_value:
            comment = "Are you sure?"
        
        print ("\nExpected value of this choice is " + str(selected_value))
        self.last_selected_layaways = last_selected_layaways
        self.last_selected_layaways_comment = comment

        return comment
    
    # Figure out what card the advanced AI player would play, compare to player selection, and return a hint
    def comment_on_play_selection(self):
        selected_card_ix = None
        for card_ix in range (len(self.hand)):
            if self.hand[card_ix].selected:
                selected_card_ix = card_ix

        if selected_card_ix == self.last_selected_card_ix and len(self.hand) == self.last_hand_len:
            return self.last_selected_card_comment

        comment = "Nice choice."
        # Find out what card the AI would play to the pegging pile
        card_scores, max_score = AdvancedPlayer.find_play (self.hand, self.starter, self.discards, self.num_opp_cards) 
        
        # Compare it to the card the player selected
        if card_scores[selected_card_ix] != max_score:
            comment = "Are you sure?"

        self.last_selected_card_ix = selected_card_ix
        self.last_selected_card_comment = comment
        self.last_hand_len = len(self.hand)

        # Print the rankings to the console if there is more than 1 playable card
        if len(card_scores) > 1:
            list = []
            for i in range(len(card_scores)):
                list.append([card_scores[i], str(self.hand[i])])
            list = sorted(list, key=lambda x: x[0], reverse=True)
            print ("\nExpected point value of each card:")
            for member in list:
                print (member[1] + ": " + str(member[0]))

        return comment


# Play the game
if len(argv) >= 1:
    file = argv[0]
    cwd = getcwd()
    dir = path.dirname(file)
    if not path.isabs(dir):
        dir = cwd + "\\" + dir
    chdir(dir)

player = PgPlayer()
player.play()