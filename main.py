from src.ffmpeg import FFMPEGController
from src.rciclient import KeeneticRCIClient
from src.signalpolicy import SignalPolicyEngine
from src.connection_checker import ConnectionChecker
from src.config import Config
from src.logger import LogType
from src.logger import GenericTextLogHandler
import time

from src.logger import get_logger
import signal
import sys

logger = get_logger(__name__, filename="main.csv", logType=LogType.BOTH, handler=GenericTextLogHandler)


def check_init_connection(config: Config = None):
    try:
        connection_check = ConnectionChecker(config)
        connection = connection_check.check_all()
        if connection:
            logger.info("[CONNECTION CHECKER] Начальные проверки соединения прошли успешно.")
        else:
            logger.error("[CONNECTION CHECKER] Ошибка при начальной проверке соединения.")
    except Exception as e:
        logger.error(f"[CONNECTION CHECKER] Ошибка во время начальной проверки соединения: {e}")


def graceful_shutdown(signum, frame):
    logger.info("[MAIN] Инициирована остановка.")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    config = Config()
    
    # Log configured devices
    logger.info(f"[MAIN] Сконфигурировано {len(config.device_configs)} устройств:")
    for device_name, device_config in config.device_configs.items():
        logger.info(f"[MAIN] - {device_name} → {device_config.output}")
    
    client = KeeneticRCIClient(config)
    if client.authenticate():
        check_init_connection(config)
        ffmpeg = FFMPEGController(config)
        policy = SignalPolicyEngine(client, ffmpeg, config)
        logger.info("[MAIN] Старт цикла обработки сигналов.")
        while True:
            signal_info = client.get_signal_info()
            logger.info(f"[SIGNAL POLICY] Получена информация о качестве соединения: {signal_info}")
            if signal_info:
                policy.evaluate_and_apply(signal_info)
            else:
                logger.error("[SIGNAL POLICY] Не удалось получить информацию о качестве соединения.")
                break
            time.sleep(int(config.timeout))
    else:
        logger.error("[MAIN] Аутентификация не удалась. Завершение работы.")
