#!/usr/bin/python

import cherrypy
import os
import urllib

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff


class rdiffHistoryPage(page_main.rdiffPage):
   def index(self, repo, date=''):
      try:
         self.validateUserPath(repo)
      except rdw_helpers.accessDeniedError, error:
         return self.writeErrorPage(str(error))

      if not repo: return self.writeErrorPage("Backup location not specified.")
      if not repo in self.getUserDB().getUserRepoPaths(self.getUsername()):
         return self.writeErrorPage("Access is denied.")

      if cherrypy.request.method == 'POST':
         if not date:
            return self.writeErrorPage("No deletion date was specified.")
         deleteTime = rdw_helpers.rdwTime()
         deleteTime.initFromString(date)
         repoPath = joinPaths(self.getUserDB().getUserRoot(self.getUsername()), repo)
         try:
            librdiff.removeRepoHistory(repoPath, deleteTime)
         except librdiff.FileError, error:
            return self.writeErrorPage(error.getErrorString())

      parms = {}
      try:
         parms = self.getParmsForPage(joinPaths(self.getUserDB().getUserRoot(self.getUsername()), repo), repo)
      except librdiff.FileError, error:
         return self.writeErrorPage(error.getErrorString())
      
      return self.startPage("Backup History") + self.compileTemplate("history.html", **parms) + self.endPage()
   index.exposed = True
   
   def getParmsForPage(self, repoPath, repoName, message='', error=''):
      rdiffHistory = librdiff.getBackupHistory(repoPath)
      rdiffHistory.reverse()
      entries = []
      cumulativeSize = 0
      if len(rdiffHistory) > 0: cumulativeSize = rdiffHistory[0].size
      
      for historyItem in rdiffHistory:
         fileSize = ""
         incrementSize = ""
         cumulativeSizeStr = ""
         if not historyItem.inProgress:
            fileSize = rdw_helpers.formatFileSizeStr(historyItem.size)
            cumulativeSize += historyItem.incrementSize
            cumulativeSizeStr = rdw_helpers.formatFileSizeStr(cumulativeSize)
         entries.append({ "date" : historyItem.date.getDisplayString(),
                          "rawDate" : historyItem.date.getUrlString(),
                          "inProgress" : historyItem.inProgress,
                          "errors" : historyItem.errors,
                          "cumulativeSize" : cumulativeSizeStr,
                          "rawIncrementSize": historyItem.incrementSize,
                          "size" : fileSize })

      # Now, go backwards through the history, and calculate space used by increments
      cumulativeSize = 0
      for entry in reversed(entries):
         entry['priorIncrementsSize'] = rdw_helpers.formatFileSizeStr(cumulativeSize)
         cumulativeSize += entry['rawIncrementSize']

      # Don't allow history deletion for the last item
      if entries:
         entries[-1]['allowHistoryDeletion'] = False
      return {
         "title": "Backup history for "+repoName,
         "history": entries,
         "totalBackups": len(rdiffHistory),
         "allowHistoryDeletion": self.getUserDB().allowRepoDeletion(self.getUsername()),
         "message": message,
         "error": error
      }
      

class historyPageTest(page_main.pageTest, rdiffHistoryPage):
   def getTemplateName(self):
      return "history_template.txt"
   
   def getExpectedResultsName(self):
      return "history_results.txt"
      
   def getParmsForTemplate(self, repoParentPath, repoName):
      return self.getParmsForPage(rdw_helpers.joinPaths(repoParentPath, repoName), repoName)
