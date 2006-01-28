#!/usr/bin/python

import page_main
import librdiff
import rdw_helpers

class rdiffStatusPage(page_main.rdiffPage):
   def index(self):
      userMessages = self._getUserMessages()
      page = self.startPage("Backup Status")
      page = page + self.writeTopLinks()
      page = page + self.compileTemplate("status.html", messages=userMessages)      
      page = page + self.endPage()
      return page
   index.exposed = True

   def _getUserMessages(self):
      userRoot = self.userDB.getUserRoot(self.getUsername())
      userRepos = self.userDB.getUserRepoPaths(self.getUsername())

      asOfDate = rdw_helpers.rdwTime()
      asOfDate.initFromMidnightUTC(-5)

      # build list of all backups
      allBackups = []
      repoErrors = []
      for repo in userRepos:
         try:
            backups = librdiff.getBackupHistorySinceDate(rdw_helpers.joinPaths(userRoot, repo), asOfDate)
            allBackups = [{"repo": repo, "date": backup.date, "displayDate": backup.date.getDisplayString(),
               "size": rdw_helpers.formatFileSizeStr(backup.size), "errors": backup.errors} for backup in backups]
         except librdiff.FileError, error:
            repoErrors.append({"repo": repo, "error": error.getErrorString()})

      allBackups.sort(lambda x, y: cmp(y["date"], x["date"]))
      failedBackups = filter(lambda x: x["errors"], allBackups)

      # group successful backups by day
      successfulBackups = filter(lambda x: not x["errors"], allBackups)
      if successfulBackups:
         lastSuccessDate = successfulBackups[0]["date"]
      successfulBackups = rdw_helpers.groupby(successfulBackups, lambda x: x["date"].getLocalDaysSinceEpoch())

      userMessages = []

      # generate failure messages
      for job in failedBackups:
         date = job["date"]
         title = "Backup Failed: " + job["repo"]
         message = self.compileTemplate("status_failure.html", **job)
         userMessages.append({"date": date, "title": title, "message": message, "repoErrors": []})

      # generate success messages (publish date is most recent backup date)
      for day in successfulBackups.keys():
         date = successfulBackups[day][0]["date"]
         title = "Successful Backups for " + date.getDateDisplayString()
         message = self.compileTemplate("status_success.html", backups=successfulBackups[day])

         # include repository errors in most recent entry
         if date == lastSuccessDate: repoErrorsForMsg = repoErrors
         else: repoErrorsForMsg = []
         
         userMessages.append({"date": date, "title": title, "message": message, "repoErrors": repoErrorsForMsg})

      # sort messages by date
      userMessages.sort(lambda x, y: cmp(y["date"], x["date"]))
      return userMessages
