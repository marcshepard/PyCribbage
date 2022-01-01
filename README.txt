A game of cribbage

Prereqs: A Windows 10 PC with Python 3.9 (or later) and PyGames installed
* To instal Python: https://www.python.org/downloads/
* To instal pygames: from cmd prompt - pip install pygames
* A familiarity with the rules of cribbage: https://bicyclecards.com/how-to-play/cribbage/

To play:copy this git locally, and then either:
* Launch from file explorer by double-clicking on Cribbage.py
* Launch cmd and run "python Cribbage.py"
* Launch the python app and type:
    from os import chdir
    chdir("<path>")     # Where <path> is the full local path; make sure to escape the "\" (to "\\" with the string)
    import CribbageUx

There are three modules:
* CribbageEngine.py - the engine that implements play, as well as some AI players
* TestHarness.py - tests the engine, and can also run tournaments between the AIs
* Cribbage.py - GUI for interactive play, written in PyGames

Known bugs and issues: https://github.com/marcshepard/PyCribbage/issues



