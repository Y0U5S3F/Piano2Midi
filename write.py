import pretty_midi

# Create a PrettyMIDI object (represents a MIDI file)
midi = pretty_midi.PrettyMIDI()

# Create an instrument (e.g., Acoustic Grand Piano with program number 0)
instrument = pretty_midi.Instrument(program=0)  # Program 0 is for Acoustic Grand Piano

# Define the melody (Twinkle Twinkle Little Star)
# Each tuple represents (pitch, start_time, end_time)
melody = [
    (60, 0.0, 0.5),  # C
    (60, 0.5, 1.0),  # C
    (67, 1.0, 1.5),  # G
    (67, 1.5, 2.0),  # G
    (69, 2.0, 2.5),  # A
    (69, 2.5, 3.0),  # A
    (67, 3.0, 4.0),  # G (longer note)
    (65, 4.0, 4.5),  # F
    (65, 4.5, 5.0),  # F
    (64, 5.0, 5.5),  # E
    (64, 5.5, 6.0),  # E
    (62, 6.0, 6.5),  # D
    (62, 6.5, 7.0),  # D
    (60, 7.0, 8.0),  # C (longer note)
]

# Add each note to the instrument
for pitch, start, end in melody:
    note = pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=end)
    instrument.notes.append(note)

# Add the instrument to the MIDI file
midi.instruments.append(instrument)

# Write the MIDI data to a file
midi.write('twinkle_twinkle.mid')