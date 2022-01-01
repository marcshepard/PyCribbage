"""
TestHarness.py - A test harness for the cribbage engine
"""

import CribbageEngine

# Tracing function for console output
def trace (s):
    pass
    #print (s)

def verify_classes():
    # Verified an unshuffled deck starts with a 2 of clubs and has 52 cards
    deck = CribbageEngine.Deck()
    card = deck.draw()
    assert card.suit == CribbageEngine.Suit.CLUBS, "Unshuffled deck doesn't start wtih ace of clubs"
    assert card.rank == 1, "Unshuffled deck doesn't start wtih ace of clubs"
    for i in range(1, 52):
        card = deck.draw()
        assert type(card) is CribbageEngine.Card, "Deck should have 52 cards"

    # Verify we can shuffle a deck, and deal a cribbage hand from 6 drawn cards
    deck = CribbageEngine.Deck()
    deck.shuffle()
    hand = CribbageEngine.Hand ()
    while len(hand) < 6:
        hand.add_card (deck.draw())
    assert len(hand) == 6

    # Verify we can sort the hand
    hand.sort()
    last_rank = 0
    for card in hand:
        assert card.rank >= last_rank, "Dealt hands should be sorted by rank"
        last_rank = card.rank

    # Verify we can discard
    card = hand.play_card(hand[0])
    assert isinstance (card, CribbageEngine.Card), "Playing a card should return a card"
    assert len(hand) == 5, "Playing a card should reduce the hand size by 1"
    assert card in hand.played_cards, "Playing a card should move it to the played_cards pile"

    # Verify we can reclaim the played cards
    while len(hand) > 0:
        hand.play_card(hand[0])
    hand.reset()
    assert len(hand) == 6, "Reset should restore the hand (bring back played cards)"

    # Verify we can create a discard pile
    deck = CribbageEngine.Deck()
    deck.shuffle()
    discards = CribbageEngine.Discards()
    for i in range (3):
        discards.add_card (deck.draw())
    assert len(discards) == 3, "Discards.add_card() should add cards"
    trace (discards)
    discards.start_new_pile()
    assert len(discards) == 0, "Discards.start_new_pile() should reset the current pile"
    assert len(discards.older_discards) == 3, "Discards.start_new_pile() should append to older_discards"
    for i in range (2):
        discards.add_card (deck.draw())
    trace (discards)
    discards.start_new_pile()
    assert len(discards.older_discards) == 5, "Discards.start_new_pile() should append to older_discards"

    # Verify we can play a match between various AIs
    matches = [[CribbageEngine.BeginerPlayer(), CribbageEngine.BeginerPlayer()], \
        [CribbageEngine.IntermediatePlayer(), CribbageEngine.IntermediatePlayer()], \
        [CribbageEngine.AdvancedPlayer(), CribbageEngine.AdvancedPlayer()], \
        [CribbageEngine.BeginerPlayer(), CribbageEngine.AdvancedPlayer()]    ]
    for match in matches:
        game = CribbageEngine.Game(match)
        game.play()
        assert (game.players[0].score == 121 and game.players[1].score < 121) or \
            (game.players[1].score == 121 and game.players[0].score < 121), "Unexpected game score"

import time


# To test the classes:
verify_classes()

# See how the various AIs perform against each other:
CribbageEngine.play_match (CribbageEngine.AdvancedPlayer(), CribbageEngine.BeginerPlayer(), 50)
