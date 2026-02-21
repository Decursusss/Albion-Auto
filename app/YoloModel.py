import cv2
from ultralytics import YOLO

class YoloModelService:
    def __init__(self):
        self.model = YOLO("../Models/OwnModelTest_v1.pt") #current best OwnModel_v4.pt | OwnModelTest_v1.pt

    def find_tree(self, frame):
        results = self.model(frame, conf=0.7, imgsz=640, verbose=False)
        positions = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())

                class_name = self.model.names[class_id]

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"{class_name} {confidence:.2f}",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

                positions.append(((x1 + x2) // 2, (y1 + y2) // 2, class_name))

        return positions, frame

    def process_yolo_model(self, frame):
        position, current_frame = self.find_tree(frame)

        return current_frame, position