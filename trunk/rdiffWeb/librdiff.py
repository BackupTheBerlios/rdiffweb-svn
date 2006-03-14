#!/usr/bin/python

"""All functions throw on error."""

import os, bisect
from rdw_helpers import joinPaths, removeDir
import rdw_helpers

##### Error definitions #####
class FileError:
   def getErrorString(self):
      return self.errorString
   def __str__(self):
      return self.getErrorString()

class AccessDeniedError(FileError):
   def __init__(self):
      self.errorString = "Access is denied."

class DoesNotExistError(FileError):
   def __init__(self):
      self.errorString = "The backup location does not exist."

class UnknownError(FileError):
   def __init__(self):
      self.errorString = "An unknown error occurred."

##### Helper Functions #####
def getSessionStatsFileName(dateString):
   return "session_statistics."+dateString+".data"

def rsplit(string, sep, count=-1):
    L = [part[::-1] for part in string[::-1].split(sep[::-1], count)]
    L.reverse()
    return L

##### Interfaced objects #####
class dirEntry:
   """Includes name, isDir, fileSize, exists, and dict (changeDates) of sorted local dates when backed up"""
   def __init__(self, name, isDir, fileSize, exists, changeDates):
      self.name = name
      self.isDir = isDir
      self.fileSize = fileSize
      self.exists = exists
      self.changeDates = changeDates

class backupHistoryEntry:
   """Includes date, size (in bytes), and errors"""
   pass

##### Other objects #####
class incrementEntry:
   """Encapsalates all the ugly knowledge of increment behavior"""
   missingSuffix = ".missing"
   suffixes = [".missing", ".snapshot.gz", ".diff.gz", ".data.gz", ".data", ".dir"];

   def __init__(self, incrementName):
      self.entryName = incrementName

   def shouldShowIncrement(self):
      return self.hasIncrementSuffix(self.entryName) and not self.entryName.endswith(self.missingSuffix)

   def getFilename(self):
      filename = self._removeSuffix(self.entryName)
      return rsplit(filename, ".", 1)[0]

   def getSize(self):
      return 0 #TODO: use gzip to figure out increment size for snapshot increments

   def getDate(self):
      timeString = self.getDateString()
      returnTime = rdw_helpers.rdwTime()
      try:
         returnTime.initFromString(timeString)
         return returnTime
      except ValueError:
         return None

   def getDateString(self):
      filename = self._removeSuffix(self.entryName)
      return rsplit(filename, ".", 1)[1]

   def getDateStringNoTZ(self, tzOffset=0):
      filename = self._removeSuffix(self.entryName)
      incrDate = self.getDate()
      if not incrDate:
         print "Warning: unintelligible date string! Filename:", self.entryName, " Filetitle:", filename, " Date String:", self.getDateString()
         return "" # avoid crashing on invalid date strings

      incrDate.timeInSeconds += tzOffset
      return incrDate.getUrlStringNoTZ()

   def isCompressed(self):
      return self.entryName.endswith(".gz")

   def hasIncrementSuffix(self, filename):
      for suffix in self.suffixes:
         if filename.endswith(suffix):
            return True
      return False

   def _removeSuffix(self, filename):
      """ returns None if there was no suffix to remove. """
      for suffix in self.suffixes:
         if filename.endswith(suffix):
            return filename[0:-len(suffix)]
      return filename


rdiffDataDirName = "rdiff-backup-data"
rdiffIncrementsDirName = joinPaths(rdiffDataDirName, "increments")

class rdiffDirEntries:
   """This class is responsible for building a listing of directory entries.
      All knowledge of how increments work is contained in this class."""
   def init(self, repo, dirPath):
      # Var assignment and validation
      self.repo = repo
      self.dirPath = dirPath
      completePath = joinPaths(repo, dirPath)
      dataPath = joinPaths(repo, rdiffDataDirName)

      # cache dir listings
      self.entries = []
      if os.access(completePath, os.F_OK):
         self.entries = os.listdir(completePath) # the directory may not exist if it has been deleted
      self.dataDirEntries = os.listdir(dataPath)
      incrementsDir = joinPaths(repo, rdiffIncrementsDirName, dirPath)
      self.incrementEntries = []
      if os.access(incrementsDir, os.F_OK): # the increments may not exist if the folder has existed forever and never been changed
         self.incrementEntries = os.listdir(incrementsDir)

   def getDirEntries(self):
      """ returns dictionary of dir entries, keyed by dir name """
      entriesDict = {}

      # First, we grab a dir listing of the target, setting entry attributes
      for entryName in self.entries:
         if entryName == rdiffDataDirName: continue
         entryPath = joinPaths(self.repo, self.dirPath, entryName)
         newEntry = dirEntry(entryName, os.path.isdir(entryPath), os.lstat(entryPath)[6], True,
                             [self._getLastChangedBackupTime(entryName)])
         entriesDict[entryName] = newEntry

      # Go through the increments dir.  If we find any files that didn't exist in dirPath (i.e. have been deleted), add them
      for entryFile in self.incrementEntries:
         entry = incrementEntry(entryFile)
         if entry.shouldShowIncrement():
            entryName = entry.getFilename()
            if (not entryName in entriesDict.keys()):
               entryPath = joinPaths(self.repo, rdiffIncrementsDirName, self.dirPath, entryName)
               newEntry = dirEntry(entryName, os.path.isdir(entryPath), 0, False, [entry.getDate()])
               entriesDict[entryName] = newEntry
            else:
               bisect.insort_left(entriesDict[entryName].changeDates, entry.getDate())

      return entriesDict

   def _getFirstBackupAfterDate(self, date):
      """ Iterates the mirror_metadata files in the rdiff data dir """
      backupFiles = filter(lambda x: x.startswith("mirror_metadata"), self.dataDirEntries)
      backupFiles.sort()
      for backup in backupFiles:
         backupTimeString = rsplit(backup, ".", 3)[1]
         backupTime = rdw_helpers.rdwTime()
         backupTime.initFromString(backupTimeString)
         if not date or backupTime > date:
            return backupTime
      return backupFiles[-1]

   def _getLastChangedBackupTime(self, filename):
      files = filter((lambda x: incrementEntry(x).getFilename() == filename), self.incrementEntries)
      files.sort()
      if not files:
         return self._getFirstBackupAfterDate(None)
      return self._getFirstBackupAfterDate(incrementEntry(files[-1]).getDate())


def getSessionStatsFile(rdiffDataDir, entry):
   """Attempts to get the sessions statistics file for a given backup. Tries the following to find a match:
      1. The date with no timezone information
      2. The date, 1 hour in the past, with no timezone information
      3. The date with timezone information"""
   sessionStatsPath = joinPaths(rdiffDataDir, getSessionStatsFileName(entry.getDateStringNoTZ()))
   if os.access(sessionStatsPath, os.F_OK):
      return sessionStatsPath
   sessionStatsPath = joinPaths(rdiffDataDir, getSessionStatsFileName(entry.getDateStringNoTZ(-60*60)))
   if os.access(sessionStatsPath, os.F_OK):
      return sessionStatsPath
   sessionStatsPath = joinPaths(rdiffDataDir, getSessionStatsFileName(entry.getDateString()))
   if os.access(sessionStatsPath, os.F_OK):
      return sessionStatsPath
   return ""

