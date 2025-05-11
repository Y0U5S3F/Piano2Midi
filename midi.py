#!/usr/bin/env python3
import argparse
import re
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

# your full midi_map...
midi_map = {
    'A0': 21, 'A#0': 22, 'B0': 23,
    'C1': 24, 'C#1': 25, 'D1': 26, 'D#1': 27, 'E1': 28, 'F1': 29, 'F#1': 30, 'G1': 31, 'G#1': 32, 'A1': 33, 'A#1': 34, 'B1': 35,
    'C2': 36, 'C#2': 37, 'D2': 38, 'D#2': 39, 'E2': 40, 'F2': 41, 'F#2': 42, 'G2': 43, 'G#2': 44, 'A2': 45, 'A#2': 46, 'B2': 47,
    'C3': 48, 'C#3': 49, 'D3': 50, 'D#3': 51, 'E3': 52, 'F3': 53, 'F#3': 54, 'G3': 55, 'G#3': 56, 'A3': 57, 'A#3': 58, 'B3': 59,
    'C4': 60, 'C#4': 61, 'D4': 62, 'D#4': 63, 'E4': 64, 'F4': 65, 'F#4': 66, 'G4': 67, 'G#4': 68, 'A4': 69, 'A#4': 70, 'B4': 71,
    'C5': 72, 'C#5': 73, 'D5': 74, 'D#5': 75, 'E5': 76, 'F5': 77, 'F#5': 78, 'G5': 79, 'G#5': 80, 'A5': 81, 'A#5': 82, 'B5': 83,
    'C6': 84, 'C#6': 85, 'D6': 86, 'D#6': 87, 'E6': 88, 'F6': 89, 'F#6': 90, 'G6': 91, 'G#6': 92, 'A6': 93, 'A#6': 94, 'B6': 95,
    'C7': 96, 'C#7': 97, 'D7': 98, 'D#7': 99, 'E7': 100, 'F7': 101, 'F#7': 102, 'G7': 103, 'G#7': 104, 'A7': 105, 'A#7': 106, 'B7': 107,
    'C8': 108
}

def note_str_to_midi(s: str) -> int:
    """
    Parse note like 'C#4', 'Db3', 'B5' into MIDI number.
    """
    m = re.match(r"^([A-Ga-g])([#b]?)(\d)$", s.strip())
    if not m:
        raise ValueError(f"Invalid note format: '{s}'")
    letter, acc, octave = m.groups()
    key = letter.upper() + (acc.replace('b', '#') if acc else '') + octave
    # normalize flats: Db -> C#
    flat_map = {'Db':'C#','Eb':'D#','Gb':'F#','Ab':'G#','Bb':'A#'}
    if key in flat_map:
        key = flat_map[key]
    if key not in midi_map:
        raise ValueError(f"Note '{s}' not found in midi_map.")
    return midi_map[key]

def build_file(chords, bpm, ts, output):
    mid = MidiFile()
    track = MidiTrack(); mid.tracks.append(track)

    # set tempo & time-signature
    track.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm), time=0))
    num, denom = map(int, ts.split('/'))
    track.append(MetaMessage('time_signature',
        numerator=num, denominator=denom,
        clocks_per_click=24, notated_32nd_notes_per_beat=8,
        time=0))

    ticks_per_beat = mid.ticks_per_beat
    beats_per_bar = num

    # collect all on/off events:
    events = []
    for chord_str, start in chords:
        notes = [ note_str_to_midi(n) for n in chord_str.split(',') ]
        start_tick = int(start * beats_per_bar * ticks_per_beat)
        dur = ticks_per_beat   # quarter-note
        for n in notes:
            events.append((start_tick,     'on',  n))
            events.append((start_tick+dur, 'off', n))

    # sort and write with delta times
    events.sort(key=lambda e:(e[0], 0 if e[1]=='on' else 1))
    last_tick = 0
    for tick, typ, note in events:
        delta = tick - last_tick
        msg = Message('note_on' if typ=='on' else 'note_off',
                      note=note, velocity=64, time=delta)
        track.append(msg)
        last_tick = tick

    mid.save(output)
    print(f"✅  Saved {output}")

def main():
    p = argparse.ArgumentParser(
        description="Build a MIDI containing multiple chords at specified measure-offsets"
    )
    p.add_argument(
        '-c','--chord',
        action='append',
        required=True,
        help="Chord and start offset, e.g. 'C3,C5:0.5' (comma-sep notes, colon, measure-offset)"
    )
    p.add_argument('-o','--output', default='out.mid', help="Output MIDI file")
    p.add_argument('--bpm', type=int, default=120, help="Tempo in BPM")
    p.add_argument('--ts','--time-signature', dest='ts', default='4/4',
                   help="Time signature (e.g. 4/4)")
    args = p.parse_args()

    # parse chords into list of (note_str, start_float)
    chords = []
    for entry in args.chord:
        notes_part, start_part = entry.split(':')
        chords.append((notes_part, float(start_part)))

    build_file(chords, args.bpm, args.ts, args.output)