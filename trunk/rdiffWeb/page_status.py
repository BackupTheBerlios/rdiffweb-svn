#!/usr/bin/python

import page_main
import librdiff
import rdw_helpers
import cherrypy

class rdiffStatusPage(page_main.rdiffPage):
   def index(self):
      userMessages = self._getRecentUserMessages()
      page = self.startPage("Backup Status", rssUrl=self._buildStatusFeedUrl(), rssTitle = "Backup status for "+self.getUsername())
      page = page + self.writeTopLinks()
      page = page + self.compileTemplate("status.html", messages=userMessages, feedLink=self._buildStatusFeedUrl())
      page = page + self.endPage()
      return page
   index.exposed = True

   def entry(self, success="", date="", repo=""):
      # Validate date
      try:
         entryTime = rdw_helpers.rdwTime()
         entryTime.initFromString(date)
      except ValueError:
         return self.writeErrorPage("Invalid date parameter.")

      if success.upper() == "TRUE":
         userRepos = self.userDB.getUserRepoPaths(self.getUsername())

         # Set the start and end time to be the start and end of the day, respectively, to get all entries for that day
         startTime = rdw_helpers.rdwTime()
         startTime.timeInSeconds = entryTime.timeInSeconds
         startTime.tzOffset = entryTime.tzOffset
         endTime = rdw_helpers.rdwTime()
         endTime.timeInSeconds = entryTime.timeInSeconds
         endTime.tzOffset = entryTime.tzOffset
         startTime.setTime(0, 0, 0)
         endTime.setTime(23, 59, 59)

         userMessages = self._getUserMessages(userRepos, True, False, startTime, endTime)
      else:
         # Validate repo parameter
         if not repo: return self.writeErrorPage("Backup location not specified.")
         if not repo in self.userDB.getUserRepoPaths(self.getUsername()):
            return self.writeErrorPage("Access is denied.")
         try:
            rdw_helpers.ensurePathValid(repo)
         except rdw_helpers.accessDeniedError, error:
            return self.writeErrorPage(str(error))

         userMessages = self._getUserMessages([repo], False, True, entryTime, entryTime)

      page = self.startPage("Backup Status", rssUrl=self._buildStatusFeedUrl(), rssTitle = "Backup status for "+self.getUsername()) # TODO: should we have an RSS feed link here?
      page = page + self.writeTopLinks()
      page = page + self.compileTemplate("status.html", messages=userMessages, feedLink=self._buildStatusFeedUrl())
      page = page + self.endPage()
      return page
   entry.exposed = True

   def feed(self):
      cherrypy.response.headerMap["Content-Type"] = "text/xml"
      userMessages = self._getRecentUserMessages()
      statusUrl = self._buildAbsoluteStatusUrl()
      return self.compileTemplate("status.xml", username=self.getUsername(), link=statusUrl, messages=userMessages)
   feed.exposed = True

   def _buildAbsoluteStatusUrl(self):
      return cherrypy.request.base + "/status/"

   def _buildStatusFeedUrl(self):
      return "/status/feed"

   def _buildStatusEntryUrl(self, isSuccess, repo, date):
      return self._buildAbsoluteStatusUrl() + "entry?success="+str(isSuccess)+"&repo="+rdw_helpers.encodeUrl(repo)+"&date="+rdw_helpers.encodeUrl(date.getUrlString())

   def _getRecentUserMessages(self):
      userRepos = self.userDB.getUserRepoPaths(self.getUsername())
      asOfDate = rdw_helpers.rdwTime()
      asOfDate.initFromMidnightUTC(-5)

      return self._getUserMessages(userRepos, True, True, asOfDate, None)

   def _getUserMessages(self, repos, includeSuccess, includeFailure, earliestDate, latestDate):
      userRoot = self.userDB.getUserRoot(self.getUsername())

      repoErrors = []
      allBackups = []
      for repo in repos:
         try:
            backups = librdiff.getBackupHistoryForDateRange(rdw_helpers.joinPaths(userRoot, repo), earliestDate, latestDate);
            allBackups += [{"repo": repo, "date": backup.date, "displayDate": backup.date.getDisplayString(),
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
      if includeFailure:
         for job in failedBackups:
            date = job["date"]
            title = "Backup Failed: " + job["repo"]
            job.update({"isSuccess": False, "date": date, "pubDate": date.getRSSPubDateString(),
               "link": self._buildStatusEntryUrl(False, job["repo"], date), "title": title, "repoErrors": [], "backups": []})
            userMessages.append(job)

      # generate success messages (publish date is most recent backup date)
      if includeSuccess:
         for day in successfulBackups.keys():
            date = successfulBackups[day][0]["date"]
            title = "Successful Backups for " + date.getDateDisplayString()

            # include repository errors in most recent entry
            if date == lastSuccessDate: repoErrorsForMsg = repoErrors
            else: repoErrorsForMsg = []

            userMessages.append({"isSuccess": 1, "date": date, "pubDate": date.getRSSPubDateString(),
               "link": self._buildStatusEntryUrl(True, "", date), "title": title, "repoErrors": repoErrorsForMsg, "backups":successfulBackups[day]})

      # sort messages by date
      userMessages.sort(lambda x, y: cmp(y["date"], x["date"]))
      return userMessages
