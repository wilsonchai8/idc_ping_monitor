import logging
import logging.handlers


class LogHandler(object):
    FILE_NAME = None
    def __init__(self, name):
        self.handler = logging.handlers.RotatingFileHandler('/tmp/idc_ping_monitor.log' , maxBytes = 1024*1024 , backupCount = 5)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        self.handler.setFormatter(formatter)
        self.logger = logging.getLogger(name)
        self.logger.addHandler(self.handler)

    def __call__(self , func , *args , **kwargs):
        if func.__name__ == 'info' :
            self.logger.setLevel(logging.INFO)
            log_record = func(*args , **kwargs)
            self.logger.info(log_record)
            self.logger.removeHandler(self.handler)
