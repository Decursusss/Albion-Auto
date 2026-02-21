import random
import cv2
import numpy as np
import win32api
import time
import win32con
from datetime import datetime

class PlayerStatusService:
    def __init__(self):
        self.VK_1 = 0x31
        self.VK_3 = 0x33
        self.coldown = datetime.now()

        self.tolerance_for_player_icon = 35
        self.tolerance_for_player_icon_ratio_min_value = 0.1
        self.hex_color_orange = "#d0460d"

        self.debug = False
        self.log = None

    def debug_log(self, message):
        if self.debug and self.log is not None:
            self.log(f"[Player Log] {message}")

    def crop_top_left_square(self, frame, size=60, offset_x=24, offset_y=45):
        h, w, _ = frame.shape

        x1 = min(max(0, offset_x), w - size)
        y1 = min(max(0, offset_y), h - size)

        return frame[y1:y1 + size, x1:x1 + size].copy()

    def check_color_level(self, frame, hex_color="#d0460d", tolerance=20, min_ratio=0.1):
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

    def press_key_1(self):
        win32api.keybd_event(self.VK_1, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.keybd_event(self.VK_1, 0, win32con.KEYEVENTF_KEYUP, 0)

    def press_key_3(self):
        win32api.keybd_event(self.VK_3, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.keybd_event(self.VK_3, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0)
        self.coldown = datetime.now()

    def process_player_status(self, frame):
        character_icon = self.crop_top_left_square(frame)
        found, ratio = self.check_color_level(character_icon, hex_color=self.hex_color_orange, tolerance=self.tolerance_for_player_icon, min_ratio=self.tolerance_for_player_icon_ratio_min_value)

        self.debug_log(f"Player Found {found} | Current Ratio {ratio}")
        # if found:
        #     print("!!Someone Attacked!!")
        #     res = datetime.now() - self.coldown
        #     if res.seconds >= 16:
        #         self.press_key_3()
        #         time.sleep(1.2 * random.uniform(0.8, 1.10))
        #     self.press_key_1()
        #     time.sleep(4 * random.uniform(0.8, 1.10))
        return character_icon, found, ratio

    def process(self):
        self.debug_log("!!Someone Attacked!!")
        #res = datetime.now() - self.coldown
        # if res.seconds >= 16:
        #     self.press_key_3()
        #     time.sleep(1.2 * random.uniform(0.8, 1.10))
        self.press_key_1()
        time.sleep(4 * random.uniform(0.8, 1.10))