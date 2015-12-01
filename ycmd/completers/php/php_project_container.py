# Copyright (C) 2016 ycmd contributors
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

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

import logging
import os

from ycmd.completers.php.php_project import PHPProject


class PHPProjectContainer():
  """
  Contains list of PHP projects.
  """

  def __init__( self ):
    self._logger = logging.getLogger( __name__ )
    self._filepaths = {}
    self._projects = {}


  def GetProject( self, filepath ):
    filepath = os.path.normpath( filepath )

    if filepath in self._filepaths:
      self._logger.info( 'Use cached filepath {0}'.format( filepath ) )
      return self._projects[ self._filepaths[ filepath ] ]

    self._logger.info( 'Find composer using filepath {0}'.format( filepath ) )
    project_root = self._FindComposerFolder( filepath )
    self._filepaths[ filepath ] = project_root

    if project_root in self._projects:
      self._logger.info( 'Use cached project {0}'.format( project_root ) )
      return self._projects[ project_root ]

    self._logger.info( 'Add project in {0}'.format( project_root ) )
    php_project = PHPProject( project_root )
    self._projects[ project_root ] = php_project

    return php_project


  def GetProjects( self ):
    return self._projects.values()


  def _FindComposerFolder( self, filepath ):
    """Search parent folders until finding a folder containing a composer.json
    file. If no folder is found, returns the current folder."""
    path = os.path.normpath( os.path.dirname( filepath ) )

    while True:
      path, folder = os.path.split( path )
      if not folder:
        return os.path.dirname( filepath )

      if os.path.exists( os.path.join( path, 'composer.json' ) ):
        return path
