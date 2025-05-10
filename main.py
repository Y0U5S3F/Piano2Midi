import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import threading
import numpy as np

# Track drag state
piano_offset = {"x": 10, "y": 330}  # Initial piano position
drag_data = {"x": 0, "y": 0}  # Track mouse position during drag

class VideoPlayer:
    def __init__(self, parent):
        self.parent = parent
        self.canvas = None
        self.cap = None
        self.running = False
        self.paused = False
        self.key_zones = []  # Store zones: (note, (x1, y1, x2, y2))
        self.last_colors = {}  # Track last color for each key zone
        self.active_notes = set()  # Track currently active notes
        self.debounce = {}  # Cooldown timer for each note

        # Initialize UI
        self.create_ui()
        
    def create_ui(self):
        # Frame for video player and piano
        self.video_piano_frame = tk.Frame(self.parent)
        self.video_piano_frame.pack(padx=10, pady=10)

        # Canvas for video and piano
        self.canvas = tk.Canvas(self.video_piano_frame, width=800, height=450, bg="black")
        self.canvas.pack()

        # Frame for buttons
        self.button_frame = tk.Frame(self.parent)
        self.button_frame.pack(pady=5)

        # Load button
        self.load_button = tk.Button(self.button_frame, text="Load Video", command=self.load_video)
        self.load_button.pack(side=tk.LEFT, padx=5)

        # Play/Pause button
        self.play_pause_button = tk.Button(self.button_frame, text="Play/Pause", command=self.toggle_play_pause)
        self.play_pause_button.pack(side=tk.LEFT, padx=5)

    def load_video(self):
        video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
        if video_path:
            self.cap = cv2.VideoCapture(video_path)
            self.running = True
            self.paused = False
            threading.Thread(target=self.play_video).start()

    def play_video(self):
        while self.cap.isOpened() and self.running:
            if self.paused:
                continue

            ret, frame = self.cap.read()
            if not ret:
                break

            # Resize to 16:9 ratio (800x450)
            frame = cv2.resize(frame, (800, 450))
            
            # Detect color changes
            self.detect_key_changes(frame)

            # Convert to PIL image and display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update canvas image
            if hasattr(self, 'last_img_id'):
                self.canvas.delete(self.last_img_id)
            self.last_img_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.image = imgtk

            # Ensure piano stays on top
            self.canvas.tag_raise("white_key")
            self.canvas.tag_raise("black_key")
            self.canvas.tag_raise("piano")

            self.parent.update_idletasks()
            self.parent.update()

        if self.cap:
            self.cap.release()

    def toggle_play_pause(self):
        if self.running:
            self.paused = not self.paused

    def set_key_zones(self, zones):
        """Set key zones: list of (note, (x1, y1, x2, y2))"""
        self.key_zones = zones
        self.last_colors = {}
        self.active_notes = set()
        self.debounce = {note: 0 for note, _ in zones}

    def detect_key_changes(self, frame):
        # Decrease debounce counters
        for note in self.debounce:
            if self.debounce[note] > 0:
                self.debounce[note] -= 1

        # Loop through each key zone
        for note, (x1, y1, x2, y2) in self.key_zones:
            # Ensure coordinates are within bounds
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            x1 = max(0, min(x1, frame.shape[1]-1))
            y1 = max(0, min(y1, frame.shape[0]-1))
            x2 = max(0, min(x2, frame.shape[1]-1))
            y2 = max(0, min(y2, frame.shape[0]-1))

            if x1 >= x2 or y1 >= y2:
                continue

            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue

            # Convert ROI to HSV for better color detection
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            avg_hsv = cv2.mean(hsv_roi)[:3]
            
            last_hsv = self.last_colors.get(note)
            if last_hsv is not None:
                # Calculate color difference in HSV space
                h_diff = min(abs(avg_hsv[0] - last_hsv[0]), 180 - abs(avg_hsv[0] - last_hsv[0])) / 90
                s_diff = abs(avg_hsv[1] - last_hsv[1]) / 255
                v_diff = abs(avg_hsv[2] - last_hsv[2]) / 255
                
                # Weighted difference (hue most important)
                diff = 0.5*h_diff + 0.2*s_diff + 0.3*v_diff
                
                # Dynamic threshold based on brightness
                brightness = avg_hsv[2]/255
                threshold = 0.2 + brightness*0.3
                
                if diff > threshold and self.debounce[note] == 0:
                    print(f"Detected color change on {note}!")
                    self.debounce[note] = 5  # 5 frame cooldown
                    self.active_notes.add(note)
                elif diff < threshold * 0.7:
                    self.active_notes.discard(note)
            
            # Update last color
            self.last_colors[note] = avg_hsv


