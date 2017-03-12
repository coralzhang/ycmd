#!/usr/bin/env python

from base64 import b64encode
from tempfile import NamedTemporaryFile
import argparse
import hashlib
import hmac
import json
import os
import requests
import socket
import subprocess
import sys
import time
from urlparse import urlparse, urljoin



HEADERS = { 'content-type': 'application/json' }
HMAC_HEADER = 'x-ycm-hmac'
HMAC_SECRET_LENGTH = 16
YCMD_PATH = os.path.abspath( os.path.join(
    os.path.dirname( __file__ ), 'ycmd' ) )
LOGFILE_FORMAT = 'server_{port}_{std}_'
CONNECT_TIMEOUT = 0.001
READ_TIMEOUT = 30


def CreateHmac( content, hmac_secret ):
  # Note that py2's str type passes this check (and that's ok)
  if not isinstance( content, bytes ):
    raise TypeError( 'content was not of bytes type; you have a bug!' )
  if not isinstance( hmac_secret, bytes ):
    raise TypeError( 'hmac_secret was not of bytes type; you have a bug!' )

  return bytes( hmac.new( hmac_secret,
                          msg = content,
                          digestmod = hashlib.sha256 ).digest() )


def CreateRequestHmac( method, path, body, hmac_secret ):
  # Note that py2's str type passes this check (and that's ok)
  if not isinstance( body, bytes ):
    raise TypeError( 'body was not of bytes type; you have a bug!' )
  if not isinstance( hmac_secret, bytes ):
    raise TypeError( 'hmac_secret was not of bytes type; you have a bug!' )
  if not isinstance( method, bytes ):
    raise TypeError( 'method was not of bytes type; you have a bug!' )
  if not isinstance( path, bytes ):
    raise TypeError( 'path was not of bytes type; you have a bug!' )

  method_hmac = CreateHmac( method, hmac_secret )
  path_hmac = CreateHmac( path, hmac_secret )
  body_hmac = CreateHmac( body, hmac_secret )

  joined_hmac_input = bytes().join( ( method_hmac, path_hmac, body_hmac ) )
  return CreateHmac( joined_hmac_input, hmac_secret )


# This is the compare_digest function from python 3.4
#   http://hg.python.org/cpython/file/460407f35aa9/Lib/hmac.py#l16
def SecureBytesEqual( a, b ):
  """Returns the equivalent of 'a == b', but avoids content based short
  circuiting to reduce the vulnerability to timing attacks."""
  # Consistent timing matters more here than data type flexibility
  # We do NOT want to support py2's str type because iterating over them
  # (below) produces different results.
  if type( a ) != bytes or type( b ) != bytes:
    raise TypeError( "inputs must be bytes instances" )

  # We assume the length of the expected digest is public knowledge,
  # thus this early return isn't leaking anything an attacker wouldn't
  # already know
  if len( a ) != len( b ):
    return False

  # We assume that integers in the bytes range are all cached,
  # thus timing shouldn't vary much due to integer object creation
  result = 0
  for x, y in zip( a, b ):
    result |= x ^ y
  return result == 0


def GetUnusedLocalhostPort():
  sock = socket.socket()
  # This tells the OS to give us any free port in the range [1024 - 65535]
  sock.bind( ( '', 0 ) )
  port = sock.getsockname()[ 1 ]
  sock.close()
  return port


class YcmdClient( object ):

  def __init__( self, logs ):
    self._logs = logs
    self._location = None
    self._port = None
    self._hmac_secret = None
    self._options_dict = {}
    self._popen_handle = None


  def Start( self ):
    self._hmac_secret = os.urandom( HMAC_SECRET_LENGTH )
    self._options_dict[ 'hmac_secret' ] = b64encode( self._hmac_secret )

    # The temp options file is deleted by ycmd during startup
    with NamedTemporaryFile( mode = 'w+', delete = False ) as options_file:
      json.dump( self._options_dict, options_file )
      options_file.flush()
      self._port = GetUnusedLocalhostPort()
      self._location = 'http://127.0.0.1:' + str( self._port )

      ycmd_args = [
        sys.executable,
        YCMD_PATH,
        '--port={0}'.format( self._port ),
        '--options_file={0}'.format( options_file.name ),
        '--log=debug'
      ]

      redirection = subprocess.PIPE if self._logs else None

      tic = time.time()
      self._popen_handle = subprocess.Popen( ycmd_args,
                                             stdout = redirection,
                                             stderr = redirection )
      self._WaitUntilReady()
      return time.time() - tic


  def _IsReady( self ):
    response = self.GetRequest( 'ready' )
    response.raise_for_status()
    return response.json()


  def _WaitUntilReady( self, timeout = 10 ):
    expiration = time.time() + timeout
    while True:
      try:
        if time.time() > expiration:
          raise RuntimeError( 'Waited for ycmd to be ready for {0} seconds, '
                              'aborting.'.format( timeout ) )

        if self._IsReady():
          return
      except requests.exceptions.ConnectionError:
        pass
      finally:
        time.sleep( 0.001 )


  def GetRequest( self, handler, params = None ):
    return self._Request( 'GET', handler, params = params )


  def PostRequest( self, handler, data = None ):
    return self._Request( 'POST', handler, data = data )


  def _Request( self, method, handler, data = None, params = None ):
    request_uri = urljoin( self._location, handler )
    data = json.dumps( data ) if data else None
    headers = self._ExtraHeaders( method,
                                  request_uri,
                                  data )
    response = requests.request( method,
                                 request_uri,
                                 headers = headers,
                                 data = data,
                                 params = params,
                                 timeout = ( CONNECT_TIMEOUT, READ_TIMEOUT ) )
    return response


  def _ExtraHeaders( self, method, request_uri, request_body = None ):
    if not request_body:
      request_body = ''
    headers = dict( HEADERS )
    headers[ HMAC_HEADER ] = b64encode(
        CreateRequestHmac( method,
                           urlparse( request_uri ).path,
                           request_body,
                           self._hmac_secret ) )
    return headers


def RemoveBytecode():
  for root, dirs, files in os.walk( YCMD_PATH ):
    for name in files:
      _, extension = os.path.splitext( name )
      if extension == '.pyc':
        os.remove( os.path.join( root, name ) )


def ParseArguments():
  parser = argparse.ArgumentParser()
  parser.add_argument( '--logs', action = 'store_false',
                       help = 'Display ycmd logs.' )
  parser.add_argument( '--runs', type = int, default = 10,
                       help = 'Number of runs.' )
  return parser.parse_args()


if __name__ == '__main__':
  args = ParseArguments()
  ycmd_client = YcmdClient( args.logs )

  # Warmup
  ycmd_client.Start()
  ycmd_client.PostRequest( 'shutdown' )

  startup_times = []
  for _ in range( args.runs ):
    RemoveBytecode()
    startup_times.append( ycmd_client.Start() )
    ycmd_client.PostRequest( 'shutdown' )
  average_startup_time_without_bytecode = int(
      sum( startup_times ) * 1000 / args.runs )

  startup_times = []
  for _ in range( args.runs ):
    startup_times.append( ycmd_client.Start() )
    ycmd_client.PostRequest( 'shutdown' )
  average_startup_time_with_bytecode = int(
      sum( startup_times ) * 1000 / args.runs )

  print( 'Average startup time on {0} runs:\n'
         '  without bytecode: {1}ms\n'
         '  with bytecode:    {2}ms'.format(
             args.runs,
             average_startup_time_without_bytecode,
             average_startup_time_with_bytecode ) )
