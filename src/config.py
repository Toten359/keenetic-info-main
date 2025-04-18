import configparser
import os

class DeviceConfig:
    def __init__(self, device_name, output_destination, resolution, bitrate, fps):
        self.device_name = device_name
        self.output = output_destination
        self.resolution = resolution
        self.bitrate = bitrate
        self.fps = fps

class Config:
    def __init__(self, config_path="main.conf"):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file {config_path} not found")
        self.config.read(config_path)
        
        # Router settings
        self.ip = self.config.get("Router", "ip_addr")
        self.login = self.config.get("Router", "login")
        self.password = self.config.get("Router", "password")
        
        # General settings
        self.timeout = self.config.get("settings", "timeout")
        self.logfile = self.config.get("settings", "logfile")
        self.connection_type = self.config.get("settings", "connection_type")
        
        # Profile settings
        self.resolution = self.config.get("Profile", "resolution")
        self.bitrate = self.config.get("Profile", "bitrate")
        self.fps = self.config.get("Profile", "fps")
        self.degradation_steps = int(self.config.get("Profile", "degradation_steps"))
        
        self.device_configs = {}
        input_device_entries = self.config.get("Profile", "input_devices").split(",")
        
        for entry in input_device_entries:
            if ":" in entry:
                device, output = entry.split(":", 1)
                self.device_configs[device] = DeviceConfig(
                    device_name=device,
                    output_destination=output,
                    resolution=self.resolution,
                    bitrate=self.bitrate,
                    fps=self.fps
                )
        
        self.ping_ip = self.config.get("connection_check", "ping_ip")
        self.curl_url = self.config.get("connection_check", "curl_url")
    
    def get_device_configs(self):
        return self.device_configs

