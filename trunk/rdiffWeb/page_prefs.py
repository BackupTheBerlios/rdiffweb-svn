#!/usr/bin/python

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff
import os
import urllib
import rdw_spider_repos
import email_notification


class rdiffPreferencesPage(page_main.rdiffPage):
   
   sampleEmail = 'joe@example.com'
   
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
      return self.getPrefsPage(statusMessage="Successfully updated backup locations.")
   updateRepos.exposed = True
   
   def setNotifications(self, **parms):
      if not self.userDB.modificationsSupported():
         return self.getPrefsPage(errorMessage="Email notification is not supported with the active user database.")
      
      repos = self.userDB.getUserRepoPaths(self.getUsername())
      
      for parmName in parms.keys():
         if parmName == "userEmail":
            if parms[parmName] == self.sampleEmail:
               parms[parmName] = ''
            self.userDB.setUserEmail(self.getUsername(), parms[parmName])
         if parmName.endswith("numDays"):
            backupName = parmName[:-7]
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
         "backups" : [],
         "sampleEmail": self.sampleEmail
      }
      if email_notification.emailNotifier().notificationsEnabled():
         repos = self.userDB.getUserRepoPaths(self.getUsername())
         backups = []
         for repo in repos:
            maxAge = self.userDB.getRepoMaxAge(self.getUsername(), repo)
            notifyOptions = []
            for i in range(0, 8):
               notifyStr = "Don't notify"
               if i == 1:
                  notifyStr = "1 day"
               elif i > 1:
                  notifyStr = str(i) + " days"
                  
               selectedStr = ""
               if i == maxAge:
                  selectedStr = "selected"
               
               notifyOptions.append({ "optionStr": notifyStr, "selectedStr": selectedStr })
               
            backups.append({ "backupName" : repo, "notifyOptions" : notifyOptions })
         
         parms.update({ "notificationsEnabled" : True, "backups" : backups })
         
      return self.startPage(title) + self.compileTemplate("user_prefs.html", **parms) + self.endPage()
      

