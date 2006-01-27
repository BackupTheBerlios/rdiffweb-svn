#!/usr/bin/python

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff
import os
import urllib


class rdiffBrowsePage(page_main.rdiffPage):
   def index(self, repo="", path=""):

      repo = rdw_helpers.decodeUrl(repo)
      path = rdw_helpers.decodeUrl(path)
      try:
         rdw_helpers.ensurePathValid(repo)
         rdw_helpers.ensurePathValid(path)
      except rdw_helpers.accessDeniedError, error:
         return self.writeErrorPage(str(error))

      # NOTE: a blank path parm is allowed, since that just results in a listing of the repo root
      if not repo: return self.writeErrorPage("Backup location not specified.")
      if not repo in self.userDB.getUserRepoPaths(self.getUsername()):
         return self.writeErrorPage("Access is denied.")

      # Build "parent directories" links
      parentDirs = [{ "parentPath" : self.buildLocationsUrl(), "parentDir" : "Backup Locations" }]
      parentDirs.append({ "parentPath" : self.buildBrowseUrl(repo, "/"), "parentDir" : repo.lstrip("/") })
      parentDirPath = "/"
      for parentDir in path.split("/"):
         if parentDir:
            parentDirPath = joinPaths(parentDirPath, parentDir)
            parentDirs.append({ "parentPath" : self.buildBrowseUrl(repo, parentDirPath), "parentDir" : parentDir })

      parentDirs[-1]["parentPath"] = "" # Clear link for last parent, so it doesn't show it as a link

      # Get list of actual directory entries
      try:
         fullRepoPath = joinPaths(self.userDB.getUserRoot(self.getUsername()), repo)
         libEntries = librdiff.getDirEntries(fullRepoPath, path)
      except librdiff.FileError, error:
         return self.writeErrorPage(str(error))

      entries = []
      for libEntry in libEntries:
         entryLink = ""
         if libEntry.isDir:
            entryLink = self.buildBrowseUrl(repo, joinPaths(path, libEntry.name))
            changeDates = []
         else:
            entryLink = self.buildRestoreUrl(repo, joinPaths(path, libEntry.name), libEntry.changeDates[-1])
            entryChangeDates = libEntry.changeDates[:-1]
            entryChangeDates.reverse()
            changeDates = [ { "changeDateUrl" : self.buildRestoreUrl(repo, joinPaths(path, libEntry.name), x),
                              "changeDateStr" : x.getDisplayString() } for x in entryChangeDates]

         showNoRevisionsText = (len(changeDates) == 0) and (not libEntry.isDir)
         entries.append({ "filename" : libEntry.name,
                          "fileRestoreUrl" : entryLink,
                          "exists" : libEntry.exists,
                          "date" : libEntry.changeDates[-1].getDisplayString(),
                          "size" : rdw_helpers.formatFileSizeStr(libEntry.fileSize),
                          "hasPrevRevisions" : len(changeDates) > 0,
                          "showNoRevisionsText" : showNoRevisionsText,
                          "changeDates" : changeDates })

      # Start page
      title = "Browse "+repo
      page = self.startPage(title)
      page = page + self.writeTopLinks()
      page = page + self.compileTemplate("dir_listing.html", title=title, files=entries, parentDirs=parentDirs)
      page = page + self.endPage()
      return page

   index.exposed = True

