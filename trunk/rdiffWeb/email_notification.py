#!/usr/bin/python

import smtplib

import rdw_config
import db
import librdiff
import rdw_helpers

def emailNotificationIsEnabled():
   return getEmailHost() != "" and getEmailSender() != "" and db.userDB().getUserDBModule().modificationsSupported()

def getEmailHost():
   return rdw_config.getConfigSetting("emailHost")

def getEmailSender():
   return rdw_config.getConfigSetting("emailSender")

def getEmailUsername():
   return rdw_config.getConfigSetting("emailUsername")

def getEmailPassword():
   return rdw_config.getConfigSetting("emailPassword")

def emailNotifications():
   emailHost = getEmailHost()
   emailSender = getEmailSender()
   emailUsername = getEmailUsername()
   emailPassword = getEmailPassword()
      
   dbBackend = db.userDB().getUserDBModule()
   for user in dbBackend.getUserList():
      userRepos = dbBackend.getUserRepoPaths(user)
      oldRepos = []
      for repo in userRepos:
         maxDaysOld = dbBackend.getRepoMaxAge(user, repo)
         if maxDaysOld != 0:
            # get the last backup date
            try:
               lastBackup = librdiff.getLastBackupHistoryEntry(rdw_helpers.joinPaths(dbBackend.getUserRoot(user), repo), False)
            except librdiff.FileError:
               pass # Skip repos that have never been successfully backed up
            else:
               if lastBackup:
                  oldestGoodBackupTime = rdw_helpers.rdwTime()
                  oldestGoodBackupTime.initFromMidnightUTC(-maxDaysOld)
                  if lastBackup.date < oldestGoodBackupTime:
                     oldRepos.append({"repo" : repo, "lastBackupDate" : lastBackup.date.getDisplayString()})
               
      if oldRepos:
         userEmailAddress = dbBackend.getUserEmail(user)
         emailText = rdw_helpers.compileTemplate("email_notification.txt", repos=oldRepos, sender=emailSender, subject="Backup Failures")
         #print emailText
         #emailText = html_email.createhtmlmail("", textEmailPart, emailTitle)

         session = smtplib.SMTP(emailHost)
         session.login(emailUsername, emailPassword)
         smtpresult = session.sendmail(emailSender, [userEmailAddress], emailText)
         if smtpresult:
            error = ""
            for recipient in smtpresult.keys():
               error = """Could not delivery mail to: %s

Server said: %s
%s

%s""" % (recipient, smtpresult[recipient][0], smtpresult[recipient][1], error)
            raise smtplib.SMTPException, error
         session.quit()

