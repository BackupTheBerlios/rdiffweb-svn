#!/usr/bin/python

import rdw_config

"""We do no length validation for incoming parameters, since truncated values will
at worst lead to slightly confusing results, but no security risks"""
class mysqlUserDB:
   def __init__(self, configFilePath=None):
      import MySQLdb
      self.configFilePath = configFilePath
      MySQLdb.paramstyle = "pyformat"
      self.userRootCache = {}
      self._connect()

   def userExists(self, username):
      results = self._executeQuery("SELECT Username FROM users WHERE Username = %(user)s", user=username)
      return len(results) == 1

   def areUserCredentialsValid(self, username, password):
      results = self._executeQuery("SELECT Username FROM users WHERE Username = %(user)s AND Password = %(password)s", user=username, password=self._hashPassword(password))
      return len(results) == 1

   def getUserRoot(self, username):
      if not username in self.userRootCache:
         self.userRootCache[username] = self._getUserField(username, "UserRoot")
      return self.userRootCache[username]

   def getUserRepoPaths(self, username):
      if not self.userExists(username): return None
      query = "SELECT RepoPath FROM repos WHERE UserID = %d" % self._getUserID(username)
      repos = [ row[0] for row in self._executeQuery(query)]
      repos.sort(lambda x, y: cmp(x.upper(), y.upper()))
      return repos

   def getUserList(self):
      query = "SELECT UserName FROM users"
      users = [x[0] for x in self._executeQuery(query)]
      return users

   def addUser(self, username):
      if self.userExists(username): raise ValueError
      query = "INSERT INTO users (Username) values (%(user)s)"
      self._executeQuery(query, user=username)

   def deleteUser(self, username):
      if not self.userExists(username): raise ValueError
      self._deleteUserRepos(username)
      query = "DELETE FROM users WHERE Username = %(user)s"
      self._executeQuery(query, user=username)

   def setUserInfo(self, username, userRoot, isAdmin):
      if not self.userExists(username): raise ValueError
      if isAdmin:
         adminInt = 1
      else:
         adminInt = 0
      query = "UPDATE users SET UserRoot=%(userRoot)s, IsAdmin="+str(adminInt)+" WHERE Username = %(user)s"
      self._executeQuery(query, userRoot=userRoot, user=username)
      self.userRootCache[username] = userRoot # update cache

   def setUserRepos(self, username, repoPaths):
      if not self.userExists(username): raise ValueError
      userID = self._getUserID(username)
      self._deleteUserRepos(username)
      query = "INSERT INTO repos (UserID, RepoPath) values ("+str(userID)+", %(repo)s)"
      repoPaths = [ {"repo" : repo} for repo in repoPaths ]
      cursor = self.sqlConnection.cursor()
      cursor.executemany(query, repoPaths)

   def setUserPassword(self, username, password):
      if not self.userExists(username): raise ValueError
      query = "UPDATE users SET Password=%(password)s WHERE Username=%(user)s"
      self._executeQuery(query, password=self._hashPassword(password), user=username)

   def userIsAdmin(self, username):
      return bool(self._getUserField(username, "IsAdmin"))

   ########## Helper functions ###########
   def _deleteUserRepos(self, username):
      if not self.userExists(username): raise ValueError
      self._executeQuery("DELETE FROM repos WHERE UserID=%d" % self._getUserID(username))

   def _getUserField(self, username, fieldName):
      if not self.userExists(username): return None
      query = "SELECT "+fieldName+" FROM users WHERE Username = %(user)s"
      results = self._executeQuery(query, user=username)
      assert len(results) == 1
      return results[0][0]

   def _getUserID(self, username):
      assert self.userExists(username)
      query = "SELECT UserID FROM users WHERE Username = %(user)s"
      results = self._executeQuery(query, user=username)
      assert len(results) == 1
      return int(results[0][0])

   def _internalExecuteQuery(self, query, **kwargs):
      cursor = self.sqlConnection.cursor()
      cursor.execute(query, kwargs)
      return cursor.fetchall()

   def _executeQuery(self, query, **kwargs):
      # The mysql server connection times out after a while.  Catch this, and try again
      import MySQLdb
      try:
         return self._internalExecuteQuery(query, **kwargs)
      except MySQLdb.OperationalError:
         self._connect()
         return self._internalExecuteQuery(query, **kwargs)

   def _connect(self):
      import MySQLdb
      sqlHost = rdw_config.getConfigSetting("sqlHost", self.configFilePath)
      sqlUsername = rdw_config.getConfigSetting("sqlUsername", self.configFilePath)
      sqlPassword = rdw_config.getConfigSetting("sqlPassword", self.configFilePath)
      sqlDatabaseName = rdw_config.getConfigSetting("sqlDatabase", self.configFilePath)
      self.sqlConnection = MySQLdb.connect(host=sqlHost, user=sqlUsername, passwd=sqlPassword,db=sqlDatabaseName)

   def _hashPassword(self, password):
      import sha
      hasher = sha.new()
      hasher.update(password)
      return hasher.hexdigest()

   def _getCreateStatements(self):
      return ["""create table users ( UserID int(11) NOT NULL auto_increment,
               Username varchar (50) binary unique NOT NULL,
               Password varchar (40) NOT NULL DEFAULT "",
               UserRoot varchar (255) NOT NULL DEFAULT "",
               IsAdmin tinyint NOT NULL DEFAULT FALSE,
               primary key (UserID) )""",
               """create table repos ( RepoID int(11) NOT NULL auto_increment,
               UserID int(11) NOT NULL, 
               RepoPath varchar (255) NOT NULL,
               primary key (RepoID))"""]


