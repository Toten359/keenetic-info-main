import requests
import hashlib
from .config import Config


from .logger import get_logger
from .logger import LogType
from .logger import GenericTextLogHandler


logger_text = get_logger(__name__, filename="RCI_log.csv", logType=LogType.FILE, handler=GenericTextLogHandler)

class KeeneticRCIClient:
    def __init__(self, config: Config):
        self.session = requests.session()
        self.ip = config.ip
        self.login = config.login
        self.password = config.password
        self.timeout = config.timeout
        self.logfile = config.logfile
        logger_text.info(
            f"[Keenetic] Инициализация сессии с таймаутом: {self.timeout} и файлом журнала: {self.logfile}"
        )
        logger_text.info("[Keenetic] Конфигурация загружена успешно.")
        logger_text.info("[Keenetic] Инициализация сессии...")

    def _request(self, path, post=None):
        url = f"http://{self.ip}/{path}"
        return self.session.post(url, json=post) if post else self.session.get(url)

    def authenticate(self) -> bool:
        r = self._request("auth")
        if r.status_code == 401:
            realm = r.headers.get("X-NDM-Realm", "")
            challenge = r.headers.get("X-NDM-Challenge", "")
            md5 = hashlib.md5(f"{self.login}:{realm}:{self.password}".encode()).hexdigest()
            sha256 = hashlib.sha256((challenge + md5).encode()).hexdigest()
            r = self._request("auth", {"login": self.login, "password": sha256})
            if r.status_code == 200:
                logger_text.info("[Keenetic] Аутентификация успешна")
                return True
            else:
                logger_text.error(f"[Keenetic] Ошибка аутентификации: {r.status_code}")
                return False
        elif r.status_code == 200:
            logger_text.info("[Keenetic] Уже авторизован")
            return True
        else:
            logger_text.error(f"[Keenetic] Ошибка аутентификации: {r.status_code}")
        return False

    def get_connected_devices(self):
        if not self.authenticate():
            logger_text.error("[Keenetic] Failed to authenticate before getting connected devices")
            return None
            
        r = self._request("rci/show/ip/hotspot")
        try:
            data = r.json()
            logger_text.info("[Keenetic] Successfully retrieved connected devices information")
            logger_text.info(data)
            return data
        except Exception as e:
            logger_text.error(f"[Keenetic] Error retrieving connected devices: {str(e)}")
            return None

    def get_signal_info(self):
        if self.get_device_type() == "wifi":
            return self.get_wifi_info()
        elif self.get_device_type() == "usb_modem":
            return self.get_usb_info()

    def get_usb_info(self):
        pass

    def get_device_type(self) -> str:
        return "wifi"

    def get_wifi_info(self):
        r = self._request("rci/show/interface")
        try:
            data = r.json()
        except:
            return None
        wifi_info = data.get("WifiMaster0/WifiStation0")
        if not wifi_info:
            logger_text.error("[Keenetic] Информация о Wi-Fi не найдена")
            return None
        return wifi_info