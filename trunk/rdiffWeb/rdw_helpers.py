#!/usr/bin/python

import os, time, datetime, re, calendar, urllib

def joinPaths(parentPath, *args):
   args = [x.lstrip("/") for x in args]
   return os.path.join(parentPath, *args)

class accessDeniedError:
   def __str__(self):
      return "Access is denied."

def ensurePathValid(path):
   normalizedPath = os.path.normpath(path)
   if normalizedPath != path:
      raise accessDeniedError

def encodeUrl(url):
   if not url: return url
   return urllib.quote_plus(url)

def decodeUrl(encodedUrl):
   if not encodedUrl: return encodedUrl
   return urllib.unquote_plus(encodedUrl)

def removeDir(dir):
   for root, dirs, files in os.walk(dir, topdown=False):
      for name in files:
         filePath = os.path.join(root, name)
         if os.path.islink(filePath):
            os.unlink(filePath)
         else:
            os.remove(filePath)
      for name in dirs:
         dirPath = os.path.join(root, name)
         if os.path.islink(dirPath):
            os.unlink(dirPath)
         else:
            os.rmdir(dirPath)
   os.rmdir(dir)

def formatNumStr(num, maxDecimals):
   numStr = "%.*f" % (maxDecimals, num)
   def replaceFunc(match):
      if match.group(1):
         return "."+match.group(1)
      return ""
   return re.compile("\.([^0]*)[0]+$").sub(replaceFunc, numStr)

def formatFileSizeStr(filesize):
   if filesize == 0: return "0 bytes"

   sizeNames = [(1024*1024*1024*1024, "TB"), (1024*1024*1024, "GB"), (1024*1024, "MB"), (1024, "KB"), (1, "bytes")]
   for (size, name) in sizeNames:
      if 1.0*filesize / size >= 1.0:
         return formatNumStr(1.0*filesize / size, 2) + " " + name

   (filesize, name) = sizeNames[-1]
   return formatNumStr(1.0*filesize / size, 2) + " " + name

class rdwTime:
   """Time information has two components: the local time, stored in GMT as seconds since Epoch,
   and the timezone, stored as a seconds offset.  Since the server may not be in the same timezone
   as the user, we cannot rely on the built-in localtime() functions, but look at the rdiff-backup string
   for timezone information.  As a general rule, we always display the "local" time, but pass the timezone
   information on to rdiff-backup, so it can restore to the correct state"""
   def __init__(self):
      self.timeInSeconds = 0
      self.tzOffset = 0

   def initFromCurrentUTC(self):
      self.timeInSeconds = time.time()
      self.tzOffset = 0

   def initFromMidnightUTC(self, daysFromToday):
      self.timeInSeconds = time.time()
      self.timeInSeconds -= self.timeInSeconds % (24*60*60)
      self.timeInSeconds += daysFromToday * 24*60*60
      self.tzOffset = 0

   def initFromString(self, timeString):
      try:
         date, daytime = timeString[:19].split("T")
         year, month, day = map(int, date.split("-"))
         hour, minute, second = map(int, daytime.split(":"))
         assert 1900 < year < 2100, year
         assert 1 <= month <= 12
         assert 1 <= day <= 31
         assert 0 <= hour <= 23
         assert 0 <= minute <= 59
         assert 0 <= second <= 61  # leap seconds

         timetuple = (year, month, day, hour, minute, second, -1, -1, 0)
         self.timeInSeconds = calendar.timegm(timetuple)
         self.tzOffset = self.tzdtoseconds(timeString[19:])
         self.getTimeZoneString() # to get assertions there

      except (TypeError, ValueError, AssertionError):
         raise ValueError

   def getLocalDaysSinceEpoch(self):
      return self.getLocalSeconds() // (24*60*60)

   def getDaysSinceEpoch(self):
      return self.getSeconds() // (24*60*60)

   def getLocalSeconds(self):
      return self.timeInSeconds

   def getSeconds(self):
      return self.timeInSeconds+self.tzOffset

   def getDateDisplayString(self):
      return time.strftime("%Y-%m-%d", time.gmtime(self.timeInSeconds))

   def getDisplayString(self):
      return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.timeInSeconds))

   def getUrlString(self):
      return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self.timeInSeconds))+self.getTimeZoneString()

   def getUrlStringNoTZ(self):
      return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self.timeInSeconds+self.tzOffset))+"Z"

   def getTimeZoneString(self):
      if not self.tzOffset: return "Z"

      hours, minutes = map(abs, divmod(self.tzOffset/60, 60))
      assert 0 <= hours <= 23
      assert 0 <= minutes <= 59
      return "-%02d:%02d" % (hours, minutes)

   def tzdtoseconds(self, tzd):
      """Given w3 compliant TZD, return how far ahead UTC is"""
      if tzd == "Z": return 0
      assert len(tzd) == 6 # only accept forms like +08:00 for now
      assert (tzd[0] == "-" or tzd[0] == "+") and tzd[3] == ":"
      return -60 * (60 * int(tzd[:3]) + int(tzd[4:]))

   def __cmp__(self, other):
      return cmp(self.getSeconds(), other.getSeconds())