def draw_piano(canvas, white_key_width, white_key_height, start_x=10, start_y=330):
    BLACK_KEY_WIDTH = int(white_key_width * 0.7)
    BLACK_KEY_HEIGHT = int(white_key_height * 0.6)

    white_notes = ['A0', 'B0']
    for octave in range(1, 8):
        white_notes += [f'C{octave}', f'D{octave}', f'E{octave}',
                        f'F{octave}', f'G{octave}', f'A{octave}', f'B{octave}']
    white_notes.append('C8')

    has_black = {
        ('A', 'B'): True,
        ('B', 'C'): False,
        ('C', 'D'): True,
        ('D', 'E'): True,
        ('E', 'F'): False,
        ('F', 'G'): True,
        ('G', 'A'): True,
    }

    midi_map = {
        'A0': 21, 'A#0': 22, 'B0': 23, 'C1': 24, 'C#1': 25, 'D1': 26, 'D#1': 27, 'E1': 28, 'F1': 29,
        'F#1': 30, 'G1': 31, 'G#1': 32, 'A1': 33, 'A#1': 34, 'B1': 35, 'C2': 36, 'C#2': 37,
        'D2': 38, 'D#2': 39, 'E2': 40, 'F2': 41, 'F#2': 42, 'G2': 43, 'G#2': 44, 'A2': 45, 'A#2': 46,
        'B2': 47, 'C3': 48, 'C#3': 49, 'D3': 50, 'D#3': 51, 'E3': 52, 'F3': 53, 'F#3': 54, 'G3': 55,
        'G#3': 56, 'A3': 57, 'A#3': 58, 'B3': 59, 'C4': 60, 'C#4': 61, 'D4': 62, 'D#4': 63, 'E4': 64,
        'F4': 65, 'F#4': 66, 'G4': 67, 'G#4': 68, 'A4': 69, 'A#4': 70, 'B4': 71, 'C5': 72, 'C#5': 73,
        'D5': 74, 'D#5': 75, 'E5': 76, 'F5': 77, 'F#5': 78, 'G5': 79, 'G#5': 80, 'A5': 81, 'A#5': 82,
        'B5': 83, 'C6': 84, 'C#6': 85, 'D6': 86, 'D#6': 87, 'E6': 88, 'F6': 89, 'F#6': 90, 'G6': 91,
        'G#6': 92, 'A6': 93, 'A#6': 94, 'B6': 95, 'C7': 96, 'C#7': 97, 'D7': 98, 'D#7': 99, 'E7': 100,
        'F7': 101, 'F#7': 102, 'G7': 103, 'G#7': 104, 'A7': 105, 'A#7': 106, 'B7': 107, 'C8': 108
    }

    positions = []
    x = int(start_x)
    start_y = int(start_y)
    zones = []

    # Draw white keys
    for note in white_notes:
        wkw = int(white_key_width)
        wkh = int(white_key_height)
        canvas.create_rectangle(
            x, start_y,
            x + wkw, start_y + wkh,
            outline="red",
            width=2,
            fill="white",
            tags=("white_key", "piano")
        )
        zones.append((note, (x, start_y, x + wkw, start_y + wkh)))
        positions.append(x)
        x += wkw

    # Draw black keys
    for i in range(1, len(white_notes)):
        current_note = white_notes[i - 1]
        next_note = white_notes[i]
        current_letter = current_note[0]
        next_letter = next_note[0]

        if (current_letter, next_letter) in has_black and has_black[(current_letter, next_letter)]:
            current_x = positions[i - 1]
            bx = current_x + int(white_key_width) - int(BLACK_KEY_WIDTH / 2)
            canvas.create_rectangle(
                bx, start_y,
                bx + BLACK_KEY_WIDTH, start_y + BLACK_KEY_HEIGHT,
                outline="red",
                width=2,
                fill="black",
                tags=("black_key", "piano")
            )
            black_note = f"{current_note[0]}#{current_note[1:]}"
            zones.append((black_note, (bx, start_y, bx + BLACK_KEY_WIDTH, start_y + BLACK_KEY_HEIGHT)))

    # Send zones to the video player for detection
    video_player.set_key_zones(zones)

    # Raise piano keys to the top
    canvas.tag_raise("white_key")
    canvas.tag_raise("black_key")
    canvas.tag_raise("piano")

    return "piano"


