import subprocess

from .config import Config, DeviceConfig

from .logger import get_logger
from .logger import LogType
from .logger import GenericTextLogHandler

logger = get_logger(__name__, filename="ffmpeg_log.csv", logType=LogType.BOTH, handler=GenericTextLogHandler)


class FFMPEGInstance:
    def __init__(self, device_config):
        self.device_name = device_config.device_name
        self.output = device_config.output
        self.resolution = device_config.resolution
        self.bitrate = device_config.bitrate
        self.fps = device_config.fps
        self.process = None
        self.current_profile = None
        logger.info(
            f"[FFMPEG] Инициализация устройства {self.device_name} с разрешением: {self.resolution}, "
            f"битрейтом: {self.bitrate}, частотой кадров: {self.fps}, выходом: {self.output}"
        )
        
    def build_command(self, profile: dict[str, str]) -> str:
        if self.device_name == "testsrc":
            return (
                f"ffmpeg -f lavfi -i testsrc=rate={profile['fps']}:size={profile['resolution']} "
                f"-vcodec libx264 -preset ultrafast -b:v {profile['bitrate']} -f mpegts {self.output}"
            )
        else:
            return (
                f"ffmpeg -f v4l2 -framerate {profile['fps']} -video_size {profile['resolution']} "
                f"-i {self.device_name} -b:v {profile['bitrate']} -f mpegts {self.output}"
            )
    
    def start(self, profile):
        if self.process:
            self.stop()
        cmd = self.build_command(profile)
        self.process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if self.process.poll() is not None:
            logger.error(f"[FFMPEG] Ошибка запуска процесса для {self.device_name}: {self.process.stderr.read().decode()}")
            return
        logger.info(f"[FFMPEG] Процесс запущен для {self.device_name} с командой: {cmd}")
        self.current_profile = profile
        
    def stop(self):
        if self.process:
            logger.info(f"[FFMPEG] Остановка процесса для {self.device_name}")
            self.process.terminate()
            self.process.wait()
            self.process = None
    
    def restart_if_needed(self, new_profile):
        if new_profile != self.current_profile:
            logger.info(f"[FFMPEG] Профиль изменился для {self.device_name}: {self.current_profile} → {new_profile}")
            self.start(new_profile)


class FFMPEGController:
    def __init__(self, config: Config):
        self.instances = {}
        
        for device_name, device_config in config.device_configs.items():
            self.instances[device_name] = FFMPEGInstance(device_config)
        
        logger.info(f"[FFMPEG] Инициализировано {len(self.instances)} устройств")
        logger.info("[FFMPEG] Инициализация завершена")

    def start(self, profile):
        """Start all FFMPEG instances with the given profile"""
        for device_name, instance in self.instances.items():
            instance.start(profile)

    def stop(self):
        """Stop all FFMPEG instances"""
        for device_name, instance in self.instances.items():
            instance.stop()

    def restart_if_needed(self, new_profile):
        """Restart all FFMPEG instances if the profile has changed"""
        for device_name, instance in self.instances.items():
            instance.restart_if_needed(new_profile)
