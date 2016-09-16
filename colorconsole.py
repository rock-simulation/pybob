#! /usr/bin/env python
from sys import stdout

BOLD = '\033[32;1m'
WARNING = '\033[38;5;166m'
ERROR = '\033[31;1m'
END = '\033[0m'

def printNormal(s):
    print s
    stdout.flush()

def printBold(s):
    print BOLD + s + END
    stdout.flush()

def printWarning(s):
    print WARNING + s + END
    stdout.flush()

def printError(s):
    print ERROR + s + END
    stdout.flush()
