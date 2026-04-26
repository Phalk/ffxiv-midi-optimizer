# ffxiv-midi-optimizer

REQUIREMENTS:
* Python 3.x
* `mido` library (Run: `pip install mido` in your terminal/cmd)
* (Note: Uses built-in `tkinter` for the file picker, no extra install needed).*

What it does:

Adjusts notes to fit the playable range (C3–C6)
Simplifies tracks for easier instrument assignment in-game
Cleans overly fast/repeated notes
Splits mixed tracks when needed
Adds a basic drum track if the song has none
Lets you tweak tempo and duplicate/remove tracks

What it doesn’t do:

It does not accurately match the game’s internal instrument IDs/soundfonts
Instrument remapping is approximate and meant for convenience, not precision
Not intended as a “correct” or standardized MIDI converter
