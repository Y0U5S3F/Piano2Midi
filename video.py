import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import threading
import numpy as np

class VideoPlayer:
    def __init__(self, parent):
        self.parent = parent

        self.video_piano_frame = tk.Frame(parent)
        self.video_piano_frame.pack(padx=10, pady=10)

        self.canvas = tk.Canvas(self.video_piano_frame, width=800, height=450, bg="black")
        self.canvas.pack()

        self.button_frame = tk.Frame(parent)
        self.button_frame.pack(pady=5)

        self.load_button = tk.Button(self.button_frame, text="Load Video", command=self.load_video)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.play_pause_button = tk.Button(self.button_frame, text="Play/Pause", command=self.toggle_play_pause)
        self.play_pause_button.pack(side=tk.LEFT, padx=5)

        self.cap = None
        self.running = False
        self.paused = False

        self.key_zones = []
        self.last_colors = {}
        self.piano_offset = None  # to be set from main

    def load_video(self):
        video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
        if video_path:
            self.cap = cv2.VideoCapture(video_path)
            self.running = True
            self.paused = False
            threading.Thread(target=self.play_video, daemon=True).start()

    def play_video(self):
        from piano import piano_offset  # Import offset shared
        while self.cap.isOpened() and self.running:
            if self.paused:
                self.parent.update_idletasks()
                self.parent.update()
                continue

            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (800, 450))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.image = imgtk

            self.canvas.tag_raise("white_key")
            self.canvas.tag_raise("black_key")
            self.canvas.tag_raise("piano")

            self.detect_key_changes(frame, piano_offset)

            self.parent.update_idletasks()
            self.parent.update()

        if self.cap:
            self.cap.release()

    def toggle_play_pause(self):
        if self.running:
            self.paused = not self.paused

    def set_key_zones(self, zones):
        self.key_zones = zones
        self.last_colors = {}

    def detect_key_changes(self, frame, piano_offset):
        for note, (x1, y1, x2, y2) in self.key_zones:
            x1_offset = int(x1 + piano_offset["x"])
            y1_offset = int(y1 + piano_offset["y"])
            x2_offset = int(x2 + piano_offset["x"])
            y2_offset = int(y2 + piano_offset["y"])

            roi = frame[y1_offset:y2_offset, x1_offset:x2_offset]
            if roi.size == 0:
                continue

            avg_color = cv2.mean(roi)[:3]
            avg_color = np.array(avg_color)

            last_color = self.last_colors.get(note)
            if last_color is not None:
                diff = np.linalg.norm(avg_color - last_color)
                if diff > 80:
                    print(f"Detected color change on {note}!")

            self.last_colors[note] = avg_color

# Global instance (needed by piano.py)
video_player = None
