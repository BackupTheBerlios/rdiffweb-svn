#!/usr/bin/python

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff
import os
import urllib
import rdw_spider_repos
import email_notification


class rdiffPreferencesPage(page_main.rdiffPage):
   
   def index(self):
      return self.getPrefsPage("", "")
   index.exposed = True
   
   def changePassword(self, currentPassword, newPassword, confirmPassword):
      if not self.userDB.modificationsSupported():
         return self.getPrefsPage(errorMessage="Password changing is not supported with the active user database.")
      
      if not self.userDB.areUserCredentialsValid(self.getUsername(), currentPassword):
         return self.getPrefsPage(errorMessage="The 'Current Password' is invalid.")
      
      if newPassword != confirmPassword:
         return self.getPrefsPage(errorMessage="The passwords do not match.")

      self.userDB.setUserPassword(self.getUsername(), newPassword)
      
      return self.getPrefsPage(statusMessage="Password updated successfully.")
   changePassword.exposed = True
   
   def updateRepos(self):
      rdw_spider_repos.findReposForUser(self.getUsername(), self.userDB)
      return self.getPrefsPage(statusMessage="Successfully updated repositories.")
   updateRepos.exposed = True
   
   def setNotifications(self, **parms):
      if not self.userDB.modificationsSupported():
         return self.getPrefsPage(errorMessage="Email notification is not supported with the active user database.")
      
      repos = self.userDB.getUserRepoPaths(self.getUsername())
      
      for parmName in parms.keys():
         if parmName == "userEmail":
            self.userDB.setUserEmail(self.getUsername(), parms[parmName])
         if parmName.endswith("numDays"):
            backupName = parmName[:-7]
            print "setting backup", backupName
            if backupName in repos:
               if parms[parmName] == "Don't notify":
                  maxDays = 0
               else:
                  maxDays = int(parms[parmName][0])
               self.userDB.setRepoMaxAge(self.getUsername(), backupName, maxDays)
               
      return self.getPrefsPage(statusMessage="Successfully changed notification settings.")
   
   setNotifications.exposed = True
   
      
   
   def getPrefsPage(self, errorMessage="", statusMessage=""):
      title = "User Preferences"
      email = self.userDB.getUserEmail(self.getUsername());
      parms = {
         "title" : title,
         "error" : errorMessage,
         "message" : statusMessage,
         "userEmail" : email,
         "notificationsEnabled" : False,
         "backups" : []
      }
      if email_notification.emailNotificationIsEnabled():
         repos = self.userDB.getUserRepoPaths(self.getUsername())
         backups = [{ "backupName" : repo, "maxDays" : self.userDB.getRepoMaxAge(self.getUsername(), repo) } for repo in repos]
         
         parms.update({ "notificationsEnabled" : True, "backups" : backups })
         
      return self.startPage(title) + self.compileTemplate("user_prefs.html", **parms) + self.endPage()
      

