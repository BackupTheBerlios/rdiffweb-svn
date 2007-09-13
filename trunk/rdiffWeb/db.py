#!/usr/bin/python

import rdw_config

class userDB:
   def getUserDBModule(self):
      authModuleSetting = rdw_config.getConfigSetting("UserDB");
      if authModuleSetting.lower() == "file":
         import db_file
         return db_file.fileUserDB()
      if authModuleSetting.lower() == "mysql":
         import db_mysql
         return db_mysql.mysqlUserDB()
      assert(False)
      
   def modificationsSupported(self):
      return False

   def areUserCredentialsValid(self, username, password):
      raise NotImplementedError

   def getUserRoot(self, username):
      raise NotImplementedError

   def getUserRepoPaths(self, username):
      raise NotImplementedError

   def getUserEmail(self, username):
      raise NotImplementedError
   
   def getUserList(self):
      raise NotImplementedError

   def addUser(self, username):
      raise NotImplementedError

   def deleteUser(self, username):
      raise NotImplementedError

   def setUserInfo(self, username, userRoot, isAdmin):
      raise NotImplementedError
   
   def setUserEmail(self, userEmail):
      raise NotImplementedError

   def setUserRepos(self, username, repos):
      raise NotImplementedError

   def setUserPassword(self, username, password):
      raise NotImplementedError

   def getUserRoot(self, username):
      raise NotImplementedError

   def userIsAdmin(self, username):
      raise NotImplementedError

