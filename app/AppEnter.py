import random
import win32api
import win32con
from app.WindowCapture import WindowCaptureService
from app.PlayerStatus import PlayerStatusService
from app.WeightStatus import WeightStatusService
from app.YoloModel import YoloModelService
from app.MouseService import MouseService
from app.WaterCluster import WaterClusterService
from app.AnchorForMoovment import AnchorForMoovmentService
from app.GatheringService import GatheringService
from app.FishingService import FishingService
import cv2
import time

class AppEnterService:
    def __init__(self, bober_example_path, anchor_example_path):
        self.DEBUG = False
        self.stage = "Start"  # other stages will be implomented
        self.stage_interapter = None # for combat and weight

        self.trees_not_found = 0

        self.capture_service = WindowCaptureService()
        self.player_status = PlayerStatusService()
        self.yolo_model = YoloModelService()
        self.mouse_service = MouseService()
        self.water_cluster = WaterClusterService()
        self.anchor_service = AnchorForMoovmentService(anchor_example_path)
        self.weight_status = WeightStatusService(anchor_service=self.anchor_service)
        self.gathering_service = GatheringService()
        self.fishing_service = FishingService(bober_example_path)

        self.now = time.time()
        self.last_weight_check = self.now
        self.weight_icon = None

        self.last_player_icon = self.now
        self.player_icon = None

        self.last_yolo_check = self.now
        self.yolo_model_frame = None

        self.last_water_check = self.now
        self.water_cluster_frame = None

        self.start_gathering_time = self.now
        self.start_fishing_time = self.now

        self.first_pie = False
        self.eating_pie_time = self.now
        self.VK_E = 0x45

        self.found_gathering_history = []

    def press_e_key(self):
        win32api.keybd_event(self.VK_E, 0, 0, 0)
        time.sleep(random.uniform(0.1, 0.2))
        win32api.keybd_event(self.VK_E, 0, win32con.KEYEVENTF_KEYUP, 0)


    def run(self):
        while True:
            frame = self.capture_service.capture_window("Albion Online Client") #Albion Online Client / ForTests - Paint | TESTCASE - Paint
            if frame is None:
                print("Can't get acess to window")
                continue

            self.now = time.time()

            if self.stage == "Test":
                #self.fishing_service.controller(frame)
                self.water_cluster.process_water_cluster(frame)

            if not self.first_pie:
                self.press_e_key()
                self.first_pie = True
                time.sleep(random.uniform(3, 4))
                self.eating_pie_time = self.now

            if self.now - self.last_player_icon > 0.2:
                self.player_icon, founded_attack, confidenc_attack_ratio = self.player_status.process_player_status(frame)
                self.last_player_icon = self.now
                if founded_attack:
                    self.player_status.process()
                    self.stage_interapter = "Player Under Attack"
                    continue
                else:
                    if self.stage_interapter is not None:
                        self.stage = "Start"
                        self.stage_interapter = None

            if self.stage_interapter != "Player Under Attack":
                self.weight_icon, founded_overweight, confidenc_weight_ratio = self.weight_status.process_weight_status(frame)
                self.last_weight_check = self.now
                if founded_overweight:
                    self.weight_status.process()
                    self.stage_interapter = "Player Over Weight"
                else:
                    self.weight_status.ON_MOUNT = False
                    if self.stage_interapter is not None:
                        self.stage = "Start"
                        self.stage_interapter = None

            if self.stage == "Start" and self.stage_interapter is None:
                anchor_coordinates = self.anchor_service.process_found_anchor(frame)
                if anchor_coordinates:
                    self.mouse_service.aim_and_click_win32(anchor_coordinates[0], anchor_coordinates[1], frame, False)
                    time.sleep(random.uniform(4, 5))
                    self.stage = "Scan Tree"
                    continue

            if self.stage == "Scan Tree" and self.stage_interapter is None:
                if self.now - self.last_yolo_check > 1.0:
                    self.yolo_model_frame, tree_positions = self.yolo_model.process_yolo_model(frame)
                    self.last_yolo_check = self.now
                    trees = [p for p in tree_positions if p[2] == "treee_v4"]
                    if trees:
                        target_x, target_y, _ = trees[0]
                        self.mouse_service.aim_and_click_win32(target_x, target_y, frame, True)
                        time.sleep(random.uniform(3, 4))
                        self.start_gathering_time = self.now
                        self.stage = "Gathering"
                        trees = []
                    else:
                        self.trees_not_found += 1

                    if self.trees_not_found > random.uniform(6, 10):
                        self.stage = "Scan Water"
                        self.trees_not_found = 0

                    continue

            if self.stage == "Gathering" and self.stage_interapter is None:
                if self.now - self.start_gathering_time > random.uniform(14, 16):
                    self.stage = "Start"
                else:
                    found, ratio = self.gathering_service.find_gathering_indicator(frame)
                    if not found:
                        self.found_gathering_history.append(found)
                        if len(self.found_gathering_history) >= 3:
                            self.stage = "Start"
                    else:
                        self.found_gathering_history = []

            if self.stage == "Scan Water" and self.stage_interapter is None:
                if self.now - self.last_water_check > 1.0:
                    self.water_cluster_frame, water_position = self.water_cluster.process_water_cluster(frame)
                    if water_position:
                        self.mouse_service.aim_and_click_win32(water_position[0], water_position[1], frame, False)
                        time.sleep(random.uniform(3, 4))
                        self.start_fishing_time = self.now
                        self.stage = "Fishing"
                        frame = self.capture_service.capture_window("Albion Online Client")
                        self.water_cluster_frame, water_position = self.water_cluster.process_water_cluster(frame)
                        self.mouse_service.aim_and_click_win32(water_position[0], water_position[1], frame, False)

            if self.stage == "Fishing" and self.stage_interapter is None:
                if self.now - self.eating_pie_time > 1810:
                    self.press_e_key()
                    time.sleep(random.uniform(3, 4))
                    self.eating_pie_time = self.now

                if self.now - self.start_fishing_time > random.uniform(180, 260):
                    self.fishing_service.reset_state()
                    self.stage = "Start"
                else:
                    if self.fishing_service.state == "RESTART":
                        self.water_cluster_frame, water_position = self.water_cluster.process_water_cluster(frame)
                        if water_position:
                            self.mouse_service.aim_and_click_win32(water_position[0], water_position[1], frame, False)
                    self.fishing_service.controller(frame)

            if self.DEBUG:
                if self.player_icon is not None:
                    cv2.imshow("Char Icon", self.player_icon)
                if self.weight_icon is not None:
                    cv2.imshow("Weight Icon", self.weight_icon)
                if self.yolo_model_frame is not None:
                    cv2.imshow("(Live)", self.yolo_model_frame)
                if self.water_cluster_frame is not None:
                    cv2.imshow("Water Cluster", self.water_cluster_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()