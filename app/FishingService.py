import random

import cv2
import time
import win32api
import win32con
import win32gui
import numpy as np

class FishingService:
    def __init__(self, bober_example_path):
        self.bobberExample = cv2.imread(bober_example_path, cv2.IMREAD_GRAYSCALE)
        self.bobberExampleInWatter = cv2.imread("bobberExamples/bobberExampleInWatter2.png", cv2.IMREAD_GRAYSCALE)
        self.h, self.w = self.bobberExample.shape[:2]
        self.h_in, self.w_in = self.bobberExampleInWatter.shape[:2]

        self.tolerance_for_bobber = 45
        self.tolerance_ration_min_value = 0.0006
        self.bober_color_hex = "#FF3F2D"

        self.last_bobber_y = None
        self.missing_frames = 0
        self.MISSING_FRAMES_LIMIT = 2

        self.mouse_down = False

        self.previous_misings = []
        self.state_enter_time = time.time()
        self.last_seen_time = time.time()
        self.NO_OBJECT_TIMEOUT = 2.0
        self.state = "STARTING" # STARTING| HOOK | MINI GAME | RESTART GAME

        self.debug = False
        self.log = None

    def debug_log(self, message):
        if self.debug and self.log is not None:
            self.log(f"[Fishing Log] {message}")

    def set_state(self, new_state):
        self.state = new_state
        self.state_enter_time = time.time()

        if new_state == "MINI GAME":
            self.last_seen_time = time.time()
            self.mouse_down = False

        self.debug_log(f"➡️ STATE → {new_state}")

    def mouse_press(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        self.mouse_down = True

    def mouse_release(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        self.mouse_down = False


    def crop_center(self, frame, crop_w=130, crop_h=50):
        h, w, _ = frame.shape

        center_x = w // 2
        center_y = h // 2 + 18

        x1 = max(center_x - crop_w // 2, 0)
        y1 = max(center_y - crop_h // 2, 0)
        x2 = min(center_x + crop_w // 2, w)
        y2 = min(center_y + crop_h // 2, h)

        return frame[y1:y2, x1:x2]

    def get_game_window_rect(self, window_title):
        hwnd = win32gui.FindWindow(None, window_title)
        if not hwnd:
            return None

        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return left, top, right, bottom

    def map_mouse_to_frame_window(self, frame, window_title):
        rect = self.get_game_window_rect(window_title)
        if not rect:
            return None, None

        left, top, right, bottom = rect
        win_w = right - left
        win_h = bottom - top

        mx, my = win32api.GetCursorPos()

        rel_x = mx - left
        rel_y = my - top

        if rel_x < 0 or rel_y < 0 or rel_x > win_w or rel_y > win_h:
            return None, None

        frame_h, frame_w, _ = frame.shape

        fx = int(rel_x * frame_w / win_w)
        fy = int(rel_y * frame_h / win_h)

        return fx, fy

    def crop_mouse_area(self, frame, window_title, crop_w=100, crop_h=100):
        fx, fy = self.map_mouse_to_frame_window(frame, window_title)

        if fx is None:
            return None

        x1 = max(fx - crop_w // 2, 0)
        y1 = max(fy - crop_h // 2, 0)
        x2 = min(fx + crop_w // 2, frame.shape[1])
        y2 = min(fy + crop_h // 2, frame.shape[0])

        return frame[y1:y2, x1:x2]

    def check_color_level(self, frame, hex_color="#fe4c4c", tolerance=20, min_ratio=0.1):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        target = np.array([b, g, r])

        lower = np.clip(target - tolerance, 0, 255)
        upper = np.clip(target + tolerance, 0, 255)

        mask = np.all((frame >= lower) & (frame <= upper), axis=2)

        ratio = mask.sum() / mask.size

        return ratio >= min_ratio, ratio

    def find_bobber_in_roi(self, roi):
        found, ratio = self.check_color_level(roi, hex_color=self.bober_color_hex, tolerance=self.tolerance_for_bobber, min_ratio=self.tolerance_ration_min_value) #0.0006 - 0.0010
        self.debug_log(f"Bobber Found: {found} | Current Ratio {ratio}")
        if found:
            return found, ratio
        else:
            print("exit")

        return None, ratio

    def start_state(self):
        if time.time() - self.state_enter_time < 3:
            return

        self.mouse_press()
        time.sleep(random.uniform(0.38, 0.75))
        self.mouse_release()
        time.sleep(2)
        self.set_state("HOOK")

    def reset_state(self):
        if self.mouse_down:
            self.mouse_release()
        self.prev_gray = None

        if time.time() - self.state_enter_time < 0.5:
            return

        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        self.set_state("STARTING")


    def hook_state(self, frame):
        if time.time() - self.state_enter_time < 1:
            return frame

        roi = self.crop_mouse_area(
            frame,
            "Albion Online Client",
            crop_w=350,
            crop_h=440
        )


        if roi is None:
            return frame

        pos, score = self.find_bobber_in_roi(roi)

        if pos is None:
            self.missing_frames += 1

            if self.missing_frames >= self.MISSING_FRAMES_LIMIT and len(self.previous_misings) >= 2:
                self.mouse_press()
                time.sleep(0.05)
                self.mouse_release()

                self.set_state("MINI GAME")
                self.last_bobber_y = None
                self.missing_frames = 0
                self.previous_misings = []

            elif self.missing_frames >= self.MISSING_FRAMES_LIMIT and len(self.previous_misings) == 0:
                self.debug_log("No bobber in this status!")
                self.set_state("RESTART")
                self.last_bobber_y = None
                self.missing_frames = 0
                self.previous_misings = []

            return roi

        self.missing_frames = 0

        if len(self.previous_misings) <= 2:
            self.previous_misings.append(1)

        return roi

    def find_bober(self, frame):
        cropped = self.crop_center(frame, 130, 50)
        if cropped is None or cropped.size == 0:
            return frame

        frame = cv2.resize(cropped, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(gray_frame, self.bobberExample, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        now = time.time()

        if max_val < 0.7:
            if now - self.last_seen_time > self.NO_OBJECT_TIMEOUT:
                self.set_state("RESTART")
            return frame

        self.last_seen_time = time.time()

        x, y = max_loc

        cv2.rectangle(frame, (x, y), (x + self.w, y + self.h), (0, 255, 255), 2)
        if x <= 55:
            if not self.mouse_down:
                self.mouse_press()
        elif x <= 130:
            if not self.mouse_down:
                self.mouse_press()
        elif x >= 160:
            if self.mouse_down:
                self.mouse_release()

        return frame


    def controller(self, frame):
        if self.state == "STARTING":
            self.start_state()

        elif self.state == "HOOK":
            self.hook_state(frame)

        elif self.state == "MINI GAME":
            self.find_bober(frame)

        elif self.state == "RESTART":
            self.reset_state()

        # frame = self.hook_state(frame)
        #
        #
        # cv2.imshow("Fishing showing", frame)