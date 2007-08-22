#!/usr/bin/python

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff
import os
import urllib


class rdiffBrowsePage(page_main.rdiffPage):
   
   def index(self, repo="", path="", restore=""):
      try:
         self.validateUserPath(joinPaths(repo, path))
      except rdw_helpers.accessDeniedError, error:
         return self.writeErrorPage(str(error))

      # NOTE: a blank path parm is allowed, since that just results in a listing of the repo root
      if not repo: return self.writeErrorPage("Backup location not specified.")
      if not repo in self.userDB.getUserRepoPaths(self.getUsername()):
         return self.writeErrorPage("Access is denied.")

      parms = self.getParmsForPage(self.userDB.getUserRoot(self.getUsername()), repo, path, restore)
      page = self.startPage(parms["title"])
      page = page + self.compileTemplate("dir_listing.html", **parms)
      page = page + self.endPage()
      return page
   
   index.exposed = True
   
   
   def getParmsForPage(self, userRoot, repo="", path="", restore=""):
      # Build "parent directories" links
      parentDirs = [{ "parentPath" : self.buildLocationsUrl(), "parentDir" : "Backup Locations" }]
      parentDirs.append({ "parentPath" : self.buildBrowseUrl(repo, "/", False), "parentDir" : repo.lstrip("/") })
      parentDirPath = "/"
      for parentDir in path.split("/"):
         if parentDir:
            parentDirPath = joinPaths(parentDirPath, parentDir)
            parentDirs.append({ "parentPath" : self.buildBrowseUrl(repo, parentDirPath, False), "parentDir" : parentDir })
      parentDirs[-1]["parentPath"] = "" # Clear link for last parent, so it doesn't show it as a link

      # Set up warning about in-progress backups, if necessary
      if librdiff.backupIsInProgressForRepo(joinPaths(userRoot, repo)):
         backupWarning = "Warning: a backup is currently in progress to this location.  The displayed data may be inconsistent."
      else:
         backupWarning = ""

      restoreUrl = ""
      viewUrl = ""
      if restore == "T":
         title = "Restore "+repo
         viewUrl = self.buildBrowseUrl(repo, path, False)
         restoreDates = librdiff.getDirRestoreDates(joinPaths(userRoot, repo), path)
         restoreDates.reverse() # sort latest first
         restoreDates = [ { "dateStr" : x.getDisplayString(), "dirRestoreUrl" : self.buildRestoreUrl(repo, path, x) }
                         for x in restoreDates ]
         entries = []
      else:
         title = "Browse "+repo
         restoreUrl = self.buildBrowseUrl(repo, path, True)
         restoreDates = []

         # Get list of actual directory entries
         try:
            fullRepoPath = joinPaths(userRoot, repo)
            libEntries = librdiff.getDirEntries(fullRepoPath, path)
         except librdiff.FileError, error:
            return self.writeErrorPage(str(error))

         entries = []
         for libEntry in libEntries:
            entryLink = ""
            if libEntry.isDir:
               entryLink = self.buildBrowseUrl(repo, joinPaths(path, libEntry.name), False)
               fileType = "folder"
               fileSize= " "
               changeDates = []
            else:
               entryLink = self.buildRestoreUrl(repo, joinPaths(path, libEntry.name), libEntry.changeDates[-1])
               fileType = "file"
               entryChangeDates = libEntry.changeDates[:-1]
               entryChangeDates.reverse()
               fileSize = rdw_helpers.formatFileSizeStr(libEntry.fileSize)
               changeDates = [ { "changeDateUrl" : self.buildRestoreUrl(repo, joinPaths(path, libEntry.name), x),
                                 "changeDateStr" : x.getDisplayString() } for x in entryChangeDates]

            showRevisionsText = (len(changeDates) > 0) or libEntry.isDir
            entries.append({ "filename" : libEntry.name,
                           "fileRestoreUrl" : entryLink,
                           "filetype" : fileType,
                           "exists" : libEntry.exists,
                           "date" : libEntry.changeDates[-1].getDisplayString(),
                           "size" : fileSize,
                           "hasPrevRevisions" : len(changeDates) > 0,
                           "numPrevRevisions" : str(len(changeDates)), 
                           "hasMultipleRevisions" : len(changeDates) > 1,
                           "showRevisionsText" : showRevisionsText,
                           "changeDates" : changeDates })

      return { "title" : title, "files" : entries, "parentDirs" : parentDirs, "restoreUrl" : restoreUrl, "viewUrl" : viewUrl, "restoreDates" : restoreDates, "warning" : backupWarning }

class browsePageTest(page_main.pageTest, rdiffBrowsePage):
   def getTemplateName(self):
      return "browse_template.txt"
   
   def getExpectedResultsName(self):
      return "browse_results.txt"
      
   def getParmsForTemplate(self, repoParentPath, repoName):
      return self.getParmsForPage(repoParentPath, repoName)

if __name__ == "__main__":
   print "Called as standalone program; running unit tests..."

   import unittest
   testSuite = unittest.makeSuite(browsePageTest, 'test')
   testRunner = unittest.TextTestRunner()
   testRunner.run(testSuite)

