import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import threading

class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Player")

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        self.load_button = tk.Button(root, text="Load Video", command=self.load_video)
        self.load_button.pack()

        self.cap = None
        self.running = False

    def load_video(self):
        video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
        if video_path:
            self.cap = cv2.VideoCapture(video_path)
            self.running = True
            threading.Thread(target=self.play_video).start()

    def play_video(self):
        while self.cap.isOpened() and self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (800, 600))  # Resize to fit canvas
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.image = imgtk  # Prevent garbage collection

            self.root.update_idletasks()
            self.root.update()

        self.cap.release()

root = tk.Tk()
app = VideoPlayer(root)
root.mainloop()
