import cv2
import numpy as np
import os
import random
import time
import win32api
import win32con
from app.WeightStatus import WeightStatusService

class AnchorForMoovmentService:
    def __init__(self, anchor_path):
        self.template = cv2.imread(anchor_path, cv2.IMREAD_GRAYSCALE)
        self.th, self.tw = self.template.shape[:2]
        self.threshold = 0.43
        self.stuck_limit = 60
        self.hex_color_orange = "#d3ce00"
        self.hex_color_blue = "#0a64b1"

        self.VK_W = 0x57
        self.VK_A = 0x41
        self.VK_S = 0x53
        self.VK_D = 0x44
        self.VK_Z = 0x5A

        self.stuck_counter = 0
        self.screenshot_sended = False
        self.stop_mooving = False
        self.weight_status_service = WeightStatusService(anchor_service=None)

        self.debug = False
        self.log = None

    def debug_log(self, message):
        if self.debug and self.log is not None:
            self.log(f"[Anchor Log] {message}")

    def press_random_key(self):
        key_press = random.choice([self.VK_W, self.VK_D, self.VK_A, self.VK_S])
        win32api.keybd_event(key_press, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.keybd_event(key_press, 0, win32con.KEYEVENTF_KEYUP, 0)

    def press_z_key(self):
        win32api.keybd_event(self.VK_Z, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.keybd_event(self.VK_Z, 0, win32con.KEYEVENTF_KEYUP, 0)


    def check_color_level(self, frame, hex_color="#d3ce00", tolerance=20, min_ratio=0.1):
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

    def restart_anchor(self):
        self.stuck_counter = 0
        self.stop_mooving = None
        self.screenshot_sended = False
        self.press_z_key()
        time.sleep(10)
        self.press_z_key()
        for i in range(2):
            self.press_random_key()


    def process_found_anchor(self, frame):
        if not self.stop_mooving:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # gray = cv2.GaussianBlur(gray, (3, 3), 0)
            # gray = cv2.equalizeHist(gray)
            #
            # bin_img = cv2.adaptiveThreshold(
            #     gray, 255,
            #     cv2.ADAPTIVE_THRESH_MEAN_C,
            #     cv2.THRESH_BINARY,
            #     15, 3
            # )

            result = cv2.matchTemplate(
                gray,
                self.template,
                cv2.TM_CCOEFF_NORMED
            )

            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val < self.threshold:
                return None

            x, y = max_loc
            y -= 7
            roi = frame[y:y + self.th + 7, x:x + self.tw]

            color_ok, ratio = self.check_color_level(
                roi,
                hex_color=self.hex_color_orange,
                tolerance=35,
                min_ratio=0.10
            ) # check orange color health bar

            self.debug_log(f"Orange Color {color_ok} | Current Ratio {ratio}")

            if not color_ok:
                self.press_random_key()
                self.stuck_counter += 1
                if self.stuck_counter > self.stuck_limit and not self.screenshot_sended:
                    self.weight_status_service.send_telegram_screenshot(frame=frame, caption="Я застрял не могу найти куда двигаться!")
                    self.screenshot_sended = True
                    self.stop_mooving = True
                return None

            color_ok_blue, ratio_blue = self.check_color_level(
                roi,
                hex_color=self.hex_color_blue,
                tolerance=35,
                min_ratio=0.10
            )  # check blue color to not follow other players

            self.debug_log(f"Blue Color {color_ok_blue} | Current Ratio {ratio_blue}")

            if color_ok_blue:
                self.press_random_key()
                self.stuck_counter += 1
                if self.stuck_counter > self.stuck_limit and not self.screenshot_sended:
                    self.weight_status_service.send_telegram_screenshot(frame=frame, caption="Я застрял не могу найти куда двигаться!")
                    self.screenshot_sended = True
                    self.stop_mooving = True
                return None

            self.stuck_counter = 0
            self.screenshot_sended = False

            top_left = max_loc
            cx = top_left[0] + self.tw // 2
            cy = top_left[1] + self.th // 2

            cv2.rectangle(
                frame,
                top_left,
                (top_left[0] + self.tw, top_left[1] + self.th),
                (0, 255, 0),
                2
            )

            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            # if self.debug:
            #     cv2.imshow("Result", frame)
            return cx, cy
        else:
            self.restart_anchor()