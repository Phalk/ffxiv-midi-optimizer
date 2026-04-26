import os
import sys
import re
import tkinter as tk
from tkinter import filedialog
from mido import MidiFile, MidiTrack, Message, MetaMessage

# ANSI Color Codes for Terminal Styling
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BG_BLUE = '\033[44m'

INSTRUMENT_NAMES = {
    0: 'Grand Piano', 24: 'Lute', 27: 'Elec Guitar: Clean', 28: 'Elec Guitar: Muted',
    29: 'Elec Guitar: Overdriven', 30: 'Elec Guitar: Power Chords', 31: 'Elec Guitar: Special',
    40: 'Violin', 41: 'Viola', 42: 'Cello', 43: 'Double Bass',
    46: 'Harp', 47: 'Timpani', 56: 'Trumpet', 57: 'Trombone',
    58: 'Tuba', 60: 'Horn', 65: 'Saxophone', 68: 'Oboe',
    71: 'Clarinet', 72: 'Fife', 73: 'Flute', 75: 'Panpipes',
    110: 'Fiddle'
}

def clear_screen():
    """Clears the terminal for a cleaner dashboard UI."""
    os.system('cls' if os.name == 'nt' else 'clear')

def select_file_gui():
    """Opens a native file browser dialog if no file is passed via CLI."""
    root = tk.Tk()
    root.withdraw() # Hides the small tk window
    root.attributes('-topmost', True) # Forces the dialog to the front
    file_path = filedialog.askopenfilename(
        title="Select a MIDI file for FFXIV Bards",
        filetypes=[("MIDI Files", "*.mid *.midi"), ("All Files", "*.*")]
    )
    root.destroy()
    return file_path

def get_ffxiv_patch(gm_id):
    if gm_id in range(0, 8): return 0
    if gm_id in range(8, 16): return 46
    if gm_id in range(16, 24): return 0
    if gm_id in (24, 25, 26): return 27 
    if gm_id == 27: return 27
    if gm_id == 28: return 28
    if gm_id == 29: return 29
    if gm_id == 30: return 30
    if gm_id == 31: return 31
    if gm_id in range(32, 40): return 43
    if gm_id == 40: return 40
    if gm_id == 41: return 41
    if gm_id == 42: return 42
    if gm_id == 43: return 43
    if gm_id in (44, 45): return 40
    if gm_id == 46: return 46
    if gm_id == 47: return 47
    
    if gm_id in (52, 53, 54): return 65 
    if gm_id in range(48, 56) and gm_id not in (52, 53, 54): return 42 
    
    if gm_id == 56: return 56
    if gm_id == 57: return 57
    if gm_id == 58: return 58
    if gm_id == 59: return 56
    if gm_id == 60: return 60
    if gm_id in range(61, 64): return 56
    if gm_id in range(64, 68): return 65
    if gm_id in (68, 69): return 68
    if gm_id == 70: return 42
    if gm_id == 71: return 71
    if gm_id == 72: return 72
    if gm_id in (73, 74): return 73
    if gm_id == 75: return 75
    if gm_id in range(76, 80): return 73
    if gm_id == 110: return 110
    return 0

def ms_to_ticks(ms, tempo, ticks_per_beat):
    return int((ms * 1000 * ticks_per_beat) / tempo)

def adjust_overall_tempo(mid):
    print(f"\n{Colors.CYAN}>>> Adjust Overall Tempo:{Colors.RESET}")
    print(f"Current base tempo will be modified by a percentage multiplier.")
    print(f"Examples:")
    print(f"  {Colors.YELLOW} 1.0 {Colors.RESET} = Keep original speed (100%)")
    print(f"  {Colors.YELLOW} 1.2 {Colors.RESET} = Increase speed by 20% (Faster)")
    print(f"  {Colors.YELLOW} 0.8 {Colors.RESET} = Decrease speed by 20% (Slower)")
    
    try:
        factor = float(input(f"\n{Colors.BOLD}Enter speed multiplier:{Colors.RESET} "))
        if factor <= 0:
            raise ValueError
    except ValueError:
        return False
        
    changes_made = 0
    for track in mid.tracks:
        for i, msg in enumerate(track):
            if msg.type == 'set_tempo':
                new_tempo = int(msg.tempo / factor)
                if new_tempo < 10000: new_tempo = 10000 
                if new_tempo > 3000000: new_tempo = 3000000
                track[i] = msg.copy(tempo=new_tempo)
                changes_made += 1
                
    if changes_made == 0 and len(mid.tracks) > 0:
        new_base_tempo = int(500000 / factor)
        mid.tracks[0].insert(0, MetaMessage('set_tempo', tempo=new_base_tempo, time=0))
        
    return factor

def remap_to_ffxiv(mid):
    changes_made = 0
    for track in mid.tracks:
        has_notes = False
        track_channel = 0
        has_program_change = False
        final_patch = 0

        for i, msg in enumerate(track):
            if msg.type == 'note_on':
                has_notes = True
                track_channel = msg.channel
            
            if msg.type == 'program_change':
                has_program_change = True
                if getattr(msg, 'channel', 0) != 9: 
                    new_p = get_ffxiv_patch(msg.program)
                    if msg.program != new_p:
                        track[i] = msg.copy(program=new_p)
                        changes_made += 1
                    final_patch = new_p

        if has_notes:
            inst_name = 'Drum Kit' if track_channel == 9 else INSTRUMENT_NAMES.get(final_patch, 'Grand Piano')
            
            if not has_program_change and track_channel != 9:
                track.insert(0, Message('program_change', channel=track_channel, program=0, time=0))
                changes_made += 1

            meta_name_msg = None
            meta_idx = -1
            for i, msg in enumerate(track):
                if msg.is_meta and msg.type == 'track_name':
                    meta_name_msg = msg
                    meta_idx = i
                    break
            
            inst_tag = f"[{inst_name}]"
            
            if meta_name_msg:
                clean_name = re.sub(r'\s*\[.*?\]', '', meta_name_msg.name)
                track[meta_idx] = meta_name_msg.copy(name=f"{clean_name} {inst_tag}".strip())
            else:
                track.insert(0, MetaMessage('track_name', name=f"Track {inst_tag}", time=0))
    return changes_made

def fit_to_octaves(mid):
    adjusted_notes = 0
    for track in mid.tracks:
        for i, msg in enumerate(track):
            if msg.type in ('note_on', 'note_off'):
                original = msg.note
                new_note = original
                while new_note < 48:
                    new_note += 12
                while new_note > 84:
                    new_note -= 12
                if new_note != original:
                    track[i] = msg.copy(note=new_note)
                    adjusted_notes += 1
    return adjusted_notes

def duplicate_track(mid, track_idx, new_program):
    original_track = mid.tracks[track_idx]
    new_track = MidiTrack()
    
    inst_name = INSTRUMENT_NAMES.get(new_program, 'Custom')
    inst_tag = f"[{inst_name}]"
    
    accumulated_time = 0
    pc_applied = False
    base_channel = 0
    
    for msg in original_track:
        if hasattr(msg, 'channel') and getattr(msg, 'channel', 0) != 9:
            base_channel = msg.channel
            break
            
    for msg in original_track:
        if msg.type == 'end_of_track': 
            continue
            
        accumulated_time += msg.time
        
        if msg.type == 'program_change':
            if not pc_applied:
                new_track.append(Message('program_change', channel=base_channel, program=new_program, time=int(accumulated_time)))
                accumulated_time = 0
                pc_applied = True
        elif msg.is_meta and msg.type == 'track_name':
            clean_name = re.sub(r'\s*\[.*?\]', '', msg.name)
            new_track.append(MetaMessage('track_name', name=f"{clean_name} {inst_tag} (Copy)", time=int(accumulated_time)))
            accumulated_time = 0
        else:
            new_msg = msg.copy(time=int(accumulated_time))
            new_track.append(new_msg)
            accumulated_time = 0
            
    if not pc_applied:
        new_track.insert(0, Message('program_change', channel=base_channel, program=new_program, time=0))
        
    mid.tracks.append(new_track)
    return len(mid.tracks) - 1

