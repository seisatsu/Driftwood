###################################
## Project Driftwood             ##
## log.py                        ##
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

import sys
from sdl2 import SDL_GetTicks


class LogManager:
    """The Log Manager

    This class handles the filtering and formatting of log messages.

    Attributes:
        config: ConfigManager instance.
    """

    def __init__(self, config):
        """LogManager class initializer.

        Args:
            config: Link back to the ConfigManager.
        """
        self.config = config

    def log(self, *chain):
        """Log a message.

        Args:
            chain: A list of strings to be separated by colon-spaces and printed.
        """
        self.__print(*chain)

    def info(self, *chain):
        """Log an info message if verbosity is enabled..

        Args:
            chain: A list of strings to be separated by colon-spaces and printed.
        """
        if self.config["log"]["verbose"]:
            self.__print(*chain)

    def __print(self, *chain):
        """Format and print the string.

        Args:
            chain: A list of strings to be separated by colon-spaces and printed.
        """
        ticks = "[{0}] ".format(str(SDL_GetTicks()))
        print(ticks + ": ".join(chain))
        sys.stdout.flush()
