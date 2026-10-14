import os
import sys

from loguru import logger

def setup_logger():
    logger.remove()

    logger.add(
        sys.stdout,
        level='TRACE',
        colorize=True,
        format='{time} | <cyan><bold>{name}</bold></cyan>:<green>{function}</green>:<magenta>{line}</magenta> - <level>{message}</level>',
        backtrace=False,
        diagnose=False,
        enqueue=True
    )

    os.makedirs("logs", exist_ok=True)
    logger.add(
        'logs/app_{time}.log',
        format='{time} | <cyan><bold>{name}</bold></cyan>:<green>{function}</green>:<magenta>{line}</magenta> - <level>{message}</level>',
        retention='30 days',
        level='DEBUG',
    )