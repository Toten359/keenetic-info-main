import subprocess
import shlex

from .config import Config

from .logger import get_logger
from .logger import LogType
from .logger import GenericTextLogHandler

logger = get_logger(__name__, logType=LogType.CONSOLE, handler=GenericTextLogHandler)

from ipaddress import AddressValueError, ip_address


class ConnectionChecker:
    def __init__(self, config: Config = None):
        self.ip_address = None
        self.url = None
        if config:
            self.ip_address = config.ping_ip
            self.url = config.curl_url
        else:
            self.ip_address = None
            self.url = None
        logger.info(f"[CONNECTION CHECKER] Инициализация завершена с IP: {self.ip_address}, URL: {self.url}")

        try:
            self.ip_address = ip_address(self.ip_address)
        except AddressValueError:
            logger.error(f"Некорректный IP адрес: {self.ip_address}")
            raise ValueError("Некорректный IP адрес")

    def check_ping(self):
        try:
            cmd = f"ping -c 3 -W 2 {self.ip_address}"
            result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Проверка ping не удалась: {e}")
            return False

    def check_curl(self) -> bool:
        if not self.url:
            logger.error("Некорректный URL для проверки curl")
            return False
        try:
            cmd = f"curl -s -I --connect-timeout 3 {self.url}"
            result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("HTTP/"):
                        status_part = line.split(" ")[1]
                        status_code = int(status_part)
                        return 200 <= status_code < 400
            return False
        except Exception as e:
            logger.error(f"Проверка curl не удалась: {e}")
            return False

    def check_all(self) -> dict[str, bool]:
        return {self.check_ping() & self.check_curl()}
