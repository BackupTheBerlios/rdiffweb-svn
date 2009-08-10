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
         if action == 'setPassword' or action == 'Change Password':
            return self._changePassword(parms['current'], parms['new'], parms['confirm'])
         elif action == 'updateRepos' or action == 'Find and Update Backup Locations':
            return self._updateRepos()
         elif action == 'setNotifications' or action == 'Change Notifications':
            return self._setNotifications(parms)
         elif action == 'setRestoreType' or action == 'Update Restore Preferences':
            return self._setRestoreType(parms['restoreType'])
         elif action == 'setAllowRepoDeletion' or action == 'Update':
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

      notifySettings = self.getUserDB().getNotificationSettings(self.getUsername())

      notifyForAnyRepo = parms['NotifyType'] == 'any'
      if not notifyForAnyRepo:
         notifySettings['anyRepoMaxAge'] = 0

      for key in parms.keys():
         if key == "userEmail":
            notifySettings['email'] = parms[key]
         elif key == 'AllReposInterval':
            if notifyForAnyRepo:
               notifySettings['anyRepoMaxAge'] = int(parms[key])
         else:
            if not notifyForAnyRepo:
               try:
                  repoID = int(key)
               except ValueError:
                  pass
               else:
                  repoName = self.getUserDB().getRepoName(self.getUsername(),
                                                         int(key))
                  if not repoName is None:
                     notifySettings['repos'][repoName] = int(parms[key])
      self.getUserDB().setNotificationSettings(self.getUsername(), notifySettings)

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
      def getNotifyIntervals(selectedOption, includeNone):
         def getDesc(num):
            if num == 0:
               return 'Ignore'
            elif num == 1:
               return '1 day'
            else:
               return str(num) + ' days'

         start = 0
         if not includeNone:
            start = 1
         return [{
            'optionValue': num,
            'optionDesc': getDesc(num),
            'optionSelected': num == selectedOption
         } for num in range(start, 8)]

      # Email notification options
      notifySettings = self.getUserDB().getNotificationSettings(self.getUsername())
      repos = []
      for repo in self.getUserDB().getUserRepoPaths(self.getUsername()):
         repos.append({
            'repoName': repo,
            'repoID': self.getUserDB().getRepoID(self.getUsername(), repo),
            'notifyOptions': getNotifyIntervals(notifySettings['repos'][repo],
                                                True)
         })

      title = "User Preferences"
      parms = {
         "title" : title,
         "error" : errorMessage,
         "message" : statusMessage,
         "userEmail" : notifySettings['email'],
         "notificationsEnabled" : email_notification.emailNotifier().notificationsEnabled(),
         "notifyForAny": notifySettings['anyRepoMaxAge'] != 0,
         "notifyOptions": getNotifyIntervals(notifySettings['anyRepoMaxAge'],
                                             False),
         "notifyRepos": repos,
         "backups" : [],
         "useZipFormat": self.getUserDB().useZipFormat(self.getUsername()),
         "allowRepoDeletion": self.getUserDB().allowRepoDeletion(self.getUsername())
      }

      return self.startPage(title) + self.compileTemplate("user_prefs.html", **parms) + self.endPage()

