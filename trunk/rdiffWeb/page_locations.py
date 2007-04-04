#!/usr/bin/python

import rdw_helpers, page_main, librdiff


class rdiffLocationsPage(page_main.rdiffPage):
   ''' Shows the locations page. Will show all available destination
   backup directories. This is the root (/) page '''
   def index(self):
      page = self.startPage("Backup Locations")

      repoList = []
      repoErrors = []
      for userRepo in self.userDB.getUserRepoPaths(self.getUsername()):
         try:
            repoHistory = librdiff.getLastBackupHistoryEntry(rdw_helpers.joinPaths(self.userDB.getUserRoot(self.getUsername()), userRepo))
         except librdiff.FileError:
            repoSize = "0"
            repoDate = "Error"
            repoErrors.append({ "repoName" : userRepo,
                           "repoSize" : repoSize,
                           "repoDate" : repoDate,
                           "repoBrowseUrl" : self.buildBrowseUrl(userRepo, "/", False),
                           "repoHistoryUrl" : self.buildHistoryUrl(userRepo) })
         else:
            repoSize = rdw_helpers.formatFileSizeStr(repoHistory.size)
            repoDate = repoHistory.date.getDisplayString()
            repoList.append({ "repoName" : userRepo,
                              "repoSize" : repoSize,
                              "repoDate" : repoDate,
                              "repoBrowseUrl" : self.buildBrowseUrl(userRepo, "/", False),
                              "repoHistoryUrl" : self.buildHistoryUrl(userRepo) })
      page = page + self.compileTemplate("repo_listing.html", title="browse", repos=repoList, badrepos=repoErrors)
      page = page + self.endPage()
      return page
   index.exposed = True

