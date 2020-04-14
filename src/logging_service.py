''' Module to be used to log output from the application in a consistent neat way'''

import logging
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__)) #the directory containing this python file

class Logger():
    ''' Logging class'''
    def __configure_logging_format(self): #Adding two underscores at start of a python method makes it private
        logging.getLogger().setLevel(logging.INFO)
        logging.basicConfig(filename=dir_path+'/logs/covid_19_estimator.log', filemode='a',format='%(asctime)s - %(levelname)s - %(message)s')

    def log_information(self,message):
        self.__configure_logging_format()
        #logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        return logging.info(message)

    def log_error(self,message):
        self.__configure_logging_format()
        #logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
        return logging.error(message)