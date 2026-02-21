import cv2
import numpy as np
import mss
import win32gui
import win32con
import pygetwindow as gw

class WindowCaptureService:
    def __init__(self):
        self.window_rect = None

    def get_window_rect(self, window_title_substring):
        # if self.window_rect:
        #     return self.window_rect

        for window in gw.getWindowsWithTitle(''):
            if window_title_substring.lower() in window.title.lower():
                hwnd = window._hWnd
                #win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                #win32gui.BringWindowToTop(hwnd)
                #win32gui.SetForegroundWindow(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                self.window_rect = rect
                return rect
        return None

    def screen_to_window(self, target_x, target_y, frame):
        x1, y1, x2, y2 = self.get_window_rect("Albion Online Client") #Albion Online Client / ForTests - Paint | TESTCASE - Paint
        window_width = x2 - x1
        window_height = y2 - y1
        frame_h, frame_w, _ = frame.shape

        win_x = x1 + int(target_x / frame_w * window_width)
        win_y = y1 + int(target_y / frame_h * window_height)

        return win_x, win_y

    def capture_window(self, window_title_substring):
        rect = self.get_window_rect(window_title_substring)
        if rect:
            x1, y1, x2, y2 = rect
            width, height = x2 - x1, y2 - y1

            with mss.mss() as sct:
                monitor = {"top": y1, "left": x1, "width": width, "height": height}
                sct_img = sct.grab(monitor)

                img = np.array(sct_img, dtype=np.uint8)
                if img is None or img.size == 0:
                    print("Ошибка: пустой кадр!")
                    return None

                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img
        return None