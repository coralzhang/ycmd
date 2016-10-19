# Copyright (C) 2017 ycmd contributors
#
# This file is part of ycmd.
#
# ycmd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ycmd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ycmd.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

import logging
import os

from ycmd import extra_conf_store
from ycmd.responses import YCM_EXTRA_CONF_FILENAME
from ycmd.utils import PathsToAllParentFolders, UpdateDictionary


# List of files that we are looking for to find the project root, from highest
# to lowest priority.
PROJECT_ROOT_CANDIDATES = [ YCM_EXTRA_CONF_FILENAME,
                            'setup.py',
                            '__main__.py',
                            '__init__.py' ]


class PythonSettings():

  def __init__( self ):
    self._project_root_for_file = {}
    self._settings_for_project_root = {}
    self._logger = logging.getLogger( __name__ )


  def SettingsForFile( self, filename, client_data = None ):
    try:
      project_root = self._project_root_for_file[ filename ]
    except KeyError:
      project_root = self.GetProjectRootForFile( filename )

    try:
      settings = self._settings_for_project_root[ project_root ]
    except KeyError:
      settings = self._GetSettingsForProjectRoot( project_root,
                                                  client_data = client_data )

    if settings[ 'do_cache' ]:
      self._settings_for_project_root[ project_root ] = settings
    return settings


  def _GetSettingsForProjectRoot( self, project_root, client_data ):
    # Default settings.
    settings = {
      'jedi': {
        'settings': {}
      },
      'do_cache': True
    }

    if not project_root:
      return settings

    module = extra_conf_store.ModuleForSourceFile( project_root )
    if not module:
      # We don't warn the user if no .ycm_extra_conf.py file is found.
      return settings

    try:
      custom_settings = module.PythonSettings( client_data = client_data )
    except AttributeError:
      self._logger.warning( 'No PythonSettings function defined '
                            'in extra conf file.' )
      return settings

    if not custom_settings:
      return settings

    return UpdateDictionary( settings, custom_settings )


  def GetProjectRootForFile( self, filename ):
    if not filename:
      return None
    for candidate in PROJECT_ROOT_CANDIDATES:
      for folder in PathsToAllParentFolders( filename ):
        if os.path.isfile( os.path.join( folder, candidate ) ):
          self._project_root_for_file[ filename ] = folder
          return folder
    return None