def start_drag(event):
    drag_data["x"] = event.x
    drag_data["y"] = event.y

def do_drag(event):
    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]
    video_player.canvas.move("piano", dx, dy)
    drag_data["x"] = event.x
    drag_data["y"] = event.y

    # Update piano_offset
    piano_offset["x"] += dx
    piano_offset["y"] += dy

    # Redraw zones with updated position
    update_zones(video_player.canvas)

def update_zones(canvas):
    """Recalculate key zones based on current piano position"""
    zones = []
    
    # Get all piano elements
    piano_items = canvas.find_withtag("piano")
    for item in piano_items:
        coords = canvas.coords(item)
        if len(coords) == 4:
            note = get_note_from_position(coords)
            if note:
                zones.append((note, coords))
    
    if zones:
        video_player.set_key_zones(zones)

def get_note_from_position(coords):
    """Placeholder function - should match your note mapping logic"""
    # In a real implementation, this would map coordinates to specific notes
    # based on piano layout
    return "C4"  # Example fallback


# Ensure the piano is drawn on top of the video and can be moved
def update_piano():
    try:
        width = float(width_entry.get())
        height = float(height_entry.get())
        if width < 5.0 or width > 100.0 or height < 30.0 or height > 300.0:
            status_label.config(text="Width: 5.0–100.0, Height: 30.0–300.0.")
            return
            
        # Clear old piano before drawing new one
        video_player.canvas.delete("piano")
        
        tag = draw_piano(video_player.canvas, width, height)
        # Bind movement
        video_player.canvas.tag_bind(tag, "<ButtonPress-1>", start_drag)
        video_player.canvas.tag_bind(tag, "<B1-Motion>", do_drag)
        status_label.config(text=f"Piano updated: width={width}, height={height}")
    except ValueError:
        status_label.config(text="Invalid input. Please enter numbers.")


# Create Tkinter window
root = tk.Tk()
root.title("Video Player and Piano")

video_player = VideoPlayer(root)

input_frame = tk.Frame(root)
input_frame.pack(pady=5)

tk.Label(input_frame, text="White Key Width:").pack(side=tk.LEFT)
width_entry = tk.Entry(input_frame, width=5)
width_entry.insert(0, "15.35")
width_entry.pack(side=tk.LEFT)

tk.Label(input_frame, text="White Key Height:").pack(side=tk.LEFT)
height_entry = tk.Entry(input_frame, width=5)
height_entry.insert(0, "100")
height_entry.pack(side=tk.LEFT)

update_button = tk.Button(input_frame, text="Update Piano", command=update_piano)
update_button.pack(side=tk.LEFT, padx=5)

status_label = tk.Label(root, text="")
status_label.pack(pady=5)

# Initial draw and bind drag
piano_tag = draw_piano(video_player.canvas, 14, 120)
video_player.canvas.tag_bind(piano_tag, "<ButtonPress-1>", start_drag)
video_player.canvas.tag_bind(piano_tag, "<B1-Motion>", do_drag)

root.mainloop()