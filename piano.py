def compute_piano_zones(video_width, video_height, start_y, white_key_height=None):
    """
    Compute bounding boxes for piano-shaped zones across the width of a video frame.

    :param video_width: int, width of the video frame in pixels
    :param video_height: int, height of the video frame in pixels
    :param start_y: int, y-coordinate where the top of the white keys begins
    :param white_key_height: int or None, height of white keys; if None, uses video_height-start_y
    :return: List of tuples: [(note, (x1, y1, x2, y2)), ...]
    """
    # Number of white keys on a standard piano
    WHITE_KEYS = 52
    # If white key height not provided, fill down to bottom of frame
    if white_key_height is None:
        white_key_height = video_height - start_y

    # Compute white key dimensions
    white_key_width = video_width / WHITE_KEYS

    # Black key size relative to white keys
    BLACK_KEY_WIDTH = white_key_width * 0.7
    BLACK_KEY_HEIGHT = white_key_height * 0.6

    # Build list of white note names
    white_notes = ['A0', 'B0']
    for octave in range(1, 8):
        white_notes += [f'C{octave}', f'D{octave}', f'E{octave}',
                        f'F{octave}', f'G{octave}', f'A{octave}', f'B{octave}']
    white_notes.append('C8')

    # Map which pairs have black keys between them
    has_black = {
        ('A', 'B'): True,
        ('B', 'C'): False,
        ('C', 'D'): True,
        ('D', 'E'): True,
        ('E', 'F'): False,
        ('F', 'G'): True,
        ('G', 'A'): True,
    }

    zones = []
    x = 0

    # Draw white key zones
    positions = []  # store x-coordinates of white keys
    for note in white_notes:
        x1 = int(x)
        x2 = int(x + white_key_width)
        y1 = start_y
        y2 = start_y + white_key_height
        zones.append((note, (x1, y1, x2, y2)))
        positions.append(x)
        x += white_key_width

    # Draw black key zones
    for i in range(1, len(white_notes)):
        current = white_notes[i - 1]
        nxt = white_notes[i]
        pair = (current[0], nxt[0])
        if has_black.get(pair, False):
            base_x = positions[i - 1]
            bx1 = int(base_x + white_key_width - BLACK_KEY_WIDTH / 2)
            bx2 = int(bx1 + BLACK_KEY_WIDTH)
            by1 = start_y
            by2 = int(start_y + BLACK_KEY_HEIGHT)
            # black note name (e.g. C#4)
            black_note = f"{current[0]}#{current[1:]}"
            zones.append((black_note, (bx1, by1, bx2, by2)))

    return zones
