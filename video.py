#!/usr/bin/env python3
import cv2
import numpy as np
import time
from piano import compute_piano_zones
from midi import build_file

class PianoZoneDetector:
    def __init__(self, video_path, zones,
                 diff_thresh=30,
                 speed=1,
                 bpm=120,
                 time_signature="4/4"):
        """
        :param video_path:       path to your video file
        :param zones:            list of (note, (x1,y1,x2,y2)) tuples
        :param diff_thresh:      min per-channel change for a “pixel change”
        :param speed:            frame-skip factor (1=every frame, 5=every5th)
        :param bpm:              tempo in BPM
        :param time_signature:   e.g. '4/4'
        """
        self.cap            = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise IOError(f"Cannot open {video_path}")

        self.zones          = zones
        self.diff_thresh    = diff_thresh
        self.speed          = max(1, int(speed))
        self.bpm            = bpm
        self.time_signature = time_signature

        # state
        self.active          = { note: False for note, _ in zones }
        self.prev_means      = { note: None  for note, _ in zones }

        # to collect chords: list of (comma_separated_notes, measure_offset)
        self.chords = []

    def _mean_color(self, frame, rect):
        x1, y1, x2, y2 = rect
        roi = frame[y1:y2, x1:x2]
        b,g,r,_ = cv2.mean(roi)
        return np.array([b,g,r], dtype=np.float32)

    def run(self, check_interval_ms=100):
        """
        Plays video at native FPS, but checks keys every check_interval_ms.
        Each check yields one "chord" of all ON notes at that moment.
        We place successive chords 0.25 measures apart.
        """
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        delay = int(1000/fps)
        last_check = 0.0
        measure_offset = 0.0
        quarter_of_measure = 0.25  # advance by a quarter-note measure

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            now_ms = time.time() * 1000
            do_check = (now_ms - last_check) >= check_interval_ms

            disp = frame.copy()
            on_notes = []
            for note, rect in self.zones:
                x1,y1,x2,y2 = rect
                cv2.rectangle(disp, (x1,y1),(x2,y2),(0,255,0),2)

                if do_check:
                    mean = self._mean_color(frame, rect)
                    prev = self.prev_means[note]
                    if prev is None:
                        self.prev_means[note] = mean
                    else:
                        diff = np.abs(mean - prev)
                        changed = np.any(diff > self.diff_thresh)
                        if changed and not self.active[note]:
                            self.active[note] = True
                        elif not changed and self.active[note]:
                            self.active[note] = False
                        self.prev_means[note] = mean

                    if self.active[note]:
                        on_notes.append(note)

            if do_check:
                # record all notes still ON at this check as one chord
                if on_notes:
                    chord_str = ",".join(on_notes)
                    self.chords.append((chord_str, measure_offset))
                measure_offset += quarter_of_measure
                last_check = now_ms

            cv2.imshow("Piano Zone Detector", disp)
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

        # write out the MIDI file with all collected chords
        build_file(self.chords,
                   bpm=self.bpm,
                   ts=self.time_signature,
                   output="detected.mid")
        print(f"✅  MIDI written to detected.mid")


if __name__ == "__main__":
    
    speed = 1
    tempo = 120
    signature = (4, 4)
    quarter_note_duration = 60 / tempo
    eighth_note_duration = quarter_note_duration / 2
    iterations = int(speed / eighth_note_duration)   
    
    zones = compute_piano_zones(
        video_width  = 1280,
        video_height = 720,
        start_y      = 560
    )
    detector = PianoZoneDetector(
        video_path      = "./detroit.mp4",
        zones            = zones,
        diff_thresh     = 30,
        speed           = speed,
        bpm             = tempo,
        time_signature  = "4/4"
    )
    # check every 100ms; chords will be placed 0.25 measures apart
    detector.run(check_interval_ms=iterations)