##################### Unit Tests #########################

import unittest, os
class mysqlUserDBTest(unittest.TestCase):
   """Unit tests for the mysqlUserDBTest class"""
   configFileData = """sqlHost=localhost
                       sqlUsername=
                       sqlPassword=
                       sqlDatabase=test"""
   configFilePath = "/tmp/rdw_config.conf"

   def setUp(self):
      file = open(self.configFilePath, "w")
      file.write(self.configFileData)
      file.close()
      self.tearDown()
      file = open(self.configFilePath, "w")
      file.write(self.configFileData)
      file.close()
      userData = mysqlUserDB(self.configFilePath)
      for statement in userData._getCreateStatements():
         userData._executeQuery(statement)

      userData.addUser("test")
      userData.setUserInfo("test", "/data", False)
      userData.setUserPassword("test", "user")
      userData.setUserRepos("test", ["/data/bill", "/data/frank"])

   def tearDown(self):
      userData = mysqlUserDB(self.configFilePath)
      userData._executeQuery("DROP TABLE IF EXISTS users;")
      userData._executeQuery("DROP TABLE IF EXISTS repos;")
      if (os.access(self.configFilePath, os.F_OK)):
         os.remove(self.configFilePath)

   def testValidUser(self):
      authModule = mysqlUserDB(self.configFilePath)
      assert(authModule.userExists("test"))
      assert(authModule.areUserCredentialsValid("test", "user"))

   def testUserTruncation(self):
      import MySQLdb
      authModule = mysqlUserDB(self.configFilePath)
      authModule.addUser("bill" * 1000)
      try:
         authModule.addUser("bill" * 1000 + "test")
      except MySQLdb.IntegrityError:
         pass
      else:
         assert(false)

   def testUserList(self):
      authModule = mysqlUserDB(self.configFilePath)
      assert(authModule.getUserList() == ["test"])

   def testUserInfo(self):
      authModule = mysqlUserDB(self.configFilePath)
      assert(authModule.getUserRoot("test") == "/data")
      assert(authModule.userIsAdmin("test") == False)

   def testBadPassword(self):
      authModule = mysqlUserDB(self.configFilePath)
      assert(not authModule.areUserCredentialsValid("test", "user2")) # Basic test
      assert(not authModule.areUserCredentialsValid("test", "User")) # password is case sensitive
      assert(not authModule.areUserCredentialsValid("test", "use")) # Match entire password
      assert(not authModule.areUserCredentialsValid("test", "")) # Match entire password

   def testBadUser(self):
      authModule = mysqlUserDB(self.configFilePath)
      assert(not authModule.userExists("Test")) # username is case sensitive
      assert(not authModule.userExists("tes")) # Match entire username

   def testGoodUserDir(self):
      userDataModule = mysqlUserDB(self.configFilePath)
      assert(userDataModule.getUserRepoPaths("test") == ["/data/bill", "/data/frank"])
      assert(userDataModule.getUserRoot("test") == "/data")

   def testBadUserReturn(self):
      userDataModule = mysqlUserDB(self.configFilePath)
      assert(not userDataModule.getUserRepoPaths("test2")) # should return None if user doesn't exist
      assert(not userDataModule.getUserRoot("")) # should return None if user doesn't exist

if __name__ == "__main__":
   print "Called as standalone program; running unit tests..."
   mysqlDataTest = unittest.makeSuite(mysqlUserDBTest, 'test')
   testRunner = unittest.TextTestRunner()
   testRunner.run(mysqlDataTest)
