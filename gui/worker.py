from PySide6.QtCore import QThread, Signal
from app.AppEnter import AppEnterService

class BotWorker(QThread):
    log = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.bot = None
        self.running = True

    def run(self):
        self.bot = AppEnterService(self.config.bobber_example_path, self.config.anchor_example_path)
        self.bot.first_pie = False

        #Mapping parameters
        #Anchor service
        self.bot.DEBUG = self.config.debug
        self.bot.anchor_service.threshold = self.config.anchor_threshold
        self.bot.anchor_service.stuck_limit = self.config.stuck_limit
        self.bot.anchor_service.hex_color_blue = self.config.anchor_hex_color_blue
        self.bot.anchor_service.hex_color_orange = self.config.anchor_hex_color_orange
        #Init Acnhor Log
        self.bot.anchor_service.log = self.log.emit
        self.bot.anchor_service.debug = self.config.anchor_debug

        #Fishing Service
        self.bot.fishing_service.tolerance_for_bobber = self.config.tolerance_for_bober
        self.bot.fishing_service.tolerance_ration_min_value = self.config.tolerance_for_bober_ratio
        self.bot.fishing_service.MISSING_FRAMES_LIMIT = self.config.missing_frame_limits
        #Init Fishing Log
        self.bot.fishing_service.log = self.log.emit
        self.bot.fishing_service.debug = self.config.fishing_debug

        #Gathering Service
        self.bot.gathering_service.tolerance_for_gathering = self.config.tolerance_for_gathering
        self.bot.gathering_service.tolerance_for_gathering_ration_min = self.config.tolerance_for_gathering_ratio
        #Init Gathering Log
        self.bot.gathering_service.log = self.log.emit
        self.bot.gathering_service.debug = self.config.gathering_debug

        #Player Icon Service
        self.bot.player_status.tolerance_for_player_icon = self.config.tolerance_for_player
        self.bot.player_status.tolerance_for_player_icon_ratio_min_value = self.config.tolerance_for_player_ratio
        self.bot.player_status.hex_color_orange = self.config.player_color_hex
        #Init Player Log
        self.bot.player_status.log = self.log.emit
        self.bot.player_status.debug = self.config.player_debug

        #Telegram Service
        self.bot.weight_status.TELEGRAM_TOKEN = self.config.telegram_bot_token
        self.bot.weight_status.CHAT_ID = self.config.telegram_chat_id
        self.bot.anchor_service.weight_status_service.TELEGRAM_TOKEN = self.config.telegram_bot_token
        self.bot.anchor_service.weight_status_service.CHAT_ID = self.config.telegram_chat_id

        self.log.emit("🚀 started")
        try:
            self.bot.stage = "Start"
            self.bot.run()
        except Exception as e:
            self.log.emit(f"❌ Error: {e}")

    def stop(self):
        self.running = False
        self.terminate()
