import configparser
import requests
import hashlib
import json
import time
import logging
import csv
import os
from datetime import datetime
import csv

from datetime import datetime


class CsvSignalLogHandler(logging.Handler):
    def __init__(self, filename="keenetic_signal_log.csv"):
        super().__init__()
        self.filename = filename
        self._init_file()

    def _init_file(self):
        new_file = not os.path.exists(self.filename)
        self.file = open(self.filename, "a", newline="")
        self.writer = csv.writer(self.file)
        if new_file:
            self.writer.writerow(["timestamp", "ssid", "rssi", "noise", "rate_mbps", "quality_percent"])

    def emit(self, record):
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = record.msg
            self.writer.writerow(
                [ts, data.get("ssid"), data.get("rssi"), data.get("noise"), data.get("rate"), data.get("quality")]
            )
            self.file.flush()
        except Exception as e:
            self.handleError(record)


class KeeneticRCIClient:
    def __init__(self, config_path="keenetic.conf"):
        self.session = requests.session()
        self._load_config(config_path)

    def _load_config(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        self.ip = config["Router"]["ip_addr"]
        self.login = config["Router"]["login"]
        self.password = config["Router"]["passw"]

    def _request(self, path, post=None):
        url = f"http://{self.ip}/{path}"
        if post:
            return self.session.post(url, json=post)
        return self.session.get(url)

    def authenticate(self):
        r = self._request("auth")
        if r.status_code == 401:
            challenge = r.headers.get("X-NDM-Challenge")
            realm = r.headers.get("X-NDM-Realm")
            if not challenge or not realm:
                raise Exception("Не получен challenge/realm")
            md5 = hashlib.md5(f"{self.login}:{realm}:{self.password}".encode()).hexdigest()
            sha256 = hashlib.sha256((challenge + md5).encode()).hexdigest()
            resp = self._request("auth", {"login": self.login, "password": sha256})
            return resp.status_code == 200
        return r.status_code == 200

    def get_wifi_info(self):
        r = self._request("rci/show/interface")
        try:
            data = r.json()
        except:
            return None
        return data.get("WifiMaster0/WifiStation0")


class WifiSignalLogger:
    def __init__(self, keenetic_client, logger=None):
        self.client = keenetic_client
        self.logger = logger

    def rssi_to_quality(self, rssi):
        if rssi is None:
            return None
        return max(0, min(100, 2 * (int(rssi) + 100)))

    def log(self):
        info = self.client.get_wifi_info()
        if not info:
            print("❌ Нет данных от роутера")
            return

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rssi = info.get("rssi")
        noise = info.get("noise")
        rate = info.get("rate")
        ssid = info.get("ssid")
        quality = self.rssi_to_quality(rssi)

        log_data = {"ssid": ssid, "rssi": rssi, "noise": noise, "rate": rate, "quality": quality}
        if not quality:
            quality = 0
        if not rssi:
            rssi = 0
        if not noise:
            noise = 0
        print(f"[{ts}] SSID: {ssid} | RSSI: {rssi} dBm | Noise: {noise} dBm | Rate: {rate} Mbps | Quality: {quality}%")

        if self.logger:
            self.logger.info(log_data)


if __name__ == "__main__":
    client = KeeneticRCIClient()
    if client.authenticate():
        logger = logging.getLogger("keenetic")
        logger.setLevel(logging.INFO)
        logger.addHandler(CsvSignalLogHandler())

        signal_logger = WifiSignalLogger(client, logger=logger)
        while True:
            signal_logger.log()
            time.sleep(1)

    else:
        print("❌ Авторизация не удалась")
