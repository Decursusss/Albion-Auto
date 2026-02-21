import cv2
import numpy as np

class GatheringService:
    def __init__(self):
        self.tolerance_for_gathering = 35
        self.tolerance_for_gathering_ration_min = 0.30

        self.debug = False
        self.log = None

    def debug_log(self, message):
        if self.debug and self.log is not None:
            self.log(f"[Gathering Log] {message}")

    def crop_center(self, frame, crop_w=250, crop_h=40):
        h, w, _ = frame.shape

        center_x = w // 2 - 91
        center_y = h // 2 + 160

        x1 = max(center_x - crop_w // 2, 0)
        y1 = max(center_y - crop_h // 2, 0)
        x2 = min(center_x + crop_w // 2, w)
        y2 = min(center_y + crop_h // 2, h)

        return frame[y1:y2, x1:x2]

    def check_color_level(self, frame, hex_color="#858483", tolerance=20, min_ratio=0.1):
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

    def find_gathering_indicator(self, frame):
        cropped = self.crop_center(frame, 7, 55)
        found, ratio = self.check_color_level(cropped, hex_color="#31556D", tolerance=self.tolerance_for_gathering, min_ratio=self.tolerance_for_gathering_ration_min) #353436
        self.debug_log(f"Gathering Icon {found} | Current Ratio {ratio}")
        #cv2.imshow("MASK", cropped)
        return found, ratio