class groupby(dict):
    def __init__(self, seq, key=lambda x:x):
        for value in seq:
            k = key(value)
            self.setdefault(k, []).append(value)
    __iter__ = dict.iteritems


# Taken from ASPN: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/278731
def daemonize():
   """Detach a process from the controlling terminal and run it in the
   background as a daemon. """
   if (hasattr(os, "devnull")):
      REDIRECT_TO = os.devnull
   else:
      REDIRECT_TO = "/dev/null"
   MAXFD = 1024
   UMASK = 0

   try:
      pid = os.fork()
   except OSError, e:
      raise Exception, "%s [%d]" % (e.strerror, e.errno)

   if (pid == 0): # The first child.
      os.setsid()
      try:
         pid = os.fork()   # Fork a second child.
      except OSError, e:
         raise Exception, "%s [%d]" % (e.strerror, e.errno)

      if (pid == 0): # The second child.
         os.umask(UMASK)
      else:
         os._exit(0) # Exit parent (the first child) of the second child.
   else:
      os._exit(0) # Exit parent of the first child.

# Redirecting output to /dev/null fails when called from a script, for some reason...
#    import resource      # Resource usage information.
#    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
#    if (maxfd == resource.RLIM_INFINITY):
#       maxfd = MAXFD
#    for fd in range(0, maxfd):
#       try:
#          os.close(fd)
#       except OSError:   # ERROR, fd wasn't open to begin with (ignored)
#          pass
#    os.open(REDIRECT_TO, os.O_RDWR)  # standard input (0)
#    os.dup2(0, 1)        # standard output (1)
#    os.dup2(0, 2)        # standard error (2)
   return(0)


