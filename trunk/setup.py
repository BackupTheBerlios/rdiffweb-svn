#!/usr/bin/env python

from distutils.core import setup, Command
import glob, sys

# < Python 2.4 does not have the package_data setup keyword, making installation a pain.
# If we can, use package_data, otherwise, hack in the files
pythonVersion = sys.version_info[0]+sys.version_info[1]/10.0
if pythonVersion > 2.3:
   setup(name='rdiffWeb',
      version='0.3.5',
      description='A web interface to rdiff-backup repositories',
      author='Josh Nisly',
      author_email='rdiffweb@rdiffweb.org',
      url='http://www.rdiffweb.org',
      packages=['rdiffWeb'],
      package_data={'rdiffWeb': ['templates/*.html', 'templates/*.xml', 'static/*.png', 'static/*.js', 'static/*.css', 'static/images/*']},
      data_files=[('/etc/rdiffweb', ['rdw.conf.sample']),
                  ('/etc/init.d', ['init/rdiff-web'])
                  ],
      scripts=['rdiff-web', 'rdiff-web-config', 'rdiff-web-notify']
     )
else:
   from distutils.dist import Distribution
   import distutils.command.install

   installer = distutils.command.install.install(Distribution())
   installer.initialize_options()
   installer.finalize_options()
   packageDataDir = installer.config_vars['prefix']+"/lib/python"+installer.config_vars['py_version_short']+"/site-packages/rdiffWeb"

   setup(name='rdiffWeb',
      version='0.3.5',
      description='A web interface to rdiff-backup repositories',
      author='Josh Nisly',
      author_email='rdiffweb@rdiffweb.org',
      url='http://www.rdiffweb.org',
      packages=['rdiffWeb'],
      data_files=[('/etc/rdiffweb', ['rdw.conf.sample']),
                  ('/etc/init.d', ['init/rdiff-web']),
                  (packageDataDir+'/templates', glob.glob('rdiffWeb/templates/*.html')),
                  (packageDataDir+'/templates', glob.glob('rdiffWeb/templates/*.xml')),
                  (packageDataDir+'/static', glob.glob('rdiffWeb/static/*.js')),
                  (packageDataDir+'/static', glob.glob('rdiffWeb/static/*.png')),
                  (packageDataDir+'/static', glob.glob('rdiffWeb/static/*.css')),
                  (packageDataDir+'/static/images', glob.glob('rdiffWeb/static/images/*')),
                  ],
      scripts=['rdiff-web', 'rdiff-web-config', 'rdiff-web-notify']
     )
