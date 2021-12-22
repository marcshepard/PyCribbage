Design notes...

CLASSES


Hand:
* __init__ (Card[])
* Card() cards
* Card() unplayed_cards
* Card() played_cards
* lay_away (card1_ix, card2_ix)
* Card play(unplayed_card_ix)

Discard:
* Player player
* Card card

Discards:
* Discard[] currentPile
* Discard[][] previousPiles

Player # Default player is interactive player
* name
* type (Enum)   # Current user, computer
* ix1, ix2 get_lay_aways (Hand hand)
* card_ix get_play(Game game, Hand hand)

Game
* Player[] players
* Hand[] hands
* int[] scores
* Card starter
* Discards discards
* Deck _deck
* int _whose_turn  # Whose turn is it for the current hand?
* int _whose_deal  # Whose deal is it?
* __init__(Player[] players):
    * create new deck, shuffle
    * cut for deal, set whose_deal (-1 from who wins the cut)
* deal():
    * whose_deal += 1 % num_players
    * whose_turn = whose_deal + 1 % num_players
    * Reset players hands, crib, discard piles
    * Create new deck and shuffle it
    * deal hands
    * whose_turn gets to cut the deck
    * select starter card
* create_crib():
    * each player selects 2 cards to transfer to the crib
        * option to get recommended_crib_discard - returns array of (card[], min, max, expected) value of discards, sorted by expected
    * next player cuts deck, starter card drawn, his heals scored
        might generate game_over event
* play():
    * if the person whose turn it is has >= 121, no-op
    * else, the person whose turn it is makes a play; either select a card to discard or say "go" (engine provides allowed options)
        * option to get recommended_play - returns array of (card[], min, max, expected) value of discards, sorted by expected
        * if go and no one else can go, then last_pegger gets a point and create new discard pile, and turn = last_pegger + 1
        * if card is played, update score (any of these might generate game_over event)
            * update player score for n-of-a-kind or runs
            * update player score for 15 or 31
            * update score for last card if this was the final card in all hands. If so, then score_hands()
            * update player score for last card if no one else can play
* score_hand(player_number):
    * score the players hand - default just auto-score; ideally config option to allow for manual score and also for muggins
    * if player_number = -1, score the whose_deal player crib
* score_hands():
    * for each player, starting at whose_deal + 1, score_hand(player_number)
    * score_hand (-1) to score the crib


Session:
* __init__:
    * Get user sign-in info
    * create Player for signed-in user
* Player
* GameResults[] history
* GameResultsStatistics statistics
* run():
    * If no signed-in user, provide option to sign-in
    * If signed in, provide options to:
        * Play new game (against the computer, one level)
        * View history
        * View statistics
        * Edit profile
        * quit

Main code:
* Create Session
* Session.run


Statistics
* num_games
* winning_percent
* num_wins
* num_losses
* num_skunks
* num_skunked
* TODO: add num_cribs/avg_crib, num_hands/avg_hand, num_pegs/avg_peg
* reset()