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

import os
from mock import MagicMock, patch
from hamcrest import assert_that, empty, equal_to, has_entries, has_entry

from ycmd.completers.python.settings import PythonSettings
from ycmd.tests.python import PathToTestFile
from ycmd.utils import PathsToAllParentFolders


def PathsToParentFoldersUntilTestData( path ):
  for path in PathsToAllParentFolders( path ):
    yield path
    if os.path.basename( path ) == 'testdata':
      return


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_GetProjectRootForFile_NoFilename_test():
  python_settings = PythonSettings()
  assert_that(
    python_settings.GetProjectRootForFile( None ),
    equal_to( None )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_GetProjectRootForFile_NoProject_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'no_project', 'script.py' )
  assert_that(
    python_settings.GetProjectRootForFile( filename ),
    equal_to( None )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_GetProjectRootForFile_ExtraConfProject_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'extra_conf_project', 'package', 'module',
                             'file.py' )
  assert_that(
    python_settings.GetProjectRootForFile( filename ),
    equal_to( PathToTestFile( 'extra_conf_project' ) )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_GetProjectRootForFile_SetupProject_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'setup_project', 'package', 'module', 'file.py' )
  assert_that(
    python_settings.GetProjectRootForFile( filename ),
    equal_to( PathToTestFile( 'setup_project' ) )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_GetProjectRootForFile_Package_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'package', 'module', 'file.py' )
  assert_that(
    python_settings.GetProjectRootForFile( filename ),
    equal_to( PathToTestFile( 'package' ) )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_GetProjectRootForFile_Module_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'module', 'file.py' )
  assert_that(
    python_settings.GetProjectRootForFile( filename ),
    equal_to( PathToTestFile( 'module' ) )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_SettingsForFile_NoFilename_test():
  python_settings = PythonSettings()
  assert_that(
    python_settings.SettingsForFile( None ),
    has_entries( {
      'jedi': has_entries( {
         'settings': empty()
      } ),
      'do_cache': True
    } )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_SettingsForFile_NoProject_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'no_project', 'script.py' )
  assert_that(
    python_settings.SettingsForFile( filename ),
    has_entries( {
      'jedi': has_entries( {
         'settings': empty()
      } ),
      'do_cache': True
    } )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_SettingsForFile_ExtraConfProject_NoPythonSettings_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'extra_conf_project', 'package', 'module',
                             'file.py' )

  module = MagicMock()
  module.PythonSettings = MagicMock( side_effect = AttributeError(
      "module 'random_name' has no attribute 'PythonSettings'" ) )

  with patch( 'ycmd.extra_conf_store.ModuleForSourceFile',
              return_value = module ):
    assert_that(
      python_settings.SettingsForFile( filename ),
      has_entries( {
        'jedi': has_entries( {
          'settings': empty()
        } ),
        'do_cache': True
      } )
    )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_SettingsForFile_ExtraConfProject_NoSettings_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'extra_conf_project', 'package', 'module',
                             'file.py' )

  module = MagicMock()
  module.PythonSettings = MagicMock( return_value = None )

  with patch( 'ycmd.extra_conf_store.ModuleForSourceFile',
              return_value = module ):
    assert_that(
      python_settings.SettingsForFile( filename ),
      has_entries( {
        'jedi': has_entries( {
          'settings': empty()
        } ),
        'do_cache': True
      } )
    )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_SettingsForFile_ExtraConfProject_CustomSettings_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'extra_conf_project', 'package', 'module',
                             'file.py' )

  module = MagicMock()
  module.PythonSettings = MagicMock( return_value = {
    'jedi': {
      'settings': {
        'some_setting': 'some_value'
      }
    },
    'do_cache': False
  } )

  with patch( 'ycmd.extra_conf_store.ModuleForSourceFile',
              return_value = module ):
    assert_that(
      python_settings.SettingsForFile( filename ),
      has_entries( {
        'jedi': has_entries( {
          'settings': has_entry( 'some_setting', 'some_value' )
        } ),
        'do_cache': False
      } )
    )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_SettingsForFile_SetupProject_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'setup_project', 'package', 'module', 'file.py' )
  assert_that(
    python_settings.SettingsForFile( filename ),
    has_entries( {
      'jedi': has_entries( {
         'settings': empty()
      } ),
      'do_cache': True
    } )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_SettingsForFile_Package_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'package', 'module', 'file.py' )
  assert_that(
    python_settings.SettingsForFile( filename ),
    has_entries( {
      'jedi': has_entries( {
         'settings': empty()
      } ),
      'do_cache': True
    } )
  )


@patch( 'ycmd.completers.python.settings.PathsToAllParentFolders',
        PathsToParentFoldersUntilTestData )
def PythonSettings_SettingsForFile_Module_test():
  python_settings = PythonSettings()
  filename = PathToTestFile( 'module', 'file.py' )
  assert_that(
    python_settings.SettingsForFile( filename ),
    has_entries( {
      'jedi': has_entries( {
         'settings': empty()
      } ),
      'do_cache': True
    } )
  )
