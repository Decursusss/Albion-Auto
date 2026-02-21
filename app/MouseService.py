import random
import win32api
import time
import win32con
import math
from app.WindowCapture import WindowCaptureService
import cv2

class MouseService:
    def __init__(self):
        self.window_capture = WindowCaptureService()

    def left_click(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.12))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def right_click(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.12))
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    def move_mouse_wind_relative(self, dest_x, dest_y, gravity=7, wind=9, min_wait=0.004, max_wait=0.015, max_step=12):
        vx = 0.0
        vy = 0.0

        while True:
            cur_x, cur_y = win32api.GetCursorPos()
            dx = dest_x - cur_x
            dy = dest_y - cur_y
            dist = math.hypot(dx, dy)

            if dist < 11:
                break

            nx = dx / dist
            ny = dy / dist

            # перпендикуляр
            px = -ny
            py = nx

            # боковой ветер
            vx += px * random.uniform(-wind, wind) * 0.12
            vy += py * random.uniform(-wind, wind) * 0.12

            # притяжение
            vx += nx * gravity
            vy += ny * gravity

            # трение
            vx *= 0.82
            vy *= 0.82

            # ограничение скорости
            speed = math.hypot(vx, vy)
            if speed > max_step:
                vx = vx / speed * max_step
                vy = vy / speed * max_step

            move_x = int(round(vx))
            move_y = int(round(vy))

            if move_x == 0 and move_y == 0:
                break


            win32api.mouse_event(
                win32con.MOUSEEVENTF_MOVE,
                move_x,
                move_y,
                0,
                0
            )

            time.sleep(random.uniform(min_wait, max_wait))

    def aim_and_click_win32(self, target_x, target_y, frame, first_click):
        win_x, win_y = self.window_capture.screen_to_window(target_x, target_y, frame)

        win_x += random.randint(-2, 2)
        win_y += random.randint(-2, 2)

        cv2.circle(frame, (target_x, target_y), 5, (0, 0, 255), -1)

        #win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0)

        self.move_mouse_wind_relative(
            win_x,
            win_y,
            gravity=random.uniform(3, 5),
            wind=random.uniform(15, 20),
            max_step=random.randint(24, 30)
        )

        #win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0)

        if first_click:
            self.left_click()
        else:
            self.right_click()
        time.sleep(random.uniform(0.1, 0.25))