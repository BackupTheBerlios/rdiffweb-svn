import cherrypy
from cherrypy.lib.filter.basefilter import BaseFilter
import page_main

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

      loginKey = "login"
      passwordKey = "password"
      redirectKey = "redirect"

      loginParms = {"message": "", "action": self.loginUrl,
         "loginKey": loginKey, "passwordKey": passwordKey, "redirectKey": redirectKey,
         "loginValue": "", "redirectValue": cherrypy.request.path }

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
