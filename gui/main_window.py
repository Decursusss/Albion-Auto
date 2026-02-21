from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDoubleSpinBox, QSpinBox, QTextEdit, QCheckBox, QGroupBox, QTabWidget, QLineEdit, QColorDialog, QFileDialog
)
from PySide6.QtGui import QColor, QPixmap
from gui.config import BotConfig
from gui.worker import BotWorker

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Albion Control Panel")
        self.resize(420, 520)

        self.config = BotConfig()
        self.worker = None

        layout = QVBoxLayout(self)

        #Anchor settings
        anchor_box = QGroupBox("Anchor Service")
        a_layout = QVBoxLayout()

        self.anchor_threshold = QDoubleSpinBox()
        self.anchor_threshold.setDecimals(2)
        self.anchor_threshold.setRange(0, 1)
        self.anchor_threshold.setSingleStep(0.01)
        self.anchor_threshold.setValue(self.config.anchor_threshold)

        self.anchor_color_ratio = QDoubleSpinBox()
        self.anchor_color_ratio.setDecimals(2)
        self.anchor_color_ratio.setRange(0, 1)
        self.anchor_color_ratio.setSingleStep(0.01)
        self.anchor_color_ratio.setValue(self.config.anchor_color_ratio)

        self.stuck_limit = QSpinBox()
        self.stuck_limit.setRange(10, 500)
        self.stuck_limit.setSingleStep(1)
        self.stuck_limit.setValue(self.config.stuck_limit)

        self.anchor_debug = QCheckBox()
        self.anchor_debug.setChecked(self.config.anchor_debug)

        self.anchor_color_btn_one = QPushButton()
        self.anchor_color_btn_one.setFixedHeight(30)
        self.anchor_color_btn_one.setText("Anchor Color To Found")
        self.current_anchor_one_color = QColor(self.config.anchor_hex_color_orange)

        def update_anchor_color_one_button():
            self.anchor_color_btn_one.setStyleSheet(
                f"background-color: {self.current_anchor_one_color.name()};"
            )

        update_anchor_color_one_button()

        def select_anchor_one_color():
            color = QColorDialog.getColor(self.current_anchor_one_color, self)

            if color.isValid():
                self.current_anchor_one_color = color
                update_anchor_color_one_button()

        self.anchor_color_btn_one.clicked.connect(select_anchor_one_color)

        self.anchor_color_btn_two = QPushButton()
        self.anchor_color_btn_two.setFixedHeight(30)
        self.anchor_color_btn_two.setText("Anchor Color To Found")
        self.current_anchor_two_color = QColor(self.config.anchor_hex_color_blue)

        def update_anchor_two_color_button():
            self.anchor_color_btn_two.setStyleSheet(
                f"background-color: {self.current_anchor_two_color.name()};"
            )

        update_anchor_two_color_button()

        def select_anchor_two_color():
            color = QColorDialog.getColor(self.current_anchor_two_color, self)

            if color.isValid():
                self.current_anchor_two_color = color
                update_anchor_two_color_button()

        self.anchor_color_btn_two.clicked.connect(select_anchor_two_color)

        self.anchor_path_edit = QLineEdit()
        self.anchor_path_edit.setText(self.config.anchor_example_path)

        self.anchor_preview = QLabel()
        self.anchor_preview.setFixedSize(320, 30)
        self.anchor_preview.setStyleSheet("border: 1px solid gray;")
        self.anchor_preview.setScaledContents(True)

        self.select_anchor_btn = QPushButton("Select Anchor Template")

        def select_anchor_template():
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Anchor Template",
                "",
                "Images (*.png *.jpg *.jpeg)"
            )

            if file_path:
                self.anchor_path_edit.setText(file_path)
                pixmap = QPixmap(file_path)
                self.anchor_preview.setPixmap(pixmap)

        self.select_anchor_btn.clicked.connect(select_anchor_template)
        pixmap = QPixmap(self.anchor_path_edit.text())
        self.anchor_preview.setPixmap(pixmap)

        a_layout.addWidget(QLabel("Template threshold"))
        a_layout.addWidget(self.anchor_threshold)
        a_layout.addWidget(QLabel("Anchor color ratio"))
        a_layout.addWidget(self.anchor_color_ratio)
        a_layout.addWidget(QLabel("Anchor stuck limit"))
        a_layout.addWidget(self.stuck_limit)
        a_layout.addWidget(QLabel("Anchor color to found"))
        a_layout.addWidget(self.anchor_color_btn_one)
        a_layout.addWidget(QLabel("Anchor color not need"))
        a_layout.addWidget(self.anchor_color_btn_two)
        a_layout.addWidget(QLabel("Anchor Template Path"))
        a_layout.addWidget(self.anchor_path_edit)
        a_layout.addWidget(self.select_anchor_btn)
        a_layout.addWidget(self.anchor_preview)
        a_layout.addWidget(QLabel("Anchor debug mode"))
        a_layout.addWidget(self.anchor_debug)
        anchor_box.setLayout(a_layout)

        #Fishing settings
        fishing_box = QGroupBox("Fishing Service")
        fishing_layout = QVBoxLayout()

        self.mising_frame_limits = QSpinBox()
        self.mising_frame_limits.setRange(1, 30)
        self.mising_frame_limits.setSingleStep(1)
        self.mising_frame_limits.setValue(self.config.missing_frame_limits)

        self.tolerance_for_bober = QSpinBox()
        self.tolerance_for_bober.setRange(1, 100)
        self.tolerance_for_bober.setSingleStep(1)
        self.tolerance_for_bober.setValue(self.config.tolerance_for_bober)

        self.tolerance_for_bober_ratio = QDoubleSpinBox()
        self.tolerance_for_bober_ratio.setDecimals(4)
        self.tolerance_for_bober_ratio.setRange(0.0001, 1)
        self.tolerance_for_bober_ratio.setSingleStep(0.0001)
        self.tolerance_for_bober_ratio.setValue(self.config.tolerance_for_bober_ratio)

        self.bobber_path_edit = QLineEdit()
        self.bobber_path_edit.setText(self.config.bobber_example_path)

        self.bobber_preview = QLabel()
        self.bobber_preview.setFixedSize(40, 40)
        self.bobber_preview.setStyleSheet("border: 1px solid gray;")
        self.bobber_preview.setScaledContents(True)

        self.select_bobber_btn = QPushButton("Select Bobber Template")

        def select_bobber_template():
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Bobber Template",
                "",
                "Images (*.png *.jpg *.jpeg)"
            )

            if file_path:
                self.bobber_path_edit.setText(file_path)
                pixmap = QPixmap(file_path)
                self.bobber_preview.setPixmap(pixmap)

        self.select_bobber_btn.clicked.connect(select_bobber_template)
        pixmap = QPixmap(self.bobber_path_edit.text())
        self.bobber_preview.setPixmap(pixmap)

        self.fishing_debug = QCheckBox()
        self.fishing_debug.setChecked(self.config.fishing_debug)

        self.bober_color_btn = QPushButton()
        self.bober_color_btn.setFixedHeight(30)
        self.bober_color_btn.setText("Bobber Color")
        self.current_bober_color = QColor(self.config.bober_color_hex)
        def update_color_button():
            self.bober_color_btn.setStyleSheet(
                f"background-color: {self.current_bober_color.name()};"
            )
        update_color_button()

        def select_bober_color():
            color = QColorDialog.getColor(self.current_bober_color, self)

            if color.isValid():
                self.current_bober_color = color
                update_color_button()
        self.bober_color_btn.clicked.connect(select_bober_color)

        fishing_layout.addWidget(QLabel("Missing Frame Hook"))
        fishing_layout.addWidget(self.mising_frame_limits)
        fishing_layout.addWidget(QLabel("Tolerance For Bober"))
        fishing_layout.addWidget(self.tolerance_for_bober)
        fishing_layout.addWidget(QLabel("Tolerance Ratio For Bober"))
        fishing_layout.addWidget(self.tolerance_for_bober_ratio)
        fishing_layout.addWidget(QLabel("Bober Color"))
        fishing_layout.addWidget(self.bober_color_btn)
        fishing_layout.addWidget(QLabel("Bobber Template Path"))
        fishing_layout.addWidget(self.bobber_path_edit)
        fishing_layout.addWidget(self.select_bobber_btn)
        fishing_layout.addWidget(self.bobber_preview)
        fishing_layout.addWidget(QLabel("Fishing Debug Mode"))
        fishing_layout.addWidget(self.fishing_debug)
        fishing_box.setLayout(fishing_layout)

        #Gathering Settings
        gathering_box = QGroupBox("Gathering Service")
        gathering_layout = QVBoxLayout()

        self.tolerance_for_gathering = QSpinBox()
        self.tolerance_for_gathering.setRange(1, 100)
        self.tolerance_for_gathering.setSingleStep(1)
        self.tolerance_for_gathering.setValue(self.config.tolerance_for_gathering)

        self.tolerance_for_gathering_ratio = QDoubleSpinBox()
        self.tolerance_for_gathering_ratio.setDecimals(2)
        self.tolerance_for_gathering_ratio.setRange(0, 1.0)
        self.tolerance_for_gathering_ratio.setSingleStep(0.01)
        self.tolerance_for_gathering_ratio.setValue(self.config.tolerance_for_gathering_ratio)

        self.gathering_debug = QCheckBox()
        self.gathering_debug.setChecked(self.config.gathering_debug)

        gathering_layout.addWidget(QLabel("Gathering Indictor Tolerance"))
        gathering_layout.addWidget(self.tolerance_for_gathering)
        gathering_layout.addWidget(QLabel("Gathering Indictor Tolerance Ratio"))
        gathering_layout.addWidget(self.tolerance_for_gathering_ratio)
        gathering_layout.addWidget(QLabel("Gathering Debug Mode"))
        gathering_layout.addWidget(self.gathering_debug)
        gathering_box.setLayout(gathering_layout)

        #Player Settings
        player_box = QGroupBox("Player Service")
        player_layout = QVBoxLayout()

        self.tolerance_for_player = QSpinBox()
        self.tolerance_for_player.setRange(1, 100)
        self.tolerance_for_player.setSingleStep(1)
        self.tolerance_for_player.setValue(self.config.tolerance_for_player)

        self.tolerance_for_player_ratio = QDoubleSpinBox()
        self.tolerance_for_player_ratio.setDecimals(2)
        self.tolerance_for_player_ratio.setRange(0, 1)
        self.tolerance_for_player_ratio.setSingleStep(0.01)
        self.tolerance_for_player_ratio.setValue(self.config.tolerance_for_player_ratio)

        self.player_color_btn_one = QPushButton()
        self.player_color_btn_one.setFixedHeight(30)
        self.player_color_btn_one.setText("Player Color Indicator")
        self.current_player_color = QColor(self.config.player_color_hex)

        def update_player_color_button():
            self.player_color_btn_one.setStyleSheet(
                f"background-color: {self.current_player_color.name()};"
            )

        update_player_color_button()

        def select_player_color():
            color = QColorDialog.getColor(self.current_player_color, self)

            if color.isValid():
                self.current_player_color = color
                update_player_color_button()

        self.player_color_btn_one.clicked.connect(select_player_color)

        self.player_debug = QCheckBox()
        self.player_debug.setChecked(self.config.player_debug)

        player_layout.addWidget(QLabel("Player Indicator Tolerance"))
        player_layout.addWidget(self.tolerance_for_player)
        player_layout.addWidget(QLabel("Player Indicator Tolerance Ratio"))
        player_layout.addWidget(self.tolerance_for_player_ratio)
        player_layout.addWidget(QLabel("Player Color Indicator"))
        player_layout.addWidget(self.player_color_btn_one)
        player_layout.addWidget(QLabel("Player Debug Mode"))
        player_layout.addWidget(self.player_debug)
        player_box.setLayout(player_layout)

        #Telegram Service
        telegram_box = QGroupBox("Telegram Service")
        telegram_layout = QVBoxLayout()
        self.telegram_bot_token = QLineEdit()
        self.telegram_bot_token.setText(self.config.telegram_bot_token)
        self.telegram_bot_token.setEchoMode(QLineEdit.Password)

        self.telegram_chat_id = QLineEdit()
        self.telegram_chat_id.setText(self.config.telegram_chat_id)
        self.telegram_chat_id.setEchoMode(QLineEdit.Password)

        def toggle_password():
            if self.telegram_bot_token.echoMode() == QLineEdit.Password:
                self.telegram_bot_token.setEchoMode(QLineEdit.Normal)
                self.telegram_chat_id.setEchoMode(QLineEdit.Normal)
            else:
                self.telegram_bot_token.setEchoMode(QLineEdit.Password)
                self.telegram_chat_id.setEchoMode(QLineEdit.Password)

        self.button_show = QPushButton("👁")
        self.button_show.clicked.connect(toggle_password)

        telegram_layout.addWidget(QLabel("Telegram Bot Token"))
        telegram_layout.addWidget(self.telegram_bot_token)
        telegram_layout.addWidget(QLabel("Telegram Chat ID"))
        telegram_layout.addWidget(self.telegram_chat_id)
        telegram_layout.addWidget(self.button_show)
        telegram_box.setLayout(telegram_layout)

        # Debug
        self.debug_checkbox = QCheckBox("Debug mode")

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start")
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        # Logs
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)

        tabs = QTabWidget()
        tabs.addTab(anchor_box, "Anchor")
        tabs.addTab(fishing_box, "Fishing")
        tabs.addTab(gathering_box, "Gathering")
        tabs.addTab(player_box, "Player")

        layout.addWidget(telegram_box)
        layout.addWidget(tabs)
        layout.addWidget(self.debug_checkbox)
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("📜 Logs"))
        layout.addWidget(self.logs)

        #Signals
        self.start_btn.clicked.connect(self.start_bot)
        self.stop_btn.clicked.connect(self.stop_bot)

    def start_bot(self):
        self.config.anchor_threshold = self.anchor_threshold.value()
        self.config.anchor_color_ratio = self.anchor_color_ratio.value()
        self.config.stuck_limit = self.stuck_limit.value()
        self.config.anchor_hex_color_orange = self.current_anchor_one_color.name()
        self.config.anchor_hex_color_blue = self.current_anchor_two_color.name()
        self.config.anchor_example_path = self.anchor_path_edit.text()
        self.config.anchor_debug = self.anchor_debug.isChecked()

        self.config.missing_frame_limits = self.mising_frame_limits.value()
        self.config.tolerance_for_bober = self.tolerance_for_bober.value()
        self.config.tolerance_for_bober_ratio = self.tolerance_for_bober_ratio.value()
        self.config.bober_color_hex = self.current_bober_color.name()
        self.config.bobber_example_path = self.bobber_path_edit.text()
        self.config.fishing_debug = self.fishing_debug.isChecked()

        self.config.tolerance_for_gathering = self.tolerance_for_gathering.value()
        self.config.tolerance_for_gathering_ratio = self.tolerance_for_gathering_ratio.value()
        self.config.gathering_debug = self.gathering_debug.isChecked()

        self.config.tolerance_for_player = self.tolerance_for_player.value()
        self.config.tolerance_for_player_ratio = self.tolerance_for_player_ratio.value()
        self.config.player_color_hex = self.current_player_color.name()
        self.config.player_debug = self.player_debug.isChecked()

        self.config.telegram_bot_token = self.telegram_bot_token.text()
        self.config.telegram_chat_id = self.telegram_chat_id.text()

        self.config.debug = self.debug_checkbox.isChecked()

        self.worker = BotWorker(self.config)
        self.worker.log.connect(self.logs.append)
        self.worker.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_bot(self):
        if self.worker:
            self.worker.stop()
            self.logs.append("🛑 stopped")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
