import logging
import os
import pathlib
import sys
from public import globvalue
from public.globvalue import CUSTOM_PATH
#LOG_PATH


class MyLogger(logging.Logger):
    def __init__(self,absdirpath:str=CUSTOM_PATH):
        super().__init__(sys.argv[0])
        logging.basicConfig(level=logging.DEBUG)
        
        for handler in self.handlers[:]:
            self.removeHandler(handler)

        self.consoleLogger=logging.StreamHandler()
        self.consoleLogger.setLevel(logging.INFO)
        self.consoleFormatter=logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
        self.consoleLogger.setFormatter(self.consoleFormatter)
        self.addHandler(self.consoleLogger)

        if not os.path.exists(os.path.abspath(absdirpath)):
            try:
                os.mkdir(os.path.abspath(absdirpath))
                self.info(f"Has create a dir named: {os.path.basename(absdirpath)}")
            except Exception as e:
                self.warning(f"{e}")
                sys.exit(-1)
        
        self.fileLog=os.path.abspath(absdirpath)+f"\\{os.path.basename(os.path.abspath(sys.argv[0].split(".")[0]))}.log"

        if not os.path.exists(os.path.abspath(self.fileLog)):
            try:
                pathlib.Path(self.fileLog).touch(exist_ok=True)
                self.info(f"Have create a log_file named: {os.path.basename(self.fileLog)}")
            except Exception as e:
                self.warning(f"{e}")
                sys.exit(-1)

        self.fileLogger=logging.FileHandler(self.fileLog)
        self.fileLogger.setLevel(logging.DEBUG)
        self.fileFormatter=logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
        self.fileLogger.setFormatter(self.fileFormatter)
        try:
            self.addHandler(self.fileLogger)
        except Exception as e:
            logger.warning(f"{e}")

        globvalue.logger=self


if __name__=='__main__':
    logger=MyLogger("D:\\testdir")
    logger.info("666")
    logger.debug("777")
   