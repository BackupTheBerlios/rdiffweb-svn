#!/usr/bin/python

import subprocess

import rdw_config
import rdw_helpers
import page_main
import librdiff


class rdiffLocationsPage(page_main.rdiffPage):
   ''' Shows the locations page. Will show all available destination
   backup directories. This is the root (/) page '''
   def index(self):
      page = self.startPage("Backup Locations")
      page = page + self.compileTemplate("repo_listing.html", **self.getParmsForPage(self.getUserDB().getUserRoot(self.getUsername()), self.getUserDB().getUserRepoPaths(self.getUsername())))
      page = page + self.endPage()
      return page
   index.exposed = True
   
   def getParmsForPage(self, root, repos):
      repoList = []
      for userRepo in repos:
         try:
            repoHistory = librdiff.getLastBackupHistoryEntry(rdw_helpers.joinPaths(root, userRepo))
         except librdiff.FileError:
            repoSize = "0"
            repoDate = "Error"
            repoList.append({ "repoName" : userRepo,
                           "repoSize" : repoSize,
                           "repoDate" : repoDate,
                           "repoBrowseUrl" : self.buildBrowseUrl(userRepo, "/", False),
                           "repoHistoryUrl" : self.buildHistoryUrl(userRepo),
                           'failed': True})
         else:
            repoSize = rdw_helpers.formatFileSizeStr(repoHistory.size)
            if repoHistory.inProgress:
               repoSize = "In Progress"
            repoDate = repoHistory.date.getDisplayString()
            repoList.append({ "repoName" : userRepo,
                              "repoSize" : repoSize,
                              "repoDate" : repoDate,
                              "repoBrowseUrl" : self.buildBrowseUrl(userRepo, "/", False),
                              "repoHistoryUrl" : self.buildHistoryUrl(userRepo),
                              'failed': False})

      self._sortLocations(repoList)
      # Make second pass through list, setting the 'altRow' attribute
      for i in range(0, len(repoList)):
         repoList[i]['altRow'] = (i % 2 == 0)
      # Calculate disk usage
      diskUsage = ''
      diskUsageCommand = rdw_config.getConfigSetting('diskUsageCommand')
      if diskUsageCommand:
         diskUsage = subprocess.Popen([diskUsageCommand, self.getUsername(), self.getUserDB().getUserRoot(self.getUsername())],
                                    stdout=subprocess.PIPE).communicate()[0]
         try:
            diskUsageNum = int(diskUsage)
         except:
            pass
         else:
            diskUsage = rdw_helpers.formatFileSizeStr(diskUsageNum)
      return { "title" : "browse", "repos" : repoList, "diskUsage": diskUsage }
            
            
   def _sortLocations(self, locations):
      def compare(left, right):
         if left['failed'] != right['failed']:
            return cmp(left['failed'], right['failed'])
         return cmp(left['repoName'], right['repoName'])
      
      locations.sort(compare)
      

class locationsPageTest(page_main.pageTest, rdiffLocationsPage):
   def getTemplateName(self):
      return "locations_template.txt"
   
   def getExpectedResultsName(self):
      return "locations_results.txt"
      
   def getParmsForTemplate(self, repoParentPath, repoName):
      return self.getParmsForPage(repoParentPath, [repoName])
