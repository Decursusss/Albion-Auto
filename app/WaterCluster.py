import cv2
import numpy as np

class WaterClusterService:
    def __init__(self):
        self.water_colors = np.array([[31, 18, 26], [23, 12, 17], [51, 37, 53]], dtype=np.uint8)

    def is_water_mask(self, frame, tolerance=15):
        mask = np.zeros(frame.shape[:2], dtype=bool)
        for wc in self.water_colors:
            diff = np.abs(frame.astype(int) - wc.reshape(1, 1, 3))
            mask |= np.all(diff <= tolerance, axis=2)
        return mask.astype(np.uint8)

    def find_largest_water_cluster(self, frame, min_area=50):
        water_mask = self.is_water_mask(frame) * 255

        kernel = np.ones((3, 3), np.uint8)
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(water_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < min_area:
            return None, None

        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None, largest
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        return (cx, cy), largest

    def process_water_cluster(self, frame):
        vis = frame.copy()
        center, contour = self.find_largest_water_cluster(frame)
        if contour is not None:
            cv2.drawContours(vis, [contour], -1, (0, 255, 0), 2)
        if center is not None:
            cv2.circle(vis, center, 5, (0, 0, 255), -1)
        #cv2.imshow("vis", vis)
        return vis, center