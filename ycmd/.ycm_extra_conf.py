# This file is NOT licensed under the GPLv3, which is the license for the rest
# of YouCompleteMe.
#
# Here's the license text for this file:
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>

import os
import fnmatch

DIR_OF_CURRENT_SCRIPT = os.path.dirname( os.path.abspath( __file__ ) )


def GetAdditionalSources():
  additional_sources = []
  for root, dirnames, filenames in os.walk( DIR_OF_CURRENT_SCRIPT ):
    for filename in fnmatch.filter( filenames, '*.py' ):
      # We don't want to include .ycm_extra_conf.py files, particularly this
      # one.
      if filename.endswith( '.ycm_extra_conf.py' ):
        continue
      additional_sources.append( os.path.join( root, filename ) )
  return additional_sources


def PythonSettings( **kwargs ):
  return {
    'additional_sources': GetAdditionalSources()
  }
