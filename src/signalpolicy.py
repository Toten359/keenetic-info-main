from .rciclient import KeeneticRCIClient
from .ffmpeg import FFMPEGController
from datetime import datetime

from .config import Config
from .logger import LogType
from .logger import GenericTextLogHandler
from .logger import get_logger


logger = get_logger(__name__, filename="signalpolicy_log.csv", logType=LogType.FILE, handler=GenericTextLogHandler)


class SignalPolicyEngine:
    def __init__(self, client: KeeneticRCIClient, ffmpeg: FFMPEGController, config: Config):
        self.client = client
        self.ffmpeg = ffmpeg
        self.config = config

        base_profile = {"resolution": config.resolution, "bitrate": config.bitrate, "fps": config.fps}
        logger.info(f"[POLICY] Инициализация с базовым профилем: {base_profile}")
        # Degradation steps
        degradation_steps = config.degradation_steps
        if degradation_steps < 1:
            logger.error("[POLICY] Количество шагов деградации должно быть больше 0")
            raise ValueError("Количество шагов деградации должно быть больше 0")

        self.profiles = []
        for step in range(degradation_steps + 1):
            width, height = base_profile["resolution"].split("x")
            width = int(width) - step * (int(width) // degradation_steps)
            height = int(height) - step * (int(height) // degradation_steps)
            if width <= 1:
                width = 320
            if height <= 1:
                height = 240
            resolution = f"{width}x{height}"
            bitrate = f"{int(int(base_profile['bitrate'].split('k')[0]) * ((degradation_steps - step) / degradation_steps))}k"
            if int(bitrate.split('k')[0]) < 300:
                bitrate = "300k"
            fps = str(int(base_profile["fps"]) - step * 3 if int(base_profile["fps"]) - step * 3 > 0 else 1)
            if int(fps) < 10:
                fps = "12"
            self.profiles.append({"resolution": resolution, "bitrate": bitrate, "fps": fps})

        if not self.config.input_device:
            logger.info("[POLICY] Используется тестовый источник")
            self.ffmpeg.input_device = "testsrc"
        else:
            logger.info(f"[POLICY] Используется устройство ввода: {self.config.input_device}")
        logger.info(f"[POLICY] Инициализация завершена с профилями: {self.profiles}")

    def evaluate_and_apply(self, signal_data: dict):
        """
        Evaluates the signal-to-noise ratio (SNR) based on the provided signal data
        and applies the appropriate profile settings.

        Args:
            signal_data (dict): A dictionary containing signal information. Expected keys:
                - "rssi" (int): Received Signal Strength Indicator. Defaults to -100 if not provided.
                - "noise" (int): Noise level. Defaults to -100 if not provided.

        Behavior:
            - Calculates the SNR as the difference between RSSI and noise.
            - Logs the SNR, RSSI, and noise values with a timestamp.
            - Selects a profile based on the SNR value:
                - SNR < 5: Selects the first profile.
                - 5 <= SNR < 10: Selects the worst profile.
                - 30 <= SNR < 40: Selects the best profile.
                - SNR >= 40: Selects the sixth profile.
            - Logs the selected profile's resolution, bitrate, and frame rate.
            - Restarts the ffmpeg process with the selected profile if needed.

        Returns:
            None
        """
        # rssi = int(signal_data.get("rssi", -100))
        # noise = int(signal_data.get("noise", -100))
        rssi = 100
        noise = 50
        snr = rssi - noise
        logger.info(f"[SIGNAL INFO] SNR: {snr}, RSSI: {rssi}, NOISE: {noise}")


        degradation_steps = self.config.degradation_steps
        effective_snr = max(snr, 0)
        profile_index = degradation_steps - (effective_snr // 10)
        profile_index = max(0, min(degradation_steps, profile_index))
        profile = self.profiles[profile_index]
        self.ffmpeg.restart_if_needed(profile)