def split_track_by_programs(mid, track_idx):
    original_track = mid.tracks[track_idx]
    
    abs_messages = []
    current_time = 0
    for msg in original_track:
        current_time += msg.time
        abs_messages.append({'msg': msg, 'abs_time': current_time})

    active_prog_per_ch = {c: 0 for c in range(16)}
    notes_per_part = {} 

    for item in abs_messages:
        msg = item['msg']
        ch = getattr(msg, 'channel', None)

        if msg.type == 'program_change' and ch is not None:
            active_prog_per_ch[ch] = msg.program

        if msg.type in ('note_on', 'note_off') and ch is not None:
            if ch == 9:
                key = (9, 'Drum')
            else:
                key = (ch, active_prog_per_ch[ch])

            if key not in notes_per_part:
                notes_per_part[key] = []
            notes_per_part[key].append(item)

    if len(notes_per_part) <= 1:
        return False

    base_name = f"Track {track_idx}"
    for msg in original_track:
        if msg.is_meta and msg.type == 'track_name':
            base_name = re.sub(r'\s*\[.*?\]', '', msg.name).strip()
            break

    new_tracks = []
    for (ch, prog), note_msgs in notes_per_part.items():
        new_track = MidiTrack()

        if ch == 9:
            inst_name = "Drum Kit"
            new_track.append(MetaMessage('track_name', name=f"{base_name} [{inst_name}]", time=0))
        else:
            inst_name = INSTRUMENT_NAMES.get(get_ffxiv_patch(prog), 'Grand Piano')
            new_track.append(MetaMessage('track_name', name=f"{base_name} [{inst_name}]", time=0))
            new_track.append(Message('program_change', channel=ch, program=prog, time=0))

        track_abs_msgs = []
        for item in abs_messages:
            msg = item['msg']
            msg_ch = getattr(msg, 'channel', None)

            if msg.is_meta and msg.type == 'track_name': continue
            if msg.type == 'program_change' and msg_ch == ch: continue
            if msg.type == 'end_of_track': continue

            if msg.type in ('note_on', 'note_off'):
                if item in note_msgs:
                    track_abs_msgs.append(item)
            else:
                if msg_ch is None or msg_ch == ch:
                    track_abs_msgs.append(item)

        last_time = 0
        for item in track_abs_msgs:
            delta = item['abs_time'] - last_time
            new_track.append(item['msg'].copy(time=int(delta)))
            last_time = item['abs_time']

        new_tracks.append(new_track)

    del mid.tracks[track_idx]
    for nt in new_tracks:
        mid.tracks.append(nt)

    return len(notes_per_part)

def generate_auto_drums(mid):
    max_abs_time = 0
    for track in mid.tracks:
        curr = 0
        for msg in track:
            curr += msg.time
        if curr > max_abs_time:
            max_abs_time = curr

    if max_abs_time == 0:
        return False

    print(f"\n{Colors.CYAN}>>> Select FFXIV Percussion Type:{Colors.RESET}")
    print(f"[{Colors.YELLOW} 1 {Colors.RESET}] Full Drum Kit (Bass, Snare, Cymbals)")
    print(f"[{Colors.YELLOW} 2 {Colors.RESET}] Bass Drum Only (4/4 Pulse)")
    print(f"[{Colors.YELLOW} 3 {Colors.RESET}] Snare Drum Only (Backbeat)")
    print(f"[{Colors.YELLOW} 4 {Colors.RESET}] Cymbals Only (Timekeeper)")
    print(f"[{Colors.YELLOW} 5 {Colors.RESET}] Bongos (Tribal Groove)")
    print(f"[{Colors.YELLOW} 6 {Colors.RESET}] Timpani (Orchestral Hits)")
    
    try:
        choice = int(input(f"\n{Colors.BOLD}Choice:{Colors.RESET} "))
    except ValueError:
        return False

    new_track = MidiTrack()
    
    if choice == 1:
        track_name = "Auto Full Kit"
        pattern = [60, 66, 62, 66, 60, 66, 62, 66]
    elif choice == 2:
        track_name = "Auto Bass Drum"
        pattern = [60, None, 60, None, 60, None, 60, None]
    elif choice == 3:
        track_name = "Auto Snare"
        pattern = [None, None, 62, None, None, None, 62, None]
    elif choice == 4:
        track_name = "Auto Cymbals"
        pattern = [66, 66, 66, 66, 66, 66, 66, 66]
    elif choice == 5:
        track_name = "Auto Bongos"
        pattern = [60, None, 61, 60, None, 61, 60, None]
    elif choice == 6:
        track_name = "Auto Timpani"
        pattern = [60, None, None, None, 60, None, None, None]
    else:
        return False

    new_track.append(MetaMessage('track_name', name=f"{track_name} [Drum Kit]", time=0))

    tpb = mid.ticks_per_beat
    step_ticks = tpb // 2 
    
    pattern_idx = 0
    current_abs_time = 0
    last_event_time = 0 

    while current_abs_time < max_abs_time:
        note = pattern[pattern_idx % 8]

        if note is not None:
            delta_on = current_abs_time - last_event_time
            new_track.append(Message('note_on', note=note, velocity=90, time=int(delta_on), channel=9))
            last_event_time = current_abs_time

            new_track.append(Message('note_off', note=note, velocity=0, time=10, channel=9))
            last_event_time += 10

        current_abs_time += step_ticks
        pattern_idx += 1

    mid.tracks.append(new_track)
    return True

