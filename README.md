# ffxiv-midi-optimizer
The Ultimate FFXIV MIDI Optimizer Tool for Bards

🛠️ **REQUIREMENTS:**
* Python 3.x
* `mido` library (Run: `pip install mido` in your terminal/cmd)
*(Note: Uses built-in `tkinter` for the file picker, no extra install needed).*

🚀 **HOW TO RUN:**
Double-click `ffxiv-midi-optimizer.py` to open the native file picker, OR drag & drop a `.mid` file directly onto the script!

🌍 **GLOBAL COMMANDS (Affects the whole song):**
* [ m ] Remap to FFXIV` - Converts weird GM instruments (Synths, Pads, FX) into valid FFXIV patches (Lute, Flute, Cello) so MidiBard2 detects the right icons automatically.
* [ o ] Fit Octaves` - Squeezes out-of-range notes into the FFXIV C3-C6 limit. No more silent bards!
* [ t ] Adjust Tempo` - Speeds up or slows down the whole song using a multiplier (e.g., `0.8` for 20% slower, `1.2` for 20% faster) to prevent game engine lag.
* [ g ] Auto-Drums` - Song has no beat? Generates a perfectly synced 4/4 drum track (Full Kit, Bongos, Snare, Cymbals) based on the song's length.
* [ s ] Save & Export` - Saves the fixed MIDI to a `show_ready` folder.

🎯 **TRACK COMMANDS (Affects specific tracks):**
* [ c ] Clean Latency` - Fixes "machine-gun" fast notes. Enter a MS limit (e.g., 120ms) and it will swallow rapid notes while keeping perfect track sync!
* [ i ] Inspect & Split` - Detects if a track hides multiple instruments or channels. If it does, BMP will ask if you want to cleanly split them into separate tracks.
* [ a ] Adjust Drumset` - Maps messy GM drum kits into clean FFXIV percussion (maps Kicks to 60, Snares to 62, Hats to 66, etc.).
* [ d ] Duplicate Track` - Clones a track and assigns it a new instrument to fill out your 5-Bard setup.
* [ r ] Remove Track` - Deletes unwanted tracks instantly.
