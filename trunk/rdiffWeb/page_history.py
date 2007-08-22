#!/usr/bin/python

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff
import os, urllib


class rdiffHistoryPage(page_main.rdiffPage):
   def index(self, repo):
      try:
         self.validateUserPath(repo)
      except rdw_helpers.accessDeniedError, error:
         return self.writeErrorPage(str(error))

      if not repo: return self.writeErrorPage("Backup location not specified.")
      if not repo in self.userDB.getUserRepoPaths(self.getUsername()):
         return self.writeErrorPage("Access is denied.")

      page = self.startPage("Backup History")
      try:
         rdiffHistory = librdiff.getBackupHistory(joinPaths(self.userDB.getUserRoot(self.getUsername()), repo))
      except librdiff.FileError, error:
         return self.writeErrorPage(error.getErrorString())

      rdiffHistory.reverse()
      entries = []
      for historyItem in rdiffHistory:
         sizeStr = ""
         if not historyItem.inProgress:
            sizeStr = rdw_helpers.formatFileSizeStr(historyItem.size)
         entries.append({ "date" : historyItem.date.getDisplayString(),
                          "inProgress" : historyItem.inProgress,
                          "errors" : historyItem.errors,
                          "size" : sizeStr })
      page = page + self.compileTemplate("history.html", title="Backup history for "+repo, history=entries)
      page = page + self.endPage()
      return page
   index.exposed = True