def adjust_drumset(mid, track_idx):
    print(f"\n{Colors.CYAN}>>> Select Target FFXIV Instrument for this Drum Track:{Colors.RESET}")
    print(f"[{Colors.YELLOW} 1 {Colors.RESET}] Full Drum Kit (Map Kicks, Snares, Hats)")
    print(f"[{Colors.YELLOW} 2 {Colors.RESET}] Bass Drum Only")
    print(f"[{Colors.YELLOW} 3 {Colors.RESET}] Snare Drum Only")
    print(f"[{Colors.YELLOW} 4 {Colors.RESET}] Cymbals Only")
    print(f"[{Colors.YELLOW} 5 {Colors.RESET}] Bongos (Map Low/High)")
    print(f"[{Colors.YELLOW} 6 {Colors.RESET}] Timpani")
    
    try:
        choice = int(input(f"\n{Colors.BOLD}Choice:{Colors.RESET} "))
    except ValueError:
        return False

    track = mid.tracks[track_idx]
    adjusted_count = 0
    
    for i, msg in enumerate(track):
        if msg.type in ('note_on', 'note_off'):
            orig_note = msg.note
            new_note = 60 
            
            if choice == 1: 
                if orig_note in (35, 36): new_note = 60 
                elif orig_note in (38, 40): new_note = 62 
                elif orig_note in (42, 44, 46): new_note = 66 
                elif orig_note in (49, 51, 52, 55, 57): new_note = 68 
                else: new_note = 64 
            elif choice == 2: new_note = 60 
            elif choice == 3: new_note = 62 
            elif choice == 4: new_note = 66 
            elif choice == 5: 
                if orig_note < 40: new_note = 60
                else: new_note = 61
            elif choice == 6: new_note = 60 
            
            if orig_note != new_note:
                track[i] = msg.copy(note=new_note)
                adjusted_count += 1
                
    inst_tag_map = {1: 'Drum Kit', 2: 'Bass Drum', 3: 'Snare Drum', 4: 'Cymbal', 5: 'Bongo', 6: 'Timpani'}
    tag = inst_tag_map.get(choice, 'Drum Kit')
    
    meta_idx = -1
    meta_name_msg = None
    for i, msg in enumerate(track):
        if msg.is_meta and msg.type == 'track_name':
            meta_name_msg = msg
            meta_idx = i
            break
    
    if meta_name_msg:
        clean_name = re.sub(r'\s*\[.*?\]', '', meta_name_msg.name)
        track[meta_idx] = meta_name_msg.copy(name=f"{clean_name} [{tag}]".strip())
    else:
        track.insert(0, MetaMessage('track_name', name=f"Adjusted Drums [{tag}]", time=0))
        
    return adjusted_count

def clean_name_recursive(name):
    name = os.path.splitext(name)[0]
    name = re.sub(r'\s*\[\d+_(ch|tracks)\]', '', name)
    while re.match(r'^\d+\s*-\s*', name):
        name = re.sub(r'^\d+\s*-\s*', '', name)
    return name.replace('_', ' ').strip()

def draw_header(filename):
    print(f"{Colors.CYAN}{Colors.BOLD}╔════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║ {Colors.YELLOW}🎵 FFXIV MIDI OPTIMIZER{Colors.CYAN}                                          ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║ {Colors.RESET}File: {filename[:60]:<60} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╠════╦══════════════════════════════════╦═══════╦════════════════════════════╣{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║ {Colors.RESET}ID {Colors.CYAN}{Colors.BOLD}║ {Colors.RESET}TRACK NAME                       {Colors.CYAN}{Colors.BOLD}║ {Colors.RESET}NOTES {Colors.CYAN}{Colors.BOLD}║ {Colors.RESET}INSTRUMENT                 {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╠════╬══════════════════════════════════╬═══════╬════════════════════════════╣{Colors.RESET}")

def draw_footer():
    print(f"{Colors.CYAN}{Colors.BOLD}╚════╩══════════════════════════════════╩═══════╩════════════════════════════╝{Colors.RESET}")

def process_interactive():
    if len(sys.argv) < 2:
        print(f"{Colors.CYAN}No file provided in command line. Opening file browser...{Colors.RESET}")
        input_path = select_file_gui()
        if not input_path:
            print(f"{Colors.RED}No file selected. Exiting...{Colors.RESET}")
            return
    else:
        input_path = sys.argv[1]

    try:
        mid = MidiFile(input_path)
        
        if mid.type == 0:
            mid.type = 1
            
        original_tempo = 500000 
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    original_tempo = msg.tempo
                    break
        
        status_msg = "" 
        
        while True:
            clear_screen() 
            draw_header(os.path.basename(input_path))
            
            for i, track in enumerate(mid.tracks):
                notes = 0
                is_drum = False
                
                active_progs = {c: 0 for c in range(16)}
                parts_found = set()
                
                for m in track:
                    ch = getattr(m, 'channel', None)
                    if m.type == 'program_change' and ch is not None:
                        active_progs[ch] = m.program
                    elif m.type == 'note_on' and m.velocity > 0 and ch is not None:
                        notes += 1
                        if ch == 9:
                            is_drum = True
                            parts_found.add((9, 'Drum Kit'))
                        else:
                            parts_found.add((ch, active_progs[ch]))
                
                if notes > 0:
                    display_name = getattr(track, 'name', 'Unnamed')
                    if not display_name: display_name = 'Unnamed'
                    display_name = display_name[:32]
                    
                    if len(parts_found) > 1:
                        inst_info = f"{Colors.RED}⚠️ MULTIPLE DETECTED! Use 'i'{Colors.RESET}"
                    elif is_drum:
                        inst_info = f"{Colors.YELLOW}Drum Kit{Colors.RESET}"
                    elif len(parts_found) == 1:
                        prog = list(parts_found)[0][1]
                        if prog == 'Drum Kit':
                            inst_info = f"{Colors.YELLOW}Drum Kit{Colors.RESET}"
                        else:
                            inst_name = INSTRUMENT_NAMES.get(get_ffxiv_patch(prog), "Grand Piano")
                            inst_info = f"{inst_name}"
                    else:
                        inst_info = "Grand Piano"
                    
                    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {Colors.YELLOW}{i:>2}{Colors.RESET} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {display_name:<32} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {notes:<5} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {inst_info:<35} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")

            draw_footer()

            if status_msg:
                print(f"\n{status_msg}")
                status_msg = ""

            print(f"\n{Colors.BOLD}Track Commands:{Colors.RESET}")
            print(f"[{Colors.YELLOW} c ID {Colors.RESET}] Clean MS Latency    [{Colors.YELLOW} d ID {Colors.RESET}] Duplicate Track")
            print(f"[{Colors.YELLOW} r ID {Colors.RESET}] Remove Track        [{Colors.YELLOW} i ID {Colors.RESET}] Inspect Insts & Split")
            print(f"[{Colors.YELLOW} a ID {Colors.RESET}] Adjust Drumset      ")
            
            print(f"\n{Colors.BOLD}Global Commands:{Colors.RESET}")
            print(f"[{Colors.YELLOW} m {Colors.RESET}] Remap to FFXIV       [{Colors.YELLOW} o {Colors.RESET}] Fit Octaves")
            print(f"[{Colors.YELLOW} g {Colors.RESET}] Generate Auto-Drums  [{Colors.YELLOW} t {Colors.RESET}] Adjust Overall Tempo")
            print(f"[{Colors.YELLOW} s {Colors.RESET}] Save & Export        [{Colors.YELLOW} q {Colors.RESET}] Quit without saving")
            
            cmd = input(f"\n{Colors.BOLD}Command:{Colors.RESET} ").lower().strip()

            if cmd == 's': break
            if cmd == 'q': sys.exit()
            
            if cmd == 'm':
                remap_to_ffxiv(mid)
                status_msg = f"{Colors.GREEN}>>> Success! Instruments remapped and name tags applied.{Colors.RESET}"
            
            elif cmd == 'o':
                adjustments = fit_to_octaves(mid)
                status_msg = f"{Colors.GREEN}>>> {adjustments} notes realigned to fit FFXIV range.{Colors.RESET}"
                
            elif cmd == 'g':
                if generate_auto_drums(mid):
                    status_msg = f"{Colors.GREEN}>>> Auto-Drums generated successfully!{Colors.RESET}"
                else:
                    status_msg = f"{Colors.RED}>>> Generation cancelled or failed.{Colors.RESET}"
                    
            elif cmd == 't':
                factor = adjust_overall_tempo(mid)
                if factor is not False:
                    status_msg = f"{Colors.GREEN}>>> Tempo adjusted successfully by a factor of {factor}x!{Colors.RESET}"
                else:
                    status_msg = f"{Colors.RED}>>> Tempo adjustment cancelled.{Colors.RESET}"

            elif cmd.startswith('a '):
                parts = cmd.split(' ')
                if len(parts) > 1 and parts[1].isdigit():
                    idx = int(parts[1])
                    if idx < len(mid.tracks):
                        adjustments = adjust_drumset(mid, idx)
                        if adjustments is not False:
                            status_msg = f"{Colors.GREEN}>>> Drumset adjusted! {adjustments} notes mapped to FFXIV format.{Colors.RESET}"
                        else:
                            status_msg = f"{Colors.RED}>>> Adjustment cancelled.{Colors.RESET}"
                    else:
                        status_msg = f"{Colors.RED}Track does not exist.{Colors.RESET}"

            elif cmd.startswith('r '):
                parts = cmd.split(' ')
                if len(parts) > 1 and parts[1].isdigit():
                    idx = int(parts[1])
                    if idx < len(mid.tracks):
                        del mid.tracks[idx]
                        status_msg = f"{Colors.GREEN}>>> Track {idx} successfully removed.{Colors.RESET}"
                    else:
                        status_msg = f"{Colors.RED}Track does not exist.{Colors.RESET}"
                
            elif cmd.startswith('i '):
                parts = cmd.split(' ')
                if len(parts) > 1 and parts[1].isdigit():
                    idx = int(parts[1])
                    if idx < len(mid.tracks):
                        print(f"\n{Colors.CYAN}--- INSPECTING TRACK {idx} ---{Colors.RESET}")
                        target_track = mid.tracks[idx]
                        
                        active_progs = {c: 0 for c in range(16)}
                        parts_found = set()
                        
                        for msg in target_track:
                            ch = getattr(msg, 'channel', None)
                            if msg.type == 'program_change' and ch is not None:
                                active_progs[ch] = msg.program
                            elif msg.type == 'note_on' and msg.velocity > 0 and ch is not None:
                                if ch == 9:
                                    parts_found.add((9, 'Drum Kit'))
                                else:
                                    parts_found.add((ch, active_progs[ch]))
                                
                        if len(parts_found) > 0:
                            for ch, prog in parts_found:
                                if ch == 9:
                                    print(f"-> Channel 9 has notes {Colors.YELLOW}(FFXIV: Drum Kit){Colors.RESET}")
                                else:
                                    ffxiv_patch = get_ffxiv_patch(prog)
                                    inst_str = INSTRUMENT_NAMES.get(ffxiv_patch, "Grand Piano")
                                    print(f"-> Channel {ch} plays ID {prog} {Colors.YELLOW}(FFXIV: {inst_str}){Colors.RESET}")
                        else:
                            print(f"{Colors.YELLOW}No instruments found playing notes on this track.{Colors.RESET}")

                        print(f"{Colors.CYAN}----------------------------{Colors.RESET}")
                        
                        if len(parts_found) > 1:
                            print(f"\n{Colors.YELLOW}⚠️ Multiple instruments/channels detected.{Colors.RESET}")
                            do_split = input(f"Do you want to split these into independent tracks? (y/n): ").lower()
                            if do_split == 'y':
                                qty = split_track_by_programs(mid, idx)
                                if qty:
                                    status_msg = f"{Colors.GREEN}>>> Success! Track split into {qty} independent tracks.{Colors.RESET}"
                                    remap_to_ffxiv(mid)
                                else:
                                    status_msg = f"{Colors.YELLOW}>>> Failed to split.{Colors.RESET}"
                            else:
                                status_msg = f"{Colors.CYAN}Split cancelled.{Colors.RESET}"
                        else:
                            input(f"\n{Colors.CYAN}Press Enter to return to Dashboard...{Colors.RESET}")
                    else:
                        status_msg = f"{Colors.RED}Track does not exist.{Colors.RESET}"

            elif cmd.startswith('d '):
                parts = cmd.split(' ')
                if len(parts) > 1 and parts[1].isdigit():
                    idx = int(parts[1])
                    if idx < len(mid.tracks):
                        print(f"\n{Colors.CYAN}>>> Choose New Instrument:{Colors.RESET}")
                        for k, v in INSTRUMENT_NAMES.items():
                            print(f"{Colors.YELLOW}{k:>3}{Colors.RESET}: {v}")
                        try:
                            new_inst = int(input("\nInstrument ID: "))
                            new_track_id = duplicate_track(mid, idx, new_inst)
                            status_msg = f"{Colors.GREEN}>>> Track {idx} successfully duplicated to position {new_track_id}!{Colors.RESET}"
                            remap_to_ffxiv(mid) 
                        except ValueError:
                            status_msg = f"{Colors.RED}Invalid ID.{Colors.RESET}"
                    else:
                        status_msg = f"{Colors.RED}Track does not exist.{Colors.RESET}"

            elif cmd.startswith('c '):
                parts = cmd.split(' ')
                if len(parts) > 1 and parts[1].isdigit():
                    idx = int(parts[1])
                    if idx >= len(mid.tracks):
                        status_msg = f"{Colors.RED}Track does not exist.{Colors.RESET}"
                        continue
                    try:
                        ms_input = int(input(f"Minimum interval (ms) for Track {idx} (Suggested 120): "))
                        t_limit = ms_to_ticks(ms_input, original_tempo, mid.ticks_per_beat)
                        
                        new_track = MidiTrack()
                        removed_notes = 0
                        acc_time = 0

                        for msg in mid.tracks[idx]:
                            if msg.type == 'end_of_track': 
                                continue
                                
                            acc_time += msg.time
                            
                            if msg.type == 'note_on' and msg.velocity > 0:
                                if acc_time <= 2:
                                    new_track.append(msg.copy(time=int(acc_time)))
                                    acc_time = 0
                                elif acc_time < t_limit:
                                    removed_notes += 1
                                    continue
                                else:
                                    new_track.append(msg.copy(time=int(acc_time)))
                                    acc_time = 0
                            else:
                                new_track.append(msg.copy(time=int(acc_time)))
                                acc_time = 0

                        mid.tracks[idx] = new_track
                        status_msg = f"{Colors.GREEN}>>> {removed_notes} short notes removed. First note preserved and synced!{Colors.RESET}"
                    except ValueError:
                        status_msg = f"{Colors.RED}Invalid input.{Colors.RESET}"
                else:
                    status_msg = f"{Colors.RED}Please provide a track ID, e.g., 'c 2'{Colors.RESET}"

        clear_screen()
        new_filename = os.path.basename(input_path)
        
        output_dir = "show_ready"
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        
        mid.save(os.path.join(output_dir, new_filename))
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ READY FOR THE SHOW: {output_dir}/{new_filename}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}Technical Error: {e}{Colors.RESET}")

if __name__ == "__main__":
    process_interactive()