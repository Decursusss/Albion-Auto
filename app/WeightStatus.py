import datetime
import random
import cv2
import numpy as np
import win32api
import time
import win32con
import requests

from app.WindowCapture import WindowCaptureService


class WeightStatusService:
    def __init__(self, anchor_service):
        self.TELEGRAM_TOKEN = ""
        self.CHAT_ID = ""
        self.last_update_id = None
        self.VK_Z = 0x5A
        self.VK_I = 0x49

        self.ALERT_ANNOUNCEMENT = None
        self.ON_MOUNT = False

        self.capture_service = WindowCaptureService()
        self.anchor_service = anchor_service

        self.now = time.time()
        self.checking_handle_commands = self.now

    def send_telegram_screenshot(self, frame, filename="screenshot.png", caption="Вот твой скриншот"):
        cv2.imwrite(filename, frame)
        url = f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': open(filename, 'rb')}
        data = {'chat_id': self.CHAT_ID, 'caption': caption}
        try:
            requests.post(url, files=files, data=data, timeout=5)
        except Exception as e:
            print("Ошибка при отправке скриншота:", e)

    def handle_updates(self):
        url = f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}/getUpdates"
        params = {}
        if self.last_update_id is not None:
            params["offset"] = self.last_update_id + 1

        resp = requests.get(url, params=params).json()
        for update in resp.get("result", []):
            self.last_update_id = update["update_id"]
            if "message" in update:
                text = update["message"].get("text", "")
                if text == "/check_screen":
                    print("Скриншот запрошен")
                    self.press_key_i()
                    time.sleep(random.uniform(1, 1.5))
                    frame = self.capture_service.capture_window("Albion Online Client")
                    self.press_key_i()
                    self.send_telegram_screenshot(frame=frame, caption="Вот твой скриншот!")

                if text == "/press z":
                    print(f"Запрошено нажатие кнопки")
                    self.press_key_z()
                    time.sleep(random.uniform(1, 1.5))
                    frame = self.capture_service.capture_window("Albion Online Client")
                    self.send_telegram_screenshot(frame=frame, caption="Нажал на кнопку Z")

                if text == "/enable_walk":
                    print("Запрошено продолжение движения")
                    self.anchor_service.stop_mooving = False
                    self.send_telegram_message("Снова начал двигаться!")


    def request_chat_id_from_bot(self):
        url = f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}/getUpdates"
        resp = requests.get(url)
        print(resp.json())

    def send_telegram_message(self, text):
        url = f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": self.CHAT_ID,
            "text": text
        }
        try:
            requests.get(url, params=payload, timeout=5)
        except Exception as e:
            print("Ошибка при отправке в Telegram:", e)

    def crop_top_right_square(self, frame, size=28, offset_x=348, offset_y=54):
        h, w, _ = frame.shape

        x1 = max(0, w - size - offset_x)
        y1 = min(max(0, offset_y), h - size)

        return frame[y1:y1 + size, x1:x1 + size].copy()

    def check_color_level(self, frame, hex_color="#d0460d", tolerance=20, min_ratio=0.1):
        # hex -> BGR
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

    def press_key_z(self):
        win32api.keybd_event(self.VK_Z, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.keybd_event(self.VK_Z, 0, win32con.KEYEVENTF_KEYUP, 0)

    def press_key_i(self):
        win32api.keybd_event(self.VK_I, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.keybd_event(self.VK_I, 0, win32con.KEYEVENTF_KEYUP, 0)

    def process_weight_status(self, frame):
        self.now = time.time()
        weight_icon = self.crop_top_right_square(frame)
        found_weight, ratio_weight = self.check_color_level(weight_icon, hex_color="#9B3B3F", tolerance=35, min_ratio=0.01)

        if self.now - self.checking_handle_commands > 10:
            self.handle_updates()
            self.checking_handle_commands = self.now

        # if found_weight:
        #     if not self.ON_MOUNT:
        #         self.press_key_z()
        #         time.sleep(5 * random.uniform(0.8, 1.10))
        #         self.ON_MOUNT = True
        #
        #     current_frame = self.capture_service.capture_window("ForTests - Paint") ## need get from window capture utils
        #     weight_icon = self.crop_top_right_square(current_frame)
        #     found_weight, ratio_weight = self.check_color_level(weight_icon, hex_color="#9B3B3F", tolerance=35, min_ratio=0.01)
        #     if found_weight:
        #         if self.ALERT_ANNOUNCEMENT is None:
        #             print("Sending Message")
        #             self.send_telegram_message("Достигнут максимальный вес надо разгрузить!")
        #             self.ALERT_ANNOUNCEMENT = datetime.datetime.now()
        #
        #         calculate_between = datetime.datetime.now() - self.ALERT_ANNOUNCEMENT
        #
        #         if calculate_between.seconds >= 600:
        #             print("Sending Message")
        #             self.send_telegram_message("Достигнут максимальный вес надо разгрузить!")
        #             self.ALERT_ANNOUNCEMENT = datetime.datetime.now()
        # else:
        #     self.ON_MOUNT = False

        return weight_icon, found_weight, ratio_weight

    def process(self):
        if not self.ON_MOUNT:
            self.press_key_z()
            time.sleep(5 * random.uniform(0.8, 1.10))
            self.ON_MOUNT = True

        current_frame = self.capture_service.capture_window("Albion Online client") ## need get from window capture utils
        weight_icon = self.crop_top_right_square(current_frame)
        found_weight, ratio_weight = self.check_color_level(weight_icon, hex_color="#9B3B3F", tolerance=35, min_ratio=0.01)
        if found_weight:
            if self.ALERT_ANNOUNCEMENT is None:
                print("Sending Message")
                #self.send_telegram_message("Достигнут максимальный вес надо разгрузить!")
                self.send_telegram_screenshot(frame=weight_icon, caption="Достигнут максимальный вес надо разгрузить!")
                self.ALERT_ANNOUNCEMENT = datetime.datetime.now()

            calculate_between = datetime.datetime.now() - self.ALERT_ANNOUNCEMENT

            if calculate_between.seconds >= 600:
                print("Sending Message")
                #self.send_telegram_message("Достигнут максимальный вес надо разгрузить!")
                self.send_telegram_screenshot(frame=weight_icon, caption="Достигнут максимальный вес надо разгрузить!")
                self.ALERT_ANNOUNCEMENT = datetime.datetime.now()