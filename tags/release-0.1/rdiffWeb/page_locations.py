#!/usr/bin/python

import rdw_helpers, page_main, librdiff


class rdiffLocationsPage(page_main.rdiffPage):
   def index(self):
      page = self.startPage("Backup Locations")
      page = page + self.writeTopLinks()

      repoList = []
      for userRepo in self.userDB.getUserRepoPaths(self.getUsername()):
         try:
            repoHistory = librdiff.getBackupHistory(rdw_helpers.joinPaths(self.userDB.getUserRoot(self.getUsername()), userRepo), 1)
         except librdiff.FileError:
            repoSize = "0"
            repoDate = "Error"
         else:
            repoSize = rdw_helpers.formatFileSizeStr(repoHistory[0].size)
            repoDate = repoHistory[0].date.getDisplayString()
         repoList.append({ "repoName" : userRepo,
                           "repoSize" : repoSize,
                           "repoDate" : repoDate,
                           "repoBrowseUrl" : self.buildBrowseUrl(userRepo, "/"),
                           "repoHistoryUrl" : self.buildHistoryUrl(userRepo) })
      page = page + self.compileTemplate("repo_listing.html", title="browse", repos=repoList)
      page = page + self.endPage()
      return page
   index.exposed = True

