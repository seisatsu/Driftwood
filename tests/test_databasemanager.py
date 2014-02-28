###################################
## Driftwood 2D Game Dev. Suite  ##
## test_databasemanager.py       ##
## Copyright 2014 PariahSoft LLC ##
###################################

## **********
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to
## deal in the Software without restriction, including without limitation the
## rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
## sell copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
## FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
## IN THE SOFTWARE.
## **********

import shutil
import unittest
import unittest.mock as mock

import databasemanager

def driftwood():
    d = mock.Mock()
    d.config = {
        'database': {
            'root': 'db.test',
            'name': 'test.db'
        }
    }
    d.log.msg.side_effect = Exception('log.msg called')
    return d

class TestDatabaseCreation(unittest.TestCase):
    """Test that the DatabaseManager can initialize itself correctly with defaults on a fresh filesystem.
    """

    def test_create_db_dir_if_not_exist(self):
        """DatabaseManager should create the directory db.test if it doesn't exist already."""
        databasemanager.DatabaseManager(driftwood())

    def test_create_db_file_if_not_exist(self):
        """DatabaseManager should create the file test.db if it doesn't exist already."""
        databasemanager.DatabaseManager(driftwood())

    def tearDown(self):
        shutil.rmtree('db.test', ignore_errors=False)
