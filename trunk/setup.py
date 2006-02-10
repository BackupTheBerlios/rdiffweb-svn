#!/usr/bin/env python

from distutils.core import setup

setup(name='rdiffWeb',
      version='0.2',
      description='A web interface to rdiff-backup repositories',
      author='Josh Nisly',
      author_email='rdiffweb@rdiffweb.org',
      url='http://www.rdiffweb.org',
      packages=['rdiffWeb'],
      package_data={'rdiffWeb': ['templates/*.html', 'static/*']},
      data_files=[('/etc/rdiffweb', ['rdw.conf.sample']),
                  ('/etc/init.d', ['init/rdiff-web'])
                  ],
      scripts=['rdiff-web', 'rdiff-web-config']
     )
