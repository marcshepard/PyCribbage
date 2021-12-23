"""
Player - abstract base class for a cribbage player
"""
from abc import abstractmethod, abstractproperty
import getpass
import Cards


class Player:
    @abstractproperty
    def name(self):
        pass

    @abstractmethod
    def new_game_welcome(self, opponent_name):
        pass

    @abstractmethod
    def cut_for_deal(self, draw_card, opponent_draw_card):
        pass

    @abstractmethod
    def select_lay_aways(self, hand):
        pass

    @abstractmethod
    def draw_starter(self, starter, my_turn):
        pass

    @abstractmethod
    def select_play(self, hand, starter, discards):
        pass

    @abstractmethod
    def get_event(self, is_me, points, message):
        pass

"""
ComputerPlayer - the automated computer opponent
"""
class ComputerPlayer(Player):
    @property
    def name(self):
        return "Computer"

    def new_game_welcome(self, opponent_name):
        pass

    def cut_for_deal(self, draw_card, opponent_draw_card):
        pass

    def select_lay_aways(self, hand):
        return 4, 5

    def draw_starter(self, starter, my_turn):
        pass

    def select_play(self, hand, starter, discards):
        return 0

    def get_event(self, is_me, points, message):
        pass

"""
ConsolePlayer - command line interface for the logged in user
"""
class ConsolePlayer(Player):
    @property
    def name(self):
        return getpass.getuser()

    def new_game_welcome(self, opponent_name):
        print()
        print("Hi, " + self.name + ". You are about to start a game against " + opponent_name + ".")
        self._opponent_name = opponent_name
        self._score = 0
        self._opponent_score = 0
    
    def cut_for_deal(self, draw_card, opponent_draw_card):
        input ("Type anything to cut for deal\n")
        print ("You drew the " + str(draw_card))
        print (self._opponent_name + " drew the " + str(opponent_draw_card))
        if opponent_draw_card.rank < draw_card.rank:
            print (self._opponent_name + " will go first")
        else:
            print ("You will go first")

    def select_lay_aways(self, hand):
        print()
        print ("The cards have been dealt - here is your hand: " + str(hand))
        while True:
            cards = input ("What (comma-separated) cards will you discard? ").split(",")
            if len(cards) != 2:
                print ("You need to type in exactly one comma")
                continue
            cards[0] = cards[0].strip()
            cards[1] = cards[1].strip()
            if (cards[0] == cards[1]):
                print ("You need to select two different cards")
                continue
            card0_ix = -1
            card1_ix = -1
            for i in range (0, len(hand.dealt_cards)):
                if str(hand.dealt_cards[i]) == cards[0]:
                    card0_ix = i
                if str(hand.dealt_cards[i]) == cards[1]:
                    card1_ix = i
            if card0_ix == -1 or card1_ix == -1:
                print ("Invalid choice: Please select two cards that are in your hand")
                continue
            if input ("Type c to confirm: ") == "c":
                return card0_ix, card1_ix

    def draw_starter(self, starter, my_turn):
        print()
        if self._score + self._opponent_score > 0:
            print ("Score: you - " + str(self._score) + ", " + self._opponent_name + " - " + str(self._opponent_score))
        if (my_turn):
            input ("Type anything to cut for the starter card: ")
            print ("Starter card: " + str(starter))
        else:
            print (self._opponent_name + " has cut to the starter card " + str(starter))
        self._starter_card = starter

    def select_play(self, hand, starter, discards):
        print()
        print (str(discards))
        print ("Starter card: " + str(starter))
        print ("Your hand: " + str(hand))
        valid_plays = ""
        for card in hand.unplayed_cards:
            if card.rank + discards.sum <= 31:
                valid_plays += str(card) + " "
        if len(valid_plays) == 0:
            valid_plays = "go"
        print ("Valid discards: " + valid_plays)
        while True:
            card = input ("What card will you discard? ").strip()
            if len(card) != 2 or card not in valid_plays:
                print ("Please enter a valid discard")
                continue
            for i in range (0, len(hand.unplayed_cards)):
                if str(hand.unplayed_cards[i]) == card:
                    return i
            return -1   # "go"

    def get_event(self, is_me, points, message):
        msg = ""
        if not is_me:
            msg += self._opponent_name + ": "
            self._opponent_score += points
        else:
            self._score += points
        msg += message
        if points > 0:
            msg += ". +" + str(points)
