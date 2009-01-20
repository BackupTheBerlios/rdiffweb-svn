#!/usr/bin/python

import sys
import traceback

import rdw_config

def log(message):
   message = message.strip('\r\n')
   print message
   log_file_path = rdw_config.getConfigSetting('ErrorLogFile')
   if log_file_path:
      log_file = open(log_file_path, 'a')
      log_file.write(message + '\n')
      log_file.close()

def log_exception():
   """ Logs the exception and traceback. Should only be called
   from an exception handler. """

   etype, value, tb = sys.exc_info()
   tb_lines = traceback.format_exception(etype, value, tb)
   log('Encountered exception:\n' + ''.join(tb_lines) + '\n')
