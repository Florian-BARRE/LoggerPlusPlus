from loggerplusplus import loggerplusplus, LoggerClass


class Worker(LoggerClass):
    def __init__(self, x=1):
        self.x = x
        LoggerClass.__init__(self)

    def do_work(self):
        self.logger.debug("Starting work in class Worker")
        self.logger.info("Worker finished successfully")


def external_function():
    loggerplusplus.bind(identifier="EXTFUNC").warning("External function was called!")
