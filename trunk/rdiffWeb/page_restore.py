#!/usr/bin/python

from cherrypy.lib.cptools import serveFile
import rdw_helpers, page_main, librdiff
import os


class autoDeleteDir:
   def __init__(self, dirPath):
      self.dirPath = dirPath

   def __del__(self):
      rdw_helpers.removeDir(self.dirPath)

class rdiffRestorePage(page_main.rdiffPage):
   def index(self, repo, path, date):
      repo = rdw_helpers.decodeUrl(repo)
      path = rdw_helpers.decodeUrl(path)
      date = rdw_helpers.decodeUrl(date)
      try:
         rdw_helpers.ensurePathValid(repo)
         rdw_helpers.ensurePathValid(path)
      except rdw_helpers.accessDeniedError, error:
         return self.writeErrorPage(str(error))
      if not repo: return self.writeErrorPage("Backup location not specified.")
      if not repo in self.userDB.getUserRepoPaths(self.getUsername()):
         return self.writeErrorPage("Access is denied.")

      try:
         restoreTime = rdw_helpers.rdwTime()
         restoreTime.initFromString(date)
         (path, file) = os.path.split(path)
         if not file:
            file = path
            path = "/"
         filePath = librdiff.restoreFileOrDir(rdw_helpers.joinPaths(self.userDB.getUserRoot(self.getUsername()), repo), path, file, restoreTime)
      except librdiff.FileError, error:
         return self.writeErrorPage(error.getErrorString())
      except ValueError:
         return self.writeErrorPage("Invalid date parameter.")

      (directory, filename) = os.path.split(filePath)
      file = autoDeleteDir(directory)
      filename = "\""+filename.replace("\"", "\\\"")+"\"" # quote file to handle files with spaces, while escaping quotes in filename
      return serveFile(filePath, None, disposition="attachment", name=filename)
   index.exposed = True

