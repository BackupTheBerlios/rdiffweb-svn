#!/usr/bin/python

import page_main


class rdiffRecentPage(page_main.rdiffPage):
   def index(self):
      page = self.startPage("Recent Backups")
      page = page + self.writeTopLinks()
      page = page + self.compileTemplate("recent.html")
      page = page + self.endPage()
      return page

   index.exposed = True