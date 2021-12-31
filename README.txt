A game of cribbage

Prereqs: A Windows 10 PC with Python 3.9 (or later) and PyGames installed
* To instal Python: https://www.python.org/downloads/
* To instal pygames: from cmd prompt - pip install pygames
* A familiarity with the rules of cribbage: https://bicyclecards.com/how-to-play/cribbage/

To play:copy this git locally, and then either:
* Launch cmd and run "python CribbageUx.py"
* Launch the python app, and type:
    from os import chdir
    chdir("<path>")     # Where <path> is the full local path; make sure to escape the "\" (to "\\" with the string)
    import CribbageUs
* In theory there should be a way to make it work with windows file associations, but I've not figured it out

Known bugs/minor features:
* Add "home screen" GUI before game to pick opponent
* Add GUI for "cut for deal" (internally it is being done - just not exposed in UX)
* This list of bugs belongs in github and not in the README

Backlog of major work items:
* Add expert computer mode play:
    * Estimating the starter card when discarding
    * Consider opponent "counter-pegging" options when pegging
* Add statistics; wins/losses, avg crib, hand, pegging points
* Add super-expert mode
    * Includes data-driven play based on stats data (prereq - hosted telemetry stats)
* Add UX for "recommended play"
* Rewrite as web hosted app for xplat (and to learn)
* Rewrite in unity for xplat (and to learn)