def checkRepoPath(repoRoot, filePath):
   # Make sure repoRoot is a valid rdiff-backup repository
   dataPath = joinPaths(repoRoot, rdiffDataDirName)
   if not os.access(dataPath, os.F_OK) or not os.path.isdir(dataPath):
      raise DoesNotExistError()

   # Make sure there are no symlinks in the path
   pathToCheck = joinPaths(repoRoot, filePath)
   while True:
      pathToCheck = pathToCheck.rstrip("/")
      if os.path.islink(pathToCheck):
         raise AccessDeniedError()

      (pathToCheck, file) = os.path.split(pathToCheck)
      if not file:
         break

   # Make sure that the folder/file exists somewhere - either in the current folder, or in the incrementsDir
   if not os.access(joinPaths(repoRoot, filePath), os.F_OK):
      (parentFolder, filename) = os.path.split(joinPaths(repoRoot, rdiffIncrementsDirName, filePath))
      try:
         increments = os.listdir(parentFolder)
      except OSError:
         increments = []
      increments = filter(lambda x: x.startswith(filename), increments)
      if not increments:
         raise DoesNotExistError()


##### Interfaced Functions #####
def getDirEntries(repoRoot, dirPath):
   """Returns list of rdiffDirEntry objects.  dirPath is relative to repoPath."""
   checkRepoPath(repoRoot, dirPath)

   entryLister = rdiffDirEntries()
   entryLister.init(repoRoot, dirPath)
   entries = entryLister.getDirEntries()
   entriesList = entries.values()

   def sortDirEntries(entry1, entry2):
      if entry1.isDir and not entry2.isDir: return -1
      if not entry1.isDir and entry2.isDir: return 1
      return cmp(entry1.name.upper(), entry2.name.upper())
   entriesList.sort(sortDirEntries)
   return entriesList

import tempfile
def restoreFileOrDir(repoRoot, dirPath, filename, restoreDate):
   """ returns a file path to the file.  User is responsible for deleting file, as well as containing dir, after use. """
   checkRepoPath(repoRoot, joinPaths(dirPath, filename))

   restoredFilename = filename
   if restoredFilename == "/":
      restoredFilename = "(root)"

   fileToRestore = joinPaths(repoRoot, dirPath, filename)
   dateString = str(restoreDate.getSeconds())
   rdiffOutputFile = joinPaths(tempfile.mkdtemp(), restoredFilename) # TODO: make so this includes the username
   args = [ "rdiff-backup", "--restore-as-of="+dateString, fileToRestore, rdiffOutputFile ]
   os.spawnvp(os.P_WAIT, args[0], args)
   if not os.access(rdiffOutputFile, os.F_OK):
      raise UnknownError()
   if os.path.isdir(rdiffOutputFile):
      rdw_helpers.recursiveZipDir(rdiffOutputFile, rdiffOutputFile+".zip")
      rdw_helpers.removeDir(rdiffOutputFile)
      rdiffOutputFile = rdiffOutputFile+".zip"
   return rdiffOutputFile

import gzip, re
def getBackupHistory(repoRoot):
   return _getBackupHistory(repoRoot)

def getLastBackupHistoryEntry(repoRoot):
   return _getBackupHistory(repoRoot, 1)[0]

def getBackupHistorySinceDate(repoRoot, date):
   return _getBackupHistory(repoRoot, -1, date)

def _getBackupHistory(repoRoot, numLatestEntries=-1, cutoffDate=None):
   """Returns a list of backupHistoryEntry's"""
   checkRepoPath(repoRoot, "")

   # Get a listing of error log files, and use that to build backup history
   rdiffDir = joinPaths(repoRoot, rdiffDataDirName)
   curEntries = os.listdir(rdiffDir)
   curEntries = filter(lambda x: x.startswith("error_log."), curEntries)
   curEntries.sort()

   if numLatestEntries != -1:
      assert numLatestEntries > 0
      curEntries = curEntries[-numLatestEntries:]
      curEntries.reverse()
   entries = []
   for entryFile in curEntries:
      entry = incrementEntry(entryFile)
      # compare local times because of discrepency between client/server time zones
      if cutoffDate and entry.getDate().getLocalSeconds() < cutoffDate.getLocalSeconds():
         continue

      try:
         if entry.isCompressed():
            errors = gzip.open(joinPaths(rdiffDir, entryFile), "r").read()
         else:
            errors = open(joinPaths(rdiffDir, entryFile), "r").read()
      except IOError:
         errors = "[Unable to read errors file.]"
      try:
         sessionStatsPath = getSessionStatsFile(rdiffDir, entry)
         session_stats = open(sessionStatsPath, "r").read()
         expression = re.compile("SourceFileSize ([0-9]+) ").findall(session_stats)[0]
      except IOError:
         expression = 0
      newEntry = backupHistoryEntry()
      newEntry.date = entry.getDate()
      newEntry.errors = errors
      newEntry.size = int(expression)
      entries.append(newEntry)

   return entries

