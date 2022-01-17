A game of cribbage

Prereqs: A familiarity with the rules of cribbage: https://bicyclecards.com/how-to-play/cribbage/

Starting the game requires the following three steps that must be done in this exact order:
1) Go to https://replit.com/@marcshepard1/PyCribbage?embed=true
2) Click the green button on the bottom right (it looks like a play button)
3) Click on the button labeled "Output" on the bottom middle

Alternatively, you can also play the game by cloning this repository on any device that has Python + PyGames installed (I've only tested on PC and Linux), and then running "python Cribbage.py"; but using replit above is simpler as there is no local install involved.

If you turn on "play hints" on the first screen, then each time you select cards for a pegging play or crib discard, text will say "Nice choice" or "Are you sure?" depending on if the program agrees with your choice or not.

There are three modules:
* Cribbage.py - GUI for interactive play, written in PyGames - this is the main entry point
* CribbageEngine.py - the engine that implements play, as well as the AI for opponent player
* TestHarness.py - tests the engine, and can also run tournaments between the AIs

Known bugs and issues: https://github.com/marcshepard/PyCribbage/issues



