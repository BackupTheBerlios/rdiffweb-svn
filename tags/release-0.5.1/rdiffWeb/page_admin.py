#!/usr/bin/python

import rdw_helpers
import page_main
import rdw_templating
import cherrypy
import rdw_spider_repos


class rdiffAdminPage(page_main.rdiffPage):
   def index(self, **kwargs):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")
      
      # If we're just showing the initial page, just do that
      if not self._isSubmit():
         return self._generatePageHtml("", "")
      
      # We need to change values. Change them, then give back that main page again, with a message
      action = cherrypy.request.paramMap["action"]
      username = cherrypy.request.paramMap["username"]
      password = cherrypy.request.paramMap["password"]
      userRoot = cherrypy.request.paramMap["userRoot"]
      userIsAdmin = cherrypy.request.paramMap.get("isAdmin", False) != False
      
      if action == "edit":
         if not self.userDB.userExists(username):
            return self._generatePageHtml("", "The user does not exist.")
         
         self.userDB.setUserInfo(username, userRoot, userIsAdmin)
         return self._generatePageHtml("User information modified successfully", "")
      elif action == "add":
         if self.userDB.userExists(username):
            return self._generatePageHtml("", "The specified user already exists.", username, userRoot, userIsAdmin)
         if username == "":
            return self._generatePageHtml("", "The username is invalid.", username, userRoot, userIsAdmin)
         self.userDB.addUser(username)
         self.userDB.setUserPassword(username, password)
         self.userDB.setUserInfo(username, userRoot, userIsAdmin)
         return self._generatePageHtml("User added successfully.", "")
      
   index.exposed = True

   def deleteUser(self, user):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")

      if not self.userDB.userExists(user):
         return self._generatePageHtml("", "The user does not exist.")

      if user == self.getUsername():
         return self._generatePageHtml("", "You cannot remove your own account!.")

      self.userDB.deleteUser(user)
      return self._generatePageHtml("User account removed.", "")
   deleteUser.exposed = True

   ############### HELPER FUNCTIONS #####################
   def _userIsAdmin(self):
      return self.userDB.userIsAdmin(self.getUsername())

   def _isSubmit(self):
      return cherrypy.request.method == "POST"

   def _generatePageHtml(self, message, error, username="", userRoot="", isAdmin=False):
      userNames = self.userDB.getUserList()
      users = [ { "username" : user, "isAdmin" : self.userDB.userIsAdmin(user), "userRoot" : self.userDB.getUserRoot(user) } for user in userNames ]
      parms = { "users" : users, 
                "username" : username, 
                "userRoot" : userRoot, 
                "isAdmin" : isAdmin,
                "message" : message,
                "error" : error }
      return self.startPage("Administration") + self.compileTemplate("admin_main.html", **parms) + self.endPage()

