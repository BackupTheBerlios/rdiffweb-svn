#!/usr/bin/python

import cherrypy
try:
   from cherrypy.filters.basefilter import BaseFilter
except:
   from cherrypy.lib.filter.basefilter import BaseFilter
import page_main
import rdw_helpers
import base64

class rdwAuthenticationFilter(BaseFilter):
   loginUrl = "/doLogin"
   logoutUrl = "/doLogout"
   sessionUserNameKey = "username"

   def beforeMain(self):
      if not cherrypy.config.get("rdwAuthenticateFilter.on", False):
         return
      checkLoginAndPassword = cherrypy.config.get("rdwAuthenticateFilter.checkLoginAndPassword", lambda username, password: u"Wrong login/password")

      if cherrypy.request.path == self.logoutUrl:
         cherrypy.session[self.sessionUserNameKey] = None
         cherrypy.request.user = None
         raise cherrypy.HTTPRedirect("/")

      elif cherrypy.session.get(self.sessionUserNameKey):
         # page passes credentials; allow to be processed
         if cherrypy.request.path == self.loginUrl:
            raise cherrypy.HTTPRedirect("/")
         return

      if cherrypy.config.get("rdwAuthenticateFilter.method", "") == "HTTP Header":
         # if not already authenticated, authenticate via the Authorization header
         httpAuth = self._getHTTPAuthorizationCredentials(cherrypy.request.headerMap.get("Authorization", ""))
         if httpAuth:
            error = checkLoginAndPassword(httpAuth["login"], httpAuth["password"])
            if not error:
               return
         else:
            error = ""

         cherrypy.response.status = "401 Unauthorized"
         cherrypy.response.body = "Not Authorized\n" + error
         cherrypy.response.headerMap["WWW-Authenticate"] = 'Basic realm="cherrypy"'
         return

      loginKey = "login"
      passwordKey = "password"
      redirectKey = "redirect"

      loginParms = {"message": "", "action": self.loginUrl,
         "loginKey": loginKey, "passwordKey": passwordKey, "redirectKey": redirectKey,
         "loginValue": "", "redirectValue": cherrypy.request.path + "?" + cherrypy.request.queryString }

      if cherrypy.request.path == self.loginUrl and cherrypy.request.method == "POST":
         # check for login credentials
         loginValue = cherrypy.request.paramMap[loginKey]
         passwordValue = cherrypy.request.paramMap[passwordKey]
         redirectValue = cherrypy.request.paramMap[redirectKey]
         errorMsg = checkLoginAndPassword(loginValue, passwordValue)
         if not errorMsg:
            cherrypy.session[self.sessionUserNameKey] = loginValue
            if not redirectValue:
               redirectValue = "/"
            raise cherrypy.HTTPRedirect(redirectValue)

         # update form values
         loginParms["message"] = errorMsg
         loginParms["loginValue"] = loginValue
         loginParms["redirectValue"] = redirectValue

      # write login page
      loginPage = page_main.rdiffPage()
      cherrypy.response.body = loginPage.compileTemplate("login.html", **loginParms)
      cherrypy.request.execute_main = False      

   def _getHTTPAuthorizationCredentials(self, authHeader):
      try:
         (realm, authEnc) = authHeader.split()
      except ValueError:
         return None

      if realm.lower() == "basic":
         auth = base64.decodestring(authEnc)
         colon = auth.find(":")
         if colon != -1:
            return { "login": auth[:colon], "password": auth[colon+1:] }
         else:
            return { "login": auth, "password": "" }

      return None

##################### Unit Tests #########################

import unittest, os
class rdwAuthenticationFilterTest(unittest.TestCase):
   """Unit tests for the rdwAuthenticationFilter class"""

   def testAuthorization(self):
      filter = rdwAuthenticationFilter()
      assert not filter._getHTTPAuthorizationCredentials("")
      assert not filter._getHTTPAuthorizationCredentials("Basic Username Password")
      assert not filter._getHTTPAuthorizationCredentials("Digest " + base64.encodestring("username"))
      assert filter._getHTTPAuthorizationCredentials("Basic " + base64.encodestring("username")) == { "login": "username", "password": "" }
      assert filter._getHTTPAuthorizationCredentials("Basic " + base64.encodestring("user:pass")) == { "login": "user", "password": "pass" }
      assert filter._getHTTPAuthorizationCredentials("Basic " + base64.encodestring("user:pass:word")) == { "login": "user", "password": "pass:word" }

if __name__ == "__main__":
   print "Called as standalone program; running unit tests..."
   fileUserDataTest = unittest.makeSuite(rdwAuthenticationFilterTest, 'test')
   testRunner = unittest.TextTestRunner()
   testRunner.run(fileUserDataTest)
