#!/usr/bin/python

import rdw_helpers
import page_main
import rdw_templating
import cherrypy
import rdw_spider_repos

class userDBFormValues:
   def __init__(self):
      self.valuesDict = {}

   def loadFromDatabase(self, user, userDBModule):
      if not userDBModule.userExists(user): return

      self.valuesDict["username"] = user
      self.valuesDict["userRoot"] = userDBModule.getUserRoot(user)
      self.valuesDict["isAdmin"] = userDBModule.userIsAdmin(user)

   def loadFromPostData(self, user, paramMap):
      self.valuesDict["username"] = user
      self.valuesDict["userRoot"] = paramMap.get("userRoot", "")
      self.valuesDict["isAdmin"] = paramMap.get("isAdmin", False)
      self.valuesDict["password"] = paramMap.get("password", False)

   def validateValues(self, addingUser):
      if not self.valuesDict.get("username"):
         return "The username must be specified."
      if addingUser and not self.valuesDict.get("password"):
         return "The password must be specified."
      if not self.valuesDict.get("userRoot"):
         return "The user's root folder must be specified."
      return ""

   def saveToDatabase(self, addingUser, userDBModule):
      if self.validateValues(addingUser): assert False
      if addingUser:
         userDBModule.addUser(self.getValue("username"))
         userDBModule.setUserPassword(self.getValue("username"), self.getValue("password"))
      userDBModule.setUserInfo(self.getValue("username"), self.getValue("userRoot"), self.getValue("isAdmin"))

   def generateFormHtml(self, addingUser, showError, page):

      errors = ""
      if showError: errors = self.validateValues(addingUser)
      parmsDict = { "username" : self.getValue("username"), "userRoot" : self.getValue("userRoot"), "isAdmin" : str(self.getValue("isAdmin")), "error" : errors }
      if addingUser:
         parmsDict["password"]=""
         parmsDict["submitUrl"]="addUser"
         parmsDict["action"]="Add User"
         template = "admin_add_user.html"
      else:
         parmsDict["submitUrl"]="editUser"
         parmsDict["action"]="Edit User"
         template = "admin_edit_user.html"

      return page.compileTemplate(template, **parmsDict)

   def getValue(self, valueName):
      return self.valuesDict.get(valueName, "")

   def setValue(self, valueName, value):
      self.valuesDict[valueName, value]



class rdiffAdminPage(page_main.rdiffPage):
   def index(self):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")

      page = self.startPage("Administration")
      userNames = self.userDB.getUserList()
      users = [ { "username" : user } for user in userNames ]
      parms = { "users" : users, "addUserUrl" : "/admin/addUser" } ]
      page = page + self.compileTemplate("admin_main.html", **parms)
      return page + self.endPage()
   index.exposed = True

   def addUser(self, username="", password="", firstName="", lastName="", userRoot="", isAdmin=False):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")

      formVals = userDBFormValues()
      if self._isSubmit():
         formVals = userDBFormValues()
         formVals.loadFromPostData(username, cherrypy.request.paramMap)
         error = formVals.validateValues(True)
         if not error:
            formVals.saveToDatabase(True, self.userDB)
            return self.writeMessagePage("Success", "User added successfully.")

      page = self.startPage("Add User")
      page = page + formVals.generateFormHtml(True, self._isSubmit(), self)
      return page + self.endPage()
   addUser.exposed = True

   def editUser(self, user, firstName="", lastName="", userRoot="", isAdmin=""):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")

      formVals = userDBFormValues()
      if self._isSubmit():
         formVals.loadFromPostData(user, cherrypy.request.paramMap)
         error = formVals.validateValues(False)
         if not error:
            formVals.saveToDatabase(False, self.userDB)
            return self.writeMessagePage("Success", "User modified successfully.")
      else:
         formVals.loadFromDatabase(user, self.userDB)

      page = self.startPage("Edit User")
      page = page + formVals.generateFormHtml(False, self._isSubmit(), self)
      return page + self.endPage()
   editUser.exposed = True

   def deleteUser(self, user):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")
      if not self.userDB.userExists(user): return

      self.userDB.deleteUser(user)
      return self.writeMessagePage("Success", "User account removed.")

   deleteUser.exposed = True

   def changePassword(self, user, password=""):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")
      if not self.userDB.userExists(user): return

      if self._isSubmit():
         self.userDB.setUserPassword(user, password)
         if not password:
            return self.writeMessagePage("Success", "Password cleared, account disabled.")
         else:
            return self.writeMessagePage("Success", "Password modified successfully.")

      page = self.startPage("Change User Password")
      page = page + self.compileTemplate("admin_change_password.html", username=user)
      return page + self.endPage()
   changePassword.exposed = True

   def updateRepos(self, user):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")
      if not self.userDB.userExists(user): return
      rdw_spider_repos.findReposForUser(user, self.userDB)
      return self.writeMessagePage("Success", "Successfully updated repositories.")
   updateRepos.exposed = True

   ############### HELPER FUNCTIONS #####################
   def _userIsAdmin(self):
      return self.userDB.userIsAdmin(self.getUsername())

   def _isSubmit(self):
      return cherrypy.request.method == "POST"



