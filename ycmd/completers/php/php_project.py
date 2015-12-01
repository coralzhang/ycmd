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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

import logging
import os
import re
from tempfile import NamedTemporaryFile

from ycmd.completers.php.php_utils import ( FindPHPExecutable,
                                            PATH_TO_PADAWAN_DIR )
from ycmd import utils


CLI_PROGRESS = re.compile( 'Progress: ([0-9]+)' )

PATH_TO_PADAWAN_CLI = os.path.join( PATH_TO_PADAWAN_DIR, 'bin',
                                    'padawan' )


class PHPProject():
  """
  Defines a PHP project as the folder containing the composer.json file.
  """

  def __init__( self, project_root ):
    self._php_executable = FindPHPExecutable()
    self._root = project_root
    self._padawan_cli_phandle = None
    self._padawan_cli_output = None
    self._logger = logging.getLogger( __name__ )


  def GetProjectRoot( self ):
    return self._root


  def GenerateIndex( self ):
    """Generates Padawan.php index and returns the initial progress."""
    self._logger.info( 'Generating index for {0} project'.format(
                       self._root ) )

    command = [ self._php_executable, PATH_TO_PADAWAN_CLI, 'generate' ]

    self._padawan_cli_output = NamedTemporaryFile(
      dir = utils.PathToCreatedTempDir(),
      prefix = 'padawan_cli',
      delete = False ).name

    # Command needs to be executed at the project root.
    with open( self._padawan_cli_output, 'w' ) as output:
      self._padawan_cli_phandle = utils.SafePopen( command,
                                                   cwd = self._root,
                                                   stdout = output,
                                                   stderr = output )


  def GetIndexingPercentage( self ):
    if self._padawan_cli_output is None:
      return None

    if self._padawan_cli_phandle.poll() is not None:
      self._padawan_cli_output = None
      return 100

    lines = open( self._padawan_cli_output ).readlines()
    for line in reversed( lines[ -10: ] ):
      match = CLI_PROGRESS.search( line )
      if match:
        return int( match.group( 1 ) )
    return 0


  def GetIndexingDescription( self ):
    return 'Generating index for {0} project'.format(
      os.path.basename( self._root ) )


  def GetProgress( self ):
    percentage = self.GetIndexingPercentage()
    if percentage is not None:
      return {
        'description': self.GetIndexingDescription(),
        'percentage': percentage
      }
    return None
