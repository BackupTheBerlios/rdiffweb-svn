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

      parms = {}
      try:
         parms = self.getParmsForPage(joinPaths(self.userDB.getUserRoot(self.getUsername()), repo), repo)
      except librdiff.FileError, error:
         return self.writeErrorPage(error.getErrorString())
      
      return self.startPage("Backup History") + self.compileTemplate("history.html", **parms) + self.endPage()
   index.exposed = True
   
   def getParmsForPage(self, repoPath, repoName):
      rdiffHistory = librdiff.getBackupHistory(repoPath)
      rdiffHistory.reverse()
      entries = []
      totalIncrementSize = 0
      for historyItem in rdiffHistory:
         fileSize = ""
         incrementSize = ""
         if not historyItem.inProgress:
            fileSize = rdw_helpers.formatFileSizeStr(historyItem.size)
            incrementSize = rdw_helpers.formatFileSizeStr(historyItem.incrementSize)
            totalIncrementSize += historyItem.incrementSize
         entries.append({ "date" : historyItem.date.getDisplayString(),
                          "inProgress" : historyItem.inProgress,
                          "errors" : historyItem.errors,
                          "incrementSize" : incrementSize,
                          "size" : fileSize })
      return {"title" : "Backup history for "+repoName, "history" : entries, "totalBackups" : len(rdiffHistory), "totalIncrementSize" : rdw_helpers.formatFileSizeStr(totalIncrementSize)}
      

class historyPageTest(page_main.pageTest, rdiffHistoryPage):
   def getTemplateName(self):
      return "history_template.txt"
   
   def getExpectedResultsName(self):
      return "history_results.txt"
      
   def getParmsForTemplate(self, repoParentPath, repoName):
      return self.getParmsForPage(rdw_helpers.joinPaths(repoParentPath, repoName), repoName)
