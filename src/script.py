###################################
## Project Driftwood             ##
## script.py                     ##
## Copyright 2013 PariahSoft LLC ##
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

import imp
import os
import zipimport


class ScriptManager:
    """The Script Manager

    This class handles loading scripts and calling their functions. It defines its own method for retrieving the
    script file (independant of ResourceManager) and internally caches it forever.

    Attributes:
        config: ConfigManager instance.
    """

    def __init__(self, config):
        """ScriptManager class initializer.

        Args:
            config: Link back to the ConfigManager.
        """
        self.config = config

        self.__log = self.config.baseclass.log
        self.__path = self.config.baseclass.path

        # Dictionary of module instances mapped by filename.
        self.__modules = {}

    def __convert_path(self, filename):
        """Get around a documented zipimport flaw.

        Args:
            filename: The filename to fix.
        """
        cpath = list(os.path.split(filename))
        cpath[-1] = os.path.splitext(cpath[-1])[0]
        return os.sep.join(cpath)

    def __load(self, filename):
        """Load a script.

        Args:
            filename: Filename of the python script to load.
        """
        importpath = self.__path.find(filename)

        if importpath:
            self.__log.info("Script", "loaded", filename)

            # This is a directory.
            if os.path.isdir(importpath):
                mname = os.path.splitext(os.path.split(filename)[-1])[0]
                self.__modules[filename] = imp.load_source(mname, os.path.join(importpath, filename))

            # This is hopefully a zip archive.
            else:
                importer = zipimport.zipimporter(importpath)
                mpath = self.__convert_path(filename)
                self.__modules[filename] = importer.load_module(mpath)

        else:
            self.__log.log("ERROR", "Script", "no such script", filename)

    def call(self, filename, func):
        """Call a function from a script, loading if not already loaded.

        Args:
            filename: Filename of the python script containing the function.
            func: Name of the function to call.
        """
        if not filename in self.__modules:
            self.__load(filename)

        if hasattr(self.__modules[filename], func):
            self.__log.info("Script", "called", filename, func + "()")
            getattr(self.__modules[filename], func)()

        else:
            self.__log.log("ERROR", "Script", filename, "no such function", func + "()")
