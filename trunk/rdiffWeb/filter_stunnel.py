import cherrypy
from cherrypy.lib.filter.basefilter import BaseFilter

class StunnelFilter(BaseFilter):
    def __init__(self, sslWrapAddr=None, sslWrapPort=None):
        if sslWrapAddr:
            self.sslWrapAddr = sslWrapAddr
        else:
            self.sslWrapAddr = '127.0.0.1'
        self.sslWrapPort = sslWrapPort

    def onStartResource(self):
        if cherrypy.request.remoteAddr == self.sslWrapAddr:
            cherrypy.request.scheme = 'https'

    def beforeRequestBody(self):
	fromPage = cherrypy.request.browserUrl
	if fromPage.startswith("http://"):
	   cherrypy.request.browserUrl = fromPage.replace("http://", "https://")

