#!/usr/bin/python

import os
import db_mysql, rdw_helpers, librdiff

def findRdiffRepos(dirToSearch, outRepoPaths):
   dirEntries = os.listdir(dirToSearch)
   if librdiff.rdiffDataDirName in dirEntries:
      print "   Found repo at " + dirToSearch
      outRepoPaths.append(dirToSearch)
      return

   for entry in dirEntries:
      entryPath = rdw_helpers.joinPaths(dirToSearch, entry)
      if os.path.isdir(entryPath) and not os.path.islink(entryPath):
         findRdiffRepos(entryPath, outRepoPaths)


def findReposForUsers(user, userDBModule):
   userRoot = userDBModule.getUserRoot(user)
   repoPaths = []
   findRdiffRepos(userRoot, repoPaths)

   def stripRoot(path):
      if not path[len(userRoot):]:
         return "/"
      return path[len(userRoot):]
   repoPaths = map(stripRoot, repoPaths)
   userDBModule.setUserRepos(user, repoPaths)


def main():
   userDBModule = db_mysql.mysqlUserDB()
   users = userDBModule.getUserList()
   for user in users:
      print "Adding repos for user %s..." % user
      findReposForUsers(user, userDBModule)


if __name__ == "__main__":
   main()
