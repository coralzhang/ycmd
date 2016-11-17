# Copyright (C) 2014 Google Inc.
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

from ycmd.utils import ( ByteOffsetToCodepointOffset,
                         ToBytes,
                         SplitLines )
from ycmd.request_validation import EnsureRequestValid


# TODO: Change the custom computed (and other) keys to be actual properties on
# the object.
class RequestWrap( object ):
  def __init__( self, request, validate = True ):
    if validate:
      EnsureRequestValid( request )
    self._request = request
    self._computed_key = {
      # Unicode string representation of the current line
      'line_value': self._CurrentLine,

      # The 'column_num' as a unicode codepoint offset
      'column_codepoint': (lambda:
        ByteOffsetToCodepointOffset( self[ 'line_bytes' ],
                                     self[ 'column_num' ] ) ),

      # Bytes string representation of the current line
      'line_bytes': lambda: ToBytes( self[ 'line_value' ] ),

      # Note: column_num is the byte offset into the UTF-8 encoded bytes
      # returned by line_bytes

      'filetypes': self._Filetypes,

      'first_filetype': self._FirstFiletype,
    }
    self._cached_computed = {}


  def __getitem__( self, key ):
    if key in self._cached_computed:
      return self._cached_computed[ key ]
    if key in self._computed_key:
      value = self._computed_key[ key ]()
      self._cached_computed[ key ] = value
      return value
    return self._request[ key ]


  def __contains__( self, key ):
    return key in self._computed_key or key in self._request


  def get( self, key, default = None ):
    try:
      return self[ key ]
    except KeyError:
      return default


  def _CurrentLine( self ):
    current_file = self._request[ 'filepath' ]
    contents = self._request[ 'file_data' ][ current_file ][ 'contents' ]

    return SplitLines( contents )[ self._request[ 'line_num' ] - 1 ]


  def _FirstFiletype( self ):
    try:
      return self[ 'filetypes' ][ 0 ]
    except (KeyError, IndexError):
      return None


  def _Filetypes( self ):
    path = self[ 'filepath' ]
    return self[ 'file_data' ][ path ][ 'filetypes' ]
