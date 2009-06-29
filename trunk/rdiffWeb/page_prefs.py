#!/usr/bin/python

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff
import os
import urllib
import rdw_spider_repos
import email_notification

class rdiffPreferencesPage(page_main.rdiffPage):
   
   def index(self, **parms):
      if parms:
         action = parms['form']
         if action == 'setPassword':
            return self._changePassword(parms['current'], parms['new'], parms['confirm'])
         elif action == 'updateRepos':
            return self._updateRepos()
         elif action == 'setNotifications':
            return self._setNotifications(parms)
         elif action == 'setRestoreType':
            return self._setRestoreType(parms['restoreType'])
         elif action == 'setAllowRepoDeletion':
            return self._setAllowRepoDeletion('allowDeletion' in parms)
         else:
            return self._getPrefsPage(errorMessage='Invalid setting.')
         
      return self._getPrefsPage('', '')
   index.exposed = True
   
   def _changePassword(self, currentPassword, newPassword, confirmPassword):
      if not self.getUserDB().areUserCredentialsValid(self.getUsername(), currentPassword):
         return self._getPrefsPage(errorMessage="The 'Current Password' is invalid.")
      
      if newPassword != confirmPassword:
         return self._getPrefsPage(errorMessage="The passwords do not match.")

      self.getUserDB().setUserPassword(self.getUsername(), newPassword)      
      return self._getPrefsPage(statusMessage="Password updated successfully.")
   
   def _updateRepos(self):
      rdw_spider_repos.findReposForUser(self.getUsername(), self.getUserDB())
      return self._getPrefsPage(statusMessage="Successfully updated backup locations.")

   def _setNotifications(self, parms):
      repos = self.getUserDB().getUserRepoPaths(self.getUsername())
      
      for parmName in parms.keys():
         if parmName == "userEmail":
            self.getUserDB().setUserEmail(self.getUsername(), parms[parmName])
         else:
            try:
               repoID = int(parmName)
            except ValueError:
               pass
            else:
               repoName = self.getUserDB().getRepoName(self.getUsername(),
                                                      int(parmName))
               if not repoName is None:
                  self.getUserDB().setRepoMaxAge(self.getUsername(), repoName,
                                                 int(parms[parmName]))

      return self._getPrefsPage(statusMessage="Successfully changed notification settings.")
   
   def _setRestoreType(self, restoreType):
      if restoreType == 'zip' or restoreType == 'tgz':
         self.getUserDB().setUseZipFormat(self.getUsername(), restoreType == 'zip')
      else:
         return self._getPrefsPage(errorMessage='Invalid restore format.')
      return self._getPrefsPage(statusMessage="Successfully set restore format.")
   
   def _setAllowRepoDeletion(self, allowDeletion):
      self.getUserDB().setAllowRepoDeletion(self.getUsername(), allowDeletion)
      verb = 'allowed' if allowDeletion else 'disallowed'
      return self._getPrefsPage(statusMessage="Successfully %s backup deletion and modification." % verb)
   
   def _getPrefsPage(self, errorMessage="", statusMessage=""):
      # Email notification options
      repos = []
      for repo in self.getUserDB().getUserRepoPaths(self.getUsername()):
         maxAge = self.getUserDB().getRepoMaxAge(self.getUsername(), repo)
         options = [{
            'optionValue': num,
            'optionDesc': str(num) + ' days' if num else 'Don\'t notify',
            'optionSelected': num == maxAge
         } for num in range(0, 8)]

         repos.append({
            'repoName': repo,
            'repoID': self.getUserDB().getRepoID(self.getUsername(), repo),
            'notifyOptions': options
         })

      title = "User Preferences"
      email = self.getUserDB().getUserEmail(self.getUsername());
      parms = {
         "title" : title,
         "error" : errorMessage,
         "message" : statusMessage,
         "userEmail" : email,
         "notificationsEnabled" : email_notification.emailNotifier().notificationsEnabled(),
         "repos": repos,
         "backups" : [],
         "useZipFormat": self.getUserDB().useZipFormat(self.getUsername()),
         "allowRepoDeletion": self.getUserDB().allowRepoDeletion(self.getUsername())
      }

      return self.startPage(title) + self.compileTemplate("user_prefs.html", **parms) + self.endPage()

