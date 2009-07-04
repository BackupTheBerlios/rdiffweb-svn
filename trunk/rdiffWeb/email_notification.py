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

def notificationsEnabled(userDB):
   notifier = emailNotifier()
   return notifier.getEmailHost() != "" and\
          notifier.getEmailSender() != "" and\
          notifier.getNotificationTimeStr()

class emailNotifier:
   def __init__(self):
      self.userDB = db.userDB().getUserDBModule()
      
   def sendEmails(self):
      # Send emails to each user, if requested
      for user in self.userDB.getUserList():
         try:
            notifySettings = self.userDB.getNotificationSettings(user)
            userRepos = self.userDB.getUserRepoPaths(user)
            oldRepos = []
            for repo in userRepos:
               # get the last backup date
               repoPath = rdw_helpers.joinPaths(self.userDB.getUserRoot(user), repo)
               oldRepoInfo = self._getOldRepoInfo(repo, repoPath,
                                                  notifySettings, False)
               if not oldRepoInfo is None:
                  oldRepos.append(oldRepoInfo)
                        
            if oldRepos:
               userEmailAddress = notifySettings['email']
               emailText = rdw_helpers.compileTemplate("email_notification.txt", repos=oldRepos,
                                                       sender=self.getEmailSender(), user=user, to=userEmailAddress)
      
               session = smtplib.SMTP(self.getEmailHost())
               if self._getEmailUsername():
                  session.login(self._getEmailUsername(), self._getEmailPassword())
               smtpresult = session.sendmail(self.getEmailSender(), userEmailAddress.split(";"), emailText)
               session.quit()
         except Exception:
            rdw_logging.log_exception()

      # Send admin-level emails, if requested
      adminEmails = []
      for user in self.userDB.getUserList():
         if self.userDB.userIsAdmin(user):
            userEmail = self.userDB.getNotificationSettings(user)['email']
            if userEmail:
               adminEmails.append(userEmail)

      if adminEmails:
         oldUserRepos = []

         for user in self.userDB.getUserList():
            notifySettings = self.userDB.getNotificationSettings(user)
            userRepos = self.userDB.getUserRepoPaths(user)
            oldRepos = []
            for repo in userRepos:
               repoPath = rdw_helpers.joinPaths(self.userDB.getUserRoot(user), repo)
               oldRepoInfo = self._getOldRepoInfo(repo, repoPath,
                                                  notifySettings, True)
               if not oldRepoInfo is None:
                  oldRepos.append(oldRepoInfo)

            if oldRepos:
               oldUserRepos.append({
                  'user': user,
                  'maxAge': maxAge,
                  'repos': oldRepos
               })

         session = smtplib.SMTP(self.getEmailHost())
         if self._getEmailUsername():
            session.login(self._getEmailUsername(), self._getEmailPassword())
         for email in adminEmails:
            emailText = rdw_helpers.compileTemplate("admin_email_notification.txt",
                                                    users=oldUserRepos,
                                                    sender=self.getEmailSender(),
                                                    date=datetime.date.today().strftime('%m/%d/%Y'),
                                                    to=email)
            smtpresult = session.sendmail(self.getEmailSender(), email.split(";"), emailText)
         session.quit()

   def notificationsEnabled(self):
      return notificationsEnabled(self.userDB)
 
   def getEmailHost(self):
      return rdw_config.getConfigSetting("emailHost")

   def getEmailSender(self):
      return rdw_config.getConfigSetting("emailSender")
   
   def getNotificationTimeStr(self):
      return rdw_config.getConfigSetting("emailNotificationTime")
   
   def _getOldRepoInfo(self, repoName, repoPath,
                     notifySettings, isAdminMonitoring):
      if isAdminMonitoring:
         maxAge = notifySettings['adminMaxAge']
      else:
         maxAge = notifySettings['anyRepoMaxAge']
         if not maxAge:
            maxAge = notifySettings['repos'][repo]

      if maxAge == 0:
         return None

      try:
         lastBackup = librdiff.getLastBackupHistoryEntry(repoPath, False)
      except librdiff.FileError:
         return {
            "repo" : repoName,
            "lastBackupDate" : "never",
            "maxAge" : maxAge
         }
      except Exception:
         rdw_logging.log_exception()
         rdw_logging.log('(Previous exception occurred for repo %s.)' % repoPath)
      else:
         if lastBackup:
            oldestGoodBackupTime = rdw_helpers.rdwTime()
            oldestGoodBackupTime.initFromMidnightUTC(-maxAge)
            if lastBackup.date < oldestGoodBackupTime:
               return {
                  "repo" : repoName,
                  "lastBackupDate" : lastBackup.date.getDisplayString(),
                  "maxAge" : maxAge
               }
      return None

   def _getEmailUsername(self):
      return rdw_config.getConfigSetting("emailUsername")
   
   def _getEmailPassword(self):
      return rdw_config.getConfigSetting("emailPassword")

def buildNotificationsTable(notify_options):
   """ options should be a dictionary of optionName to selectedOptionNum """
   
   options = []
   keys = notify_options.keys()
   keys.sort()
   for key in keys:
      notifyOptions = []
      for i in range(0, 8):
         notifyStr = "Don't notify"
         if i == 1:
            notifyStr = "1 day"
         elif i > 1:
            notifyStr = str(i) + " days"
            
         selectedStr = ""
         if i == notify_options[key]:
            selectedStr = "selected"
         
         notifyOptions.append({ "optionStr": notifyStr, "selectedStr": selectedStr })
      options.append({ "key" : key, "notifyOptions" : notifyOptions })

   return rdw_helpers.compileTemplate("notifications_table.html", options=options)

def loadNotificationsTableResults(post_parms):
   """ Returns a dictionary like is taken above, loaded from postdata. """

   options = {}
   for parmName in post_parms.keys():
      if parmName.endswith("numDays"):
         backupName = parmName[:-7]
         if post_parms[parmName] == "Don't notify":
            maxDays = 0
         else:
            maxDays = int(post_parms[parmName][0])
         options[backupName] = maxDays
   return options

