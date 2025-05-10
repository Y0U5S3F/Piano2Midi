import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import threading

class VideoPlayer:
    def __init__(self, parent):
        self.parent = parent

        # Frame for video player and piano
        self.video_piano_frame = tk.Frame(parent)
        self.video_piano_frame.pack(padx=10, pady=10)

        # Canvas for video and piano
        self.canvas = tk.Canvas(self.video_piano_frame, width=800, height=600, bg="black")
        self.canvas.pack()

        # Frame for buttons
        self.button_frame = tk.Frame(parent)
        self.button_frame.pack(pady=5)

        # Load button
        self.load_button = tk.Button(self.button_frame, text="Load Video", command=self.load_video)
        self.load_button.pack(side=tk.LEFT, padx=5)

        # Play/Pause button
        self.play_pause_button = tk.Button(self.button_frame, text="Play/Pause", command=self.toggle_play_pause)
        self.play_pause_button.pack(side=tk.LEFT, padx=5)

        self.cap = None
        self.running = False
        self.paused = False

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
                self.parent.update_idletasks()
                self.parent.update()
                continue

            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (800, 600))  # Resize to fit canvas
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.image = imgtk  # Prevent garbage collection

            self.parent.update_idletasks()
            self.parent.update()

        if self.cap:
            self.cap.release()

    def toggle_play_pause(self):
        if self.running:
            self.paused = not self.paused

def draw_piano(canvas, white_key_width, white_key_height, start_x=10, start_y=400):
    BLACK_KEY_WIDTH = white_key_width * 0.6
    BLACK_KEY_HEIGHT = white_key_height * 0.6

    white_keys = []
    black_keys = []
    x = start_x

    # Generate white key names (A0 to C8)
    white_notes = ['A0', 'B0']  # Sub-contra octave
    for octave in range(1, 8):
        white_notes += [f'C{octave}', f'D{octave}', f'E{octave}', 
                        f'F{octave}', f'G{octave}', f'A{octave}', f'B{octave}']
    white_notes.append('C8')  # Five-line octave

    has_black = {
        ('A', 'B'): True,
        ('B', 'C'): False,
        ('C', 'D'): True,
        ('D', 'E'): True,
        ('E', 'F'): False,
        ('F', 'G'): True,
        ('G', 'A'): True,
    }

    positions = []

    # Draw white keys
    for note in white_notes:
        key = canvas.create_rectangle(
            x, start_y,
            x + white_key_width, start_y + white_key_height,
            fill="white", outline="black"
        )
        white_keys.append(key)
        positions.append(x)
        x += white_key_width

    # Draw black keys
    for i in range(1, len(white_notes)):
        current_note = white_notes[i - 1]
        next_note = white_notes[i]

        current_letter = current_note[0]
        next_letter = next_note[0]

        if (current_letter, next_letter) in has_black and has_black[(current_letter, next_letter)]:
            current_x = positions[i - 1]
            bx = current_x + white_key_width - (BLACK_KEY_WIDTH // 2)
            black_key = canvas.create_rectangle(
                bx, start_y,
                bx + BLACK_KEY_WIDTH, start_y + BLACK_KEY_HEIGHT,
                fill="black", outline="black"
            )
            black_keys.append(black_key)

    return white_keys, black_keys

def update_piano():
    try:
        width = int(width_entry.get())
        height = int(height_entry.get())
        if width < 5 or width > 100 or height < 30 or height > 300:
            status_label.config(text="Width: 5–100, Height: 30–300.")
            return
        draw_piano(video_player.canvas, width, height)
        status_label.config(text=f"Piano updated: width={width}, height={height}")
    except ValueError:
        status_label.config(text="Invalid input. Please enter integers.")

# Create Tkinter window
root = tk.Tk()
root.title("Video Player and Piano")

# Create VideoPlayer instance
video_player = VideoPlayer(root)

# Frame for width and height inputs
input_frame = tk.Frame(root)
input_frame.pack(pady=5)

# Width input
tk.Label(input_frame, text="White Key Width:").pack(side=tk.LEFT)
width_entry = tk.Entry(input_frame, width=5)
width_entry.insert(0, "14")
width_entry.pack(side=tk.LEFT)

# Height input
tk.Label(input_frame, text="White Key Height:").pack(side=tk.LEFT)
height_entry = tk.Entry(input_frame, width=5)
height_entry.insert(0, "120")
height_entry.pack(side=tk.LEFT)

# Update button
update_button = tk.Button(input_frame, text="Update Piano", command=update_piano)
update_button.pack(side=tk.LEFT, padx=5)

# Status label for messages
status_label = tk.Label(root, text="")
status_label.pack(pady=5)

# Initial draw
draw_piano(video_player.canvas, 14, 120)

root.mainloop()