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
import requests
import threading
import urllib.parse

from ycmd import responses, utils
from ycmd.completers.completer import Completer
from ycmd.completers.php.php_project_container import PHPProjectContainer
from ycmd.completers.php.php_utils import ( FindPHPExecutable,
                                            PATH_TO_PADAWAN_DIR )


PATH_TO_PADAWAN_SERVER = os.path.join( PATH_TO_PADAWAN_DIR, 'bin',
                                       'padawan-server' )

SERVER_LOGFILE_FORMAT = os.path.join( utils.PathToCreatedTempDir(),
                                      u'padawan_{port}_{std}.log' )

PADAWAN_SERVER_NOT_FOUND = ( 'Padawan.php server not found. You probably '
                             'forgot to run: '
                             'git submodule update --init --recursive' )
PADAWAN_SERVER_NOT_RUNNING = 'Padawan.php server is not running'
PADAWAN_SERVER_ALREADY_STARTED = 'Padawan.php server is already started'


class PHPCompleter( Completer ):
  """
  A completer for PHP that uses the Padawan.php completion engine:
  https://github.com/mkusher/padawan.php
  """

  def __init__( self, user_options ):
    super( PHPCompleter, self ).__init__( user_options )
    self._php_executable = FindPHPExecutable()
    self._php_project_container = PHPProjectContainer()
    self._padawan_lock = threading.RLock()
    self._padawan_handle = None
    self._padawan_port = None
    self._padawan_host = None
    self._padawan_stdout = None
    self._padawan_stderr = None
    self._logger = logging.getLogger( __name__ )
    self._keep_logfiles = user_options[ 'server_keep_logfiles' ]

    if not os.path.isfile( PATH_TO_PADAWAN_SERVER ):
      self._logger.error( PADAWAN_SERVER_NOT_FOUND )
      raise RuntimeError( PADAWAN_SERVER_NOT_FOUND )

    self._StartServer()


  def SupportedFiletypes( self ):
    return [ 'php' ]


  def GetSubcommandsMap( self ):
    return {
      'StopServer'   : ( lambda self, request_data, args:
                         self._StopServer() ),
      'RestartServer': ( lambda self, request_data, args:
                         self._RestartServer() ),
      'GenerateIndex': ( lambda self, request_data, args:
                         self._GenerateIndex( request_data ) ),
    }


  def _TranslateRequestForPadawan( self, request_data ):
    if not request_data:
      return {}, None

    filepath = request_data[ 'filepath' ]
    contents = request_data[ 'file_data' ][ filepath ][ 'contents' ]

    # Padawan need line separators according to the platform: \n on Unix and
    # \r\n on Windows.
    contents = os.linesep.join( contents.split( '\n' ) )

    project = self._php_project_container.GetProject( filepath )
    project_root = project.GetProjectRoot()

    return {
        'filepath': os.path.relpath( filepath, project_root ),
        'line'    : request_data[ 'line_num' ],
        'column'  : request_data[ 'start_column' ],
        'path'    : project_root
    }, contents


  # TODO: add a timeout parameter
  def _SendRequest( self, handler, request_data = {} ):
    """Send a request to the server. Requests available are:
     - /complete
     - /update
     - /list
     - /kill
    """
    url = urllib.parse.urljoin( self._padawan_host, handler )
    params, data = self._TranslateRequestForPadawan( request_data )

    self._logger.debug( 'Making Padawan request: {0} {1} {2}'.format( url,
                                                                      params,
                                                                      data ) )

    response = requests.post( url,
                              params = params,
                              data = data )
    response.raise_for_status()
    result = response.json()
    if 'error' in result:
      raise RuntimeError( result[ 'error' ] )
    return result


  def _StartServer( self ):
    """Start the Padawan server."""
    with self._padawan_lock:
      self._logger.info( 'Starting Padawan server' )

      self._padawan_port = utils.GetUnusedLocalhostPort()
      self._padawan_host = 'http://127.0.0.1:{0}'.format( self._padawan_port )

      command = [ self._php_executable,
                  PATH_TO_PADAWAN_SERVER,
                  '--port={0}'.format( self._padawan_port ) ]

      self._padawan_stdout = SERVER_LOGFILE_FORMAT.format(
          port = self._padawan_port, std = 'stdout' )
      self._padawan_stderr = SERVER_LOGFILE_FORMAT.format(
          port = self._padawan_port, std = 'stderr' )

      with utils.OpenForStdHandle( self._padawan_stdout ) as stdout:
        with utils.OpenForStdHandle( self._padawan_stderr ) as stderr:
          self._padawan_handle = utils.SafePopen( command,
                                                  stdout = stdout,
                                                  stderr = stderr )


  def _StopServer( self ):
    """Stop the padawan server."""
    with self._padawan_lock:
      if self._ServerIsRunning():
        self._logger.info( 'Stopping Padawan server' )
        # A ConnectionError with message "Connection is aborted" is raised when
        # sending a kill request to the Padawan server.
        try:
          self._SendRequest( '/kill' )
        except requests.exceptions.ConnectionError:
          pass
        try:
          utils.WaitUntilProcessIsTerminated( self._padawan_handle,
                                              timeout = 5 )
          self._logger.info( 'Padawan server stopped' )
        except RuntimeError:
          self._logger.exception( 'Error while stopping Padawan server' )

      self._CleanUp()


  def _CleanUp( self ):
    self._padawan_handle = None
    self._padawan_port = None
    self._padawan_host = None
    if not self._keep_logfiles:
      if self._padawan_stdout:
        utils.RemoveIfExists( self._padawan_stdout )
        self._padawan_stdout = None
      if self._padawan_stderr:
        utils.RemoveIfExists( self._padawan_stderr )
        self._padawan_stdout = None


  def _RestartServer( self ):
    with self._padawan_lock:
      self._StopServer()
      self._StartServer()


  def _ServerIsRunning( self ):
    return utils.ProcessIsRunning( self._padawan_handle )


  def ServerIsHealthy( self ):
    """Check if the Padawan server is healthy (up and serving).

    Since the Padawan server does not provide a healthy-like handler, we check
    if the expected error is returned."""
    if not self._ServerIsRunning():
      return False

    try:
      self._SendRequest( '/healthy' )
    except RuntimeError as error:
      return str( error ) == 'Unknown command'
    except Exception:
      return False


  def ServerIsReady( self ):
    """Check if the Padawan server is ready. Same as the healthy status."""
    return self.ServerIsHealthy()


  def _ConvertCompletionData( self, completion ):
    insertion_text = completion[ 'name' ]
    extra_menu_info = completion[ 'signature' ]
    kind = 'f' if extra_menu_info.startswith( '(' ) else None
    detailed_info = completion[ 'description' ].rstrip()
    return responses.BuildCompletionData(
      insertion_text = insertion_text,
      extra_menu_info = extra_menu_info,
      kind = kind,
      detailed_info = detailed_info,
      extra_data = None )


  def ComputeCandidatesInner( self, request_data ):
    completions = self._SendRequest( '/complete', request_data )[ 'completion' ]
    return [ self._ConvertCompletionData( completion )
             for completion in completions ]


  def Shutdown( self ):
    self._StopServer()


  def DebugInfo( self, request_data ):
    with self._padawan_lock:
      if self._ServerIsRunning():
        return ( 'PHP completer debug information:\n'
                 '  Padawan running at: {0}\n'
                 '  Padawan process ID: {1}\n'
                 '  Padawan executable: {2}\n'
                 '  Padawan logfiles:\n'
                 '    {3}\n'
                 '    {4}'.format( self._padawan_host,
                                   self._padawan_handle.pid,
                                   PATH_TO_PADAWAN_SERVER,
                                   self._padawan_stdout,
                                   self._padawan_stderr ) )

      if self._padawan_stdout and self._padawan_stderr:
        return ( 'PHP completer debug information:\n'
                 '  Padawan no longer running\n'
                 '  Padawan executable: {0}\n'
                 '  Padawan logfiles:\n'
                 '    {1}\n'
                 '    {2}'.format( PATH_TO_PADAWAN_SERVER,
                                   self._padawan_stdout,
                                   self._padawan_stderr ) )

      return ( 'PHP completer debug information:\n'
               '  Padawan is not running\n'
               '  Padawan executable: {0}'.format( PATH_TO_PADAWAN_SERVER ) )


  def _GenerateIndex( self, request_data ):
    filepath = request_data[ 'filepath' ]
    project = self._php_project_container.GetProject( filepath )
    project.GenerateIndex()
    return responses.BuildProgressResponse()


  def GetProgress( self ):
    progress = []
    for project in self._php_project_container.GetProjects():
      project_progress = project.GetProgress()
      if project_progress is not None:
        progress.append( project_progress )
    return progress