import unittest
class helpersTest(unittest.TestCase):
   def testJoinPaths(self):
      assert(joinPaths("/", "/test", "/temp.txt") == "/test/temp.txt")
      assert(joinPaths("/", "test", "/temp.txt") == "/test/temp.txt")
      assert(joinPaths("/", "/test", "temp.txt") == "/test/temp.txt")
      assert(joinPaths("/", "//test", "/temp.txt") == "/test/temp.txt")
      assert(joinPaths("/", "", "/temp.txt") == "/temp.txt")
      assert(joinPaths("test", "", "/temp.txt") == "test/temp.txt")

   def testRdwTime(self):
      # Test initialization
      myTime = rdwTime()
      assert myTime.getSeconds() == 0
      goodTimeString = "2005-12-25T23:34:15-05:00"
      goodTimeStringNoTZ = "2005-12-26T04:34:15Z"
      myTime.initFromString(goodTimeString)

      myTimeNoTZ = rdwTime()
      myTimeNoTZ.initFromString(goodTimeStringNoTZ)
      assert myTimeNoTZ.getSeconds() == myTimeNoTZ.getLocalSeconds()
      assert myTime.getSeconds() == myTimeNoTZ.getSeconds()

      # Test correct load and retrieval
      assert myTime.getUrlString() == goodTimeString
      assert myTime.getUrlStringNoTZ() == goodTimeStringNoTZ
      assert myTime.getDisplayString() == "2005-12-25 23:34:15"

      assert myTime.getDateDisplayString() == "2005-12-25"
      assert myTime.getLocalSeconds() < myTime.getSeconds()
      assert myTime.getLocalSeconds() == 1135571655 - 5*60*60
      assert myTime.getSeconds() == 1135571655
      assert myTime.getLocalDaysSinceEpoch() <= myTime.getDaysSinceEpoch()
      assert myTime.getLocalDaysSinceEpoch() == 13142
      assert myTime.getDaysSinceEpoch() == 13143

      # Test boundaries on days since epoch
      myTime.initFromString("2005-12-31T18:59:59-05:00")
      assert myTime.getUrlStringNoTZ() == "2005-12-31T23:59:59Z"
      assert myTime.getDaysSinceEpoch() == 13148
      assert myTime.getLocalDaysSinceEpoch() == 13148

      myTime.initFromString("2005-12-31T19:00:00-05:00")
      assert myTime.getUrlStringNoTZ() == "2006-01-01T00:00:00Z"
      assert myTime.getDaysSinceEpoch() == 13149
      assert myTime.getLocalDaysSinceEpoch() == 13148

      # Test UTC
      myTime.initFromCurrentUTC()
      assert myTime.getSeconds() == myTime.getLocalSeconds()
      todayAsString = myTime.getDateDisplayString()

      # Test midnight UTC
      myTime.initFromMidnightUTC(0)
      assert myTime.getSeconds() == myTime.getLocalSeconds()
      assert myTime.getUrlString().find("T00:00:00Z") != -1
      assert myTime.getDateDisplayString() == todayAsString

      # Make sure it rejects bad strings with the appropriate exceptions
      badTimeStrings = ["2005-12X25T23:34:15-05:00", "20005-12-25T23:34:15-05:00", "2005-12-25", "2005-12-25 23:34:15"]
      for badTime in badTimeStrings:
         try:
            myTime.initFromString(badTime)
         except ValueError:
            pass
         else:
            assert False

   def testFormatSizeStr(self):
      # Test simple values
      assert(formatFileSizeStr(1024) == "1 KB")
      assert(formatFileSizeStr(1024*1024*1024) == "1 GB")
      assert(formatFileSizeStr(1024*1024*1024*1024) == "1 TB")

      assert(formatFileSizeStr(0) == "0 bytes")
      assert(formatFileSizeStr(980) == "980 bytes")
      assert(formatFileSizeStr(1024*980) == "980 KB")
      assert(formatFileSizeStr(1024*1024*1024*1.2) == "1.2 GB")
      assert(formatFileSizeStr(1024*1024*1024*1.243) == "1.24 GB") # Round to one decimal
      assert(formatFileSizeStr(1024*1024*1024*1024*120) == "120 TB") # Round to one decimal

   def testGroupBy(self):
      numbers = [1,2,3,4,5,6,0,0,5,5]
      groupedNumbers = groupby(numbers)
      assert groupedNumbers == {0: [0, 0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5,5,5], 6: [6]}

      projects = [{"name": "rdiffWeb", "language": "python"}, {"name": "CherryPy", "language": "python"},
         {"name": "librsync", "language": "C"}]
      projectsByLanguage = groupby(projects, lambda x: x["language"])
      assert projectsByLanguage == {"C": [{"name": "librsync", "language": "C"}],
         "python": [{"name": "rdiffWeb", "language": "python"}, {"name": "CherryPy", "language": "python"}]}

if __name__ == "__main__":
   print "Called as standalone program; running unit tests..."
   testSuite = unittest.makeSuite(helpersTest, 'test')
   testRunner = unittest.TextTestRunner()
   testRunner.run(testSuite)
