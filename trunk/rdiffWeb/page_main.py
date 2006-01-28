
import cherrypy
import urllib
import os.path

import db_file
import db_mysql
import rdw_templating
import rdw_helpers
import rdw_config
from stunnelfilter import StunnelFilter

def getTunnellingFilters():
   if rdw_config.getConfigSetting("UseSTunnel").upper() == "TRUE":
      return [StunnelFilter(rdw_config.getConfigSetting("VisibleServerName"))]
   return []


class rdiffPage:
   _cpFilterList = getTunnellingFilters()
   def __init__(self):
      self.userDB = self.getUserDBModule()

   ############################## HELPER FUNCTIONS ###################################
   def buildBrowseUrl(self, repo, path):
      return "/browse/?repo="+rdw_helpers.encodeUrl(repo)+"&path="+rdw_helpers.encodeUrl(path)

   def buildRestoreUrl(self, repo, path, date):
      return "/restore/?repo="+rdw_helpers.encodeUrl(repo)+"&path="+rdw_helpers.encodeUrl(path)+"&date="+rdw_helpers.encodeUrl(date.getUrlString())

   def buildHistoryUrl(self, repo):
      return "/history/?repo="+rdw_helpers.encodeUrl(repo)

   def buildLocationsUrl(self):
      return "/"

   def compileTemplate(self, templatePath, **kwargs):
      (packageDir, ignored) = os.path.split(__file__)
      templateText = open(rdw_helpers.joinPaths(packageDir, "templates", templatePath), "r").read()
      return rdw_templating.templateParser().parseTemplate(templateText, **kwargs)

   def getUserDBModule(self):
      authModuleSetting = rdw_config.getConfigSetting("UserDB");
      if authModuleSetting.lower() == "file":
         return db_file.fileUserDB()
      if authModuleSetting.lower() == "mysql":
         return db_mysql.mysqlUserDB()
      assert(False)


   ########################## PAGE HELPER FUNCTIONS ##################################
   def startPage(self, title):
      return self.compileTemplate("page_start.html", title=title)

   def endPage(self):
      return self.compileTemplate("page_end.html")

   def writeTopLinks(self):
      pages = [("/status/", "Backup Status"), ("/doLogout", "Log out")]
      if self.userDB.userIsAdmin(self.getUsername()):
         pages.append(("admin", "Admin"))
      links = []
      for page in pages:
         (url, title) = page
         links.append({"linkText" : title, "title": title, "linkUrl" : url})
      return self.compileTemplate("nav_bar.html", topLinks=links)

   def writeErrorPage(self, error):
      page = self.startPage("Error")
      page = page + self.writeTopLinks()
      page = page + error
      page = page + self.endPage()
      return page

   def writeMessagePage(self, title, message):
      page = self.startPage(title)
      page = page + self.writeTopLinks()
      page = page + message
      page = page + self.endPage()
      return page


   ########## SESSION INFORMATION #############
   def checkAuthentication(self, username, password):
      if self.userDB.areUserCredentialsValid(username, password):
         cherrypy.session['username'] = username #TODO: this seems like a hack.  Figure out clean way to pull this off
         return None
      return "Bad password!"

   def getUsername(self):
      username = cherrypy.session['username']
      return username


