#!/usr/bin/python

class userDB:
   def modificationsSupported(self):
      return False

   def areUserCredentialsValid(self, username, password):
      raise NotImplementedError

   def getUserRoot(self, username):
      raise NotImplementedError

   def getUserRepoPaths(self, username):
      raise NotImplementedError

   def getUserList(self):
      raise NotImplementedError

   def addUser(self, username):
      raise NotImplementedError

   def deleteUser(self, username):
      raise NotImplementedError

   def setUserInfo(self, username, userRoot, isAdmin):
      raise NotImplementedError

   def setUserRepos(self, username, repos):
      raise NotImplementedError

   def setUserPassword(self, username, password):
      raise NotImplementedError

   def getUserRoot(self, username):
      raise NotImplementedError

   def userIsAdmin(self, username):
      raise NotImplementedError


