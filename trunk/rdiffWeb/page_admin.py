#!/usr/bin/python

import cherrypy

import email_notification
import page_main
import rdw_helpers
import rdw_templating
import rdw_spider_repos


class rdiffAdminPage(page_main.rdiffPage):
   def index(self, **kwargs):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")
      
      # If we're just showing the initial page, just do that
      if not self._isSubmit():
         return self._generatePageHtml("", "")
      
      # We need to change values. Change them, then give back that main page again, with a message
      action = cherrypy.request.params["action"]
      if action == "edit" or action == "add":
         username = cherrypy.request.params["username"]
         userRoot = cherrypy.request.params["userRoot"]
         userIsAdmin = cherrypy.request.params.get("isAdmin", False) != False
      
      if action == "edit":
         if not self.getUserDB().userExists(username):
            return self._generatePageHtml("", "The user does not exist.")
         
         self.getUserDB().setUserInfo(username, userRoot, userIsAdmin)
         return self._generatePageHtml("User information modified successfully", "")
      elif action == "add":
         if self.getUserDB().userExists(username):
            return self._generatePageHtml("", "The specified user already exists.", username, userRoot, userIsAdmin)
         if username == "":
            return self._generatePageHtml("", "The username is invalid.", username, userRoot, userIsAdmin)
         self.getUserDB().addUser(username)
         self.getUserDB().setUserPassword(username, cherrypy.request.params["password"])
         self.getUserDB().setUserInfo(username, userRoot, userIsAdmin)
         return self._generatePageHtml("User added successfully.", "")
      elif action == "sendEmails":
         return self._sendEmails()
      elif action == "changeNotifications":
         return self._changeNotifications(kwargs)
      
   index.exposed = True

   def deleteUser(self, user):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")

      if not self.getUserDB().userExists(user):
         return self._generatePageHtml("", "The user does not exist.")

      if user == self.getUsername():
         return self._generatePageHtml("", "You cannot remove your own account!.")

      self.getUserDB().deleteUser(user)
      return self._generatePageHtml("User account removed.", "")
   deleteUser.exposed = True

   def _sendEmails(self):
      if not self._userIsAdmin(): return self.writeErrorPage("Access denied.")

      emailNotifier = email_notification.emailNotifier()
      if emailNotifier.notificationsEnabled():
         emailNotifier.sendEmails()
         return self._generatePageHtml("Email notifications sent.", "")
      else:
         return self._generatePageHtml("", "Email notifications are disabled.")

   def _changeNotifications(self, parms):
      if not self.getUserDB().modificationsSupported():
         return self._getPrefsPage(errorMessage="Email notification is not supported with the active user database.")

      users = self.getUserDB().getUserList()
      notify_options = email_notification.loadNotificationsTableResults(parms)
      for option in notify_options:
         if option in users:
            self.getUserDB().setAdminMonitoredRepoMaxAge(option, notify_options[option])

      return self._generatePageHtml("Successfully changed notifications.", "")
      

   ############### HELPER FUNCTIONS #####################
   def _userIsAdmin(self):
      return self.getUserDB().userIsAdmin(self.getUsername())

   def _isSubmit(self):
      return cherrypy.request.method == "POST"

   def _generatePageHtml(self, message, error, username="", userRoot="", isAdmin=False):
      userNames = self.getUserDB().getUserList()
      users = [{
         "username" : user,
         "isAdmin" : self.getUserDB().userIsAdmin(user),
         "userRoot" : self.getUserDB().getUserRoot(user)
      } for user in userNames]

      notificationsEnabled = email_notification.notificationsEnabled(self.getUserDB())
      notificationsTable = ''
      if notificationsEnabled:
         options = {}
         for user in userNames:
            options[user] = self.getUserDB().getAdminMonitoredRepoMaxAge(user)
         notificationsTable = email_notification.buildNotificationsTable(options)

      parms = { "users" : users, 
                "username" : username, 
                "userRoot" : userRoot, 
                "isAdmin" : isAdmin,
                "message" : message,
                "notificationsEnabled" : notificationsEnabled,
                "notificationsTable" : notificationsTable,
                "userEmail" : self.getUserDB().getUserEmail(user),
                "error" : error }
      return self.startPage("Administration") + self.compileTemplate("admin_main.html", **parms) + self.endPage()

