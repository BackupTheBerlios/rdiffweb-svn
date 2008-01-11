#!/usr/bin/python

import unittest


from rdiffWeb.page_browse import browsePageTest
from rdiffWeb.page_history import historyPageTest
from rdiffWeb.page_locations import locationsPageTest
from rdiffWeb.db_mysql import mysqlUserDBTest
from rdiffWeb.rdw_helpers import helpersTest
from rdiffWeb.rdw_templating import templateParsingTest
from rdiffWeb.filter_authentication import rdwAuthenticationFilterTest
from rdiffWeb.db_file import fileUserDataTest
from rdiffWeb.rdw_config import configFileTest

unittest.main()
