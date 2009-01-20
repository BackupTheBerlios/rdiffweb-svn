#!/usr/bin/python

import smtplib

import rdw_config
import db
import librdiff
import rdw_helpers
import rdw_logging
import datetime
import threading
import time

def startEmailNotificationThread(killEvent):
   newThread = emailNotifyThread(killEvent)
   newThread.start()

class emailNotifyThread(threading.Thread):
   def __init__(self, killEvent):
      self.killEvent = killEvent
      threading.Thread.__init__(self)
      
   def run(self):
      self.notifier = emailNotifier()
      if not self.notifier.notificationsEnabled():
         return;
      emailTimeStr = rdw_config.getConfigSetting("emailNotificationTime")
      while True:
         try:
            emailTime = time.strptime(emailTimeStr, "%H:%M")
            now = datetime.datetime.now()
            nextEmailTime = now.replace(hour=emailTime.tm_hour, minute=emailTime.tm_min, second=0, microsecond=0)
            if nextEmailTime < now:
               nextEmailTime = nextEmailTime + datetime.timedelta(days=1)
            delta = (nextEmailTime - now).seconds
            self.killEvent.wait(delta)
            if self.killEvent.isSet():
               return

            self.notifier.sendEmails()
         except Exception:
            rdw_logging.log_exception()

class emailNotifier:
   def __init__(self):
      self.userDB = db.userDB().getUserDBModule()
      
   def notificationsEnabled(self):
      return self._getEmailHost() != "" and\
             self._getEmailSender() != "" and\
             self._getNotificationTimeStr() != "" and\
             self.userDB.modificationsSupported()

   def sendEmails(self):
      for user in self.userDB.getUserList():
         try:
            userRepos = self.userDB.getUserRepoPaths(user)
            oldRepos = []
            for repo in userRepos:
               maxDaysOld = self.userDB.getRepoMaxAge(user, repo)
               if maxDaysOld != 0:
                  # get the last backup date
                  repoPath = rdw_helpers.joinPaths(self.userDB.getUserRoot(user), repo)
                  try:
                     lastBackup = librdiff.getLastBackupHistoryEntry(repo_path, False)
                  except librdiff.FileError:
                     pass # Skip repos that have never been successfully backed up
                  except Exception:
                     rdw_logging.log_exception()
                     rdw_logging.log('(Previous exception occurred for repo %s.)' % repoPath)
                  else:
                     if lastBackup:
                        oldestGoodBackupTime = rdw_helpers.rdwTime()
                        oldestGoodBackupTime.initFromMidnightUTC(-maxDaysOld)
                        if lastBackup.date < oldestGoodBackupTime:
                           oldRepos.append({"repo" : repo, "lastBackupDate" : lastBackup.date.getDisplayString(), "maxAge" : maxDaysOld })
                        
            if oldRepos:
               userEmailAddress = self.userDB.getUserEmail(user)
               emailText = rdw_helpers.compileTemplate("email_notification.txt", repos=oldRepos,
                                                       sender=self._getEmailSender(), user=user, to=userEmailAddress)
      
               session = smtplib.SMTP(self._getEmailHost())
               if self._getEmailUsername():
                  session.login(self._getEmailUsername(), self._getEmailPassword())
               smtpresult = session.sendmail(self._getEmailSender(), userEmailAddress.split(";"), emailText)
               session.quit()
         except Exception:
            rdw_logging.log_exception()
             
   def _getEmailHost(self):
      return rdw_config.getConfigSetting("emailHost")

   def _getEmailSender(self):
      return rdw_config.getConfigSetting("emailSender")
   
   def _getEmailUsername(self):
      return rdw_config.getConfigSetting("emailUsername")
   
   def _getEmailPassword(self):
      return rdw_config.getConfigSetting("emailPassword")
   
   def _getNotificationTimeStr(self):
      return rdw_config.getConfigSetting("emailNotificationTime")

