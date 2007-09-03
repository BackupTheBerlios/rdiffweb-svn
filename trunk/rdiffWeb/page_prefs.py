#!/usr/bin/python

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff
import os
import urllib


class rdiffPreferencesPage(page_main.rdiffPage):
   
   def index(self):
      return self.getPrefsPage("", "")
   index.exposed = True
   
   def changePassword(self, currentPassword, newPassword, confirmPassword):
      if not self.userDB.modificationsSupported():
         return self.getPrefsPage("Password changing is not supported with the active user database.", "")
      
      if not self.userDB.areUserCredentialsValid(self.getUsername(), currentPassword):
         return self.getPrefsPage("The 'Current Password' is invalid.", "")
      
      if newPassword != confirmPassword:
         return self.getPrefsPage("The passwords do not match.", "")

      self.userDB.setUserPassword(self.getUsername(), newPassword)
      
      return self.getPrefsPage("", "Password updated successfully.")
   changePassword.exposed = True
   
   def getPrefsPage(self, errorMessage, statusMessage):
      title = "User Preferences"
      return self.startPage(title) + self.compileTemplate("user_prefs.html", title=title, error=errorMessage, message=statusMessage) + self.endPage()
      