def getDirRestoreDates(repo, path):
   backupHistory = [ x.date for x in getBackupHistory(repo) ]

   if path != "/":
      (parentPath, dirName) = os.path.split(path)
      dirListing = getDirEntries(repo, parentPath)
      entries = filter(lambda x: x.name == dirName, dirListing)
      if not entries:
         raise DoesNotExistError
      entry = entries[0]

      # Don't allow restores before the dir existed
      backupHistory = filter(lambda x: x > entry.changeDates[0], backupHistory)

      if not entry.exists:
         # If the dir has been deleted, don't allow restores after its deletion
         backupHistory = filter(lambda x: x < entry.changeDates[-1], backupHistory)

   return backupHistory


def backupIsInProgress(repo):
   rdiffDir = joinPaths(repo, rdiffDataDirName)
   mirrorMarkers = os.listdir(rdiffDir)
   mirrorMarkers = filter(lambda x: x.startswith("current_mirror."), mirrorMarkers)
   assert mirrorMarkers
   return len(mirrorMarkers) > 1


##################### Unit Tests #########################

import unittest, time
class libRdiffTest(unittest.TestCase):
   # The temp dir on Mac OS X is a symlink; expand it because of validation against symlinks in paths
   tmpDir = os.path.realpath(tempfile.gettempdir())
   sourceDir = os.path.join(tmpDir, "librdiff-src")
   destDir = os.path.join(tmpDir, "librdiff-dest")
   restoreDir = os.path.join(tmpDir, "librdiff-restore")
   file1 = "test.txt"
   file2 = "test-2.txt"
   dir = "temp"
   currentBackupTime = 0

   def setUp(self):
      self.tearDown()
      # Create files
      os.makedirs(self.sourceDir)
      os.makedirs(self.restoreDir)

      self.writeToFile(os.path.join(self.sourceDir,self.file1), "some text here\n")
      os.makedirs(os.path.join(self.sourceDir, self.dir))
      self.runRdiff()

      self.writeToFile(os.path.join(self.sourceDir,self.file1), "some text here\nand some more text")
      self.writeToFile(os.path.join(self.sourceDir,self.file2), "now in the second file\n")

      self.runRdiff()

      os.remove(os.path.join(self.sourceDir,self.file1))
      self.runRdiff()

      # at the end here there should be three files total:
      # temp
      # test-2.txt
      # test.txt

   def tearDown(self):
      # Remove sandbox dirs
      for sandboxDir in [self.sourceDir, self.destDir, self.restoreDir]:
         if (os.access(sandboxDir, os.F_OK)):
            removeDir(sandboxDir)

   def runRdiff(self):
      libRdiffTest.currentBackupTime = libRdiffTest.currentBackupTime+10000
      os.spawnlp(os.P_WAIT, "rdiff-backup", "rdiff-backup", "--current-time="+str(libRdiffTest.currentBackupTime), self.sourceDir, self.destDir)

   def cleanRestoredFile(self, filePath):
      (containingFolder, file) = os.path.split(filePath)
      removeDir(containingFolder)

   def writeToFile(self, file, text):
      f = open(file, "w")
      f.write(text)
      f.close()

   ################  Start actual tests ###################
   def testGetDirEntries(self):
      try:
         getDirEntries(self.destDir, "/bogus_dir")
      except DoesNotExistError:
         pass
      else:
         assert(False)

      os.symlink("/", self.destDir+"/link")
      try:
         getDirEntries(self.destDir, "/link")
      except AccessDeniedError:
         pass
      else:
         assert(False)
      try:
         getDirEntries(self.destDir+"/link"+self.destDir, "/")
      except AccessDeniedError:
         pass
      else:
         assert(False)
      os.unlink(self.destDir+"/link")

      # Make sure all files are listed
      # Tests that isDir is reported correctly
      entries = getDirEntries(self.destDir, "/")
      assert(len(entries) == 3)
      assert(entries[0].name == "temp")
      assert(entries[0].isDir == True)
      assert(entries[2].exists == False)
      assert(entries[1].exists == True)

      # Test file size of one of the backed-up files (w/o increments)
      assert(entries[1].fileSize == len("now in the second file\n"))

      # Tests that the files created/changed between backups have that reflected in the changeDates dict
      assert(len(entries[0].changeDates) == 1)
      assert(len(entries[1].changeDates) == 1)

      # Tests that the changeDates dict is sorted correctly
      # Tests that changeDates are in local time
      for entry in entries:
         unsortedDates = entry.changeDates[:]
         entry.changeDates.sort()
         assert(unsortedDates == entry.changeDates)

      # Tests that dates on files that exist currently are correct
      restoredFilePath = restoreFileOrDir(self.destDir, "/", self.file2, entries[1].changeDates[0]) # when file was created
      assert(open(restoredFilePath, "r").read() == "now in the second file\n")
      self.cleanRestoredFile(restoredFilePath)

      # Tests that subdirs are backed-up correctly
      entries = getDirEntries(self.destDir, "/temp")
      assert(len(entries) == 0)

   def testGetBackupHistory(self):
      entries = getBackupHistory(self.destDir)
      assert len(entries) == 3
      for entry in entries:
         assert entry.errors == ""
      assert entries[0].size == 15
      assert entries[1].size == 56
      assert entries[2].size == 23

      lastEntry = getLastBackupHistoryEntry(self.destDir)
      assert lastEntry.size == 23

      # Test that timezone differences are ignored
      historyAsOf = lastEntry.date.getUrlString()
      if "+" in historyAsOf:
         historyAsOf = historyAsOf.replace("+", "-")
      else:
         historyAsOf = historyAsOf[:19] + "+" + historyAsOf[20:]

      lastBackupTime = rdw_helpers.rdwTime()
      lastBackupTime.initFromString(historyAsOf)
      entries = getBackupHistorySinceDate(self.destDir, lastBackupTime)
      assert len(entries) == 1

      # Test that no backups are returned one second after the last backup
      historyAsOf = historyAsOf[:18] + "1" + historyAsOf[19:]
      postBackupTime = rdw_helpers.rdwTime()
      postBackupTime.initFromString(historyAsOf)
      assert lastBackupTime.getLocalSeconds() + 1 == postBackupTime.getLocalSeconds()
      entries = getBackupHistorySinceDate(self.destDir, postBackupTime)
      assert len(entries) == 0

   def testRestoreFile(self):
      entries = getBackupHistory(self.destDir)
      restoredFilePath = restoreFileOrDir(self.destDir, "/", self.file1, entries[0].date)
      assert(open(restoredFilePath, "r").read() == "some text here\n")
      self.cleanRestoredFile(restoredFilePath)
      restoredFilePath = restoreFileOrDir(self.destDir, "/", self.file1, entries[1].date)
      assert(open(restoredFilePath, "r").read() == "some text here\nand some more text")
      self.cleanRestoredFile(restoredFilePath)


if __name__ == "__main__":
   print "Called as standalone program; running unit tests..."
   testSuite = unittest.makeSuite(libRdiffTest, 'test')
   testRunner = unittest.TextTestRunner()
   testRunner.run(testSuite)
