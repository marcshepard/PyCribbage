"""
TestHarness.py - test harness for the cribbage game
"""

import Cards
import Cribbage

# Tracing function for console output
def trace (s):
    print (s)

# Verified an unshuffled deck starts with a 2 of clubs and has 52 cards
deck = Cards.Deck()
card = deck.draw()
assert card.suit == Cards.Suit.CLUBS, "Unshuffled deck doesn't start wtih ace of clubs"
assert card.rank == 1, "Unshuffled deck doesn't start wtih ace of clubs"
for i in range(1, 52):
    card = deck.draw()
    assert type(card) is Cards.Card, "Deck should have 52 cards"

# Verify we can shuffle a deck, and create a cribbage hand from 6 drawn cards
deck = Cards.Deck()
deck.shuffle()
cards = []
while len(cards) < 6:
    cards.append (deck.draw())
hand = Cribbage.Hand (cards)
trace (hand)

# Verify the dealt hand is sorted, and after a lay-away the unplayed_cards are populated properly
assert len(hand.dealt_cards) == 6
last_rank = 0
for card in hand.dealt_cards:
    assert card.rank >= last_rank, "Dealt hands should be sorted by rank"
    last_rank = card.rank
hand.lay_away(4, 5)
for i in range (0, 4):
    assert str(hand.unplayed_cards[i]) == str(hand.dealt_cards[i]), "After lay_away, unplayed_cards should be populated with the remaining 4 cards"
trace (hand)

# Verify that playing cards moves cards from the unplayed pile to the played pile
for i in range (1, 5):
    card = hand.play(0)
    assert type(card) is Cards.Card, "Hand.play() should return a Card"
    assert len(hand.played_cards) == i, "Hand.play: should add a card to the played list"
    assert len(hand.unplayed_cards) == 4-i, "Hand.play: should remove a card from the unplayed list"
trace (hand)

# Verify we can create a discard pile
deck = Cards.Deck()
deck.shuffle()
discards = Cribbage.Discards()
for i in range (3):
    discards.add_card (deck.draw())
assert len(discards.current_pile) == 3, "Discards.add_card() should add cards"
trace (discards)
discards.start_new_pile()
assert len(discards.current_pile) == 0, "Discards.start_new_pile() should reset the current pile"
assert len(discards.older_discards) == 3, "Discards.start_new_pile() should append to older_discards"
for i in range (2):
    discards.add_card (deck.draw())
trace (discards)
discards.start_new_pile()
assert len(discards.older_discards) == 5, "Discards.start_new_pile() should append to older_discards"
