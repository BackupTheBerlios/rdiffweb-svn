#!/usr/bin/python

import rdw_helpers, page_main, librdiff


class rdiffLocationsPage(page_main.rdiffPage):
   ''' Shows the locations page. Will show all available destination
   backup directories. This is the root (/) page '''
   def index(self):
      page = self.startPage("Backup Locations")
      page = page + self.compileTemplate("repo_listing.html", **self.getParmsForPage(self.userDB.getUserRoot(self.getUsername()), self.userDB.getUserRepoPaths(self.getUsername())))
      page = page + self.endPage()
      return page
   index.exposed = True
   
   def getParmsForPage(self, root, repos):
      repoList = []
      repoErrors = []
      for userRepo in repos:
         try:
            repoHistory = librdiff.getLastBackupHistoryEntry(rdw_helpers.joinPaths(root, userRepo))
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
            if repoHistory.inProgress:
               repoSize = "In Progress"
            repoDate = repoHistory.date.getDisplayString()
            repoList.append({ "repoName" : userRepo,
                              "repoSize" : repoSize,
                              "repoDate" : repoDate,
                              "repoBrowseUrl" : self.buildBrowseUrl(userRepo, "/", False),
                              "repoHistoryUrl" : self.buildHistoryUrl(userRepo) })
      return { "title" : "browse", "repos" : repoList, "badrepos" : repoErrors }
      

class locationsPageTest(page_main.pageTest, rdiffLocationsPage):
   def getTemplateName(self):
      return "locations_template.txt"
   
   def getExpectedResultsName(self):
      return "locations_results.txt"
      
   def getParmsForTemplate(self, repoParentPath, repoName):
      return self.getParmsForPage(repoParentPath, [repoName])
