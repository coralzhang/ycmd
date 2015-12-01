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

from hamcrest import assert_that, has_items

from ycmd.utils import ReadFile
from ycmd.tests.php import PathToTestFile, SharedYcmd
from ycmd.tests.test_utils import BuildRequest, CompletionEntryMatcher


@SharedYcmd
def GetCompletions_Basic_test( app ):
  filepath = PathToTestFile( 'basic.php' )
  completion_data = BuildRequest( filepath = filepath,
                                  filetype = 'php',
                                  contents = ReadFile( filepath ),
                                  line_num = 12,
                                  column_num = 9 )

  results = app.post_json( '/completions',
                           completion_data ).json[ 'completions' ]

  assert_that( results,
               has_items( CompletionEntryMatcher( 'methodA' ),
                          CompletionEntryMatcher( 'methodB' ),
                          CompletionEntryMatcher( 'methodC' ) ) )
