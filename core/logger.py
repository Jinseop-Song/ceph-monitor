import logging
import os
from logging.handlers import RotatingFileHandler

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')

        # 콘솔 출력 (도커 로그용)
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        # 파일 출력 (logs 디렉토리 자동 생성)
        if not os.path.exists("logs"):
            os.makedirs("logs")
        fh = RotatingFileHandler("logs/ceph_monitor.log", maxBytes=10*1024*1024, backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger