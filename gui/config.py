from dataclasses import dataclass

@dataclass
class BotConfig:
    # Anchor Service
    anchor_threshold: float = 0.43
    anchor_color_ratio: float = 0.13
    stuck_limit: int = 30
    anchor_hex_color_orange = "#d3ce00"
    anchor_hex_color_blue = "#0a64b1"
    anchor_example_path = "MountHealthBar/MountHealthBar.png"
    anchor_debug: bool = False

    #Fishing Service
    missing_frame_limits: int = 2
    tolerance_for_bober: int = 45
    tolerance_for_bober_ratio: float = 0.0006
    bobber_example_path: str = "bobberExamples/bobberExample2.png"
    bober_color_hex: str = "#FF3F2D"
    fishing_debug: bool = False

    #Gathering Service
    tolerance_for_gathering: int = 35
    tolerance_for_gathering_ratio: float = 0.30
    gathering_debug: bool = False

    #Player Service
    tolerance_for_player: int = 35
    tolerance_for_player_ratio: float = 0.10
    player_color_hex: str = "#d0460d"
    player_debug: bool = False

    #Telegram Service
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


    debug: bool = False
