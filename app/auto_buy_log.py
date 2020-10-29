from datetime import datetime
from logging import getLogger, StreamHandler, DEBUG, FileHandler, Formatter, INFO
import logging
import os, os.path
import pathlib


class Log():
    log_dir_name = ''
    filename = ''
    logger = getLogger(__name__)

    def __init__(self, logname, log_date: datetime):
        self.log_dir_name = os.path.dirname(__file__) + '/../log/{}_{}_{}/'.format(log_date.year, log_date.month, log_date.day)
        self.filename = self.log_dir_name + logname

    def create_log(self):
        if not os.path.isdir(self.log_dir_name):
            os.mkdir(self.log_dir_name)

        if not os.path.exists(self.filename):
            pathlib.Path(self.filename)

        logging.basicConfig(
            filename=self.filename,
            level=INFO,
        )
        formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler = StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
        file_handler = FileHandler(filename=self.filename)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)