#! /usr/bin/env python

BOLD = '\033[32;1m'
WARNING = '\033[38;5;166m'
ERROR = '\033[31;1m'
END = '\033[0m'

def printBold(s):
    print BOLD + s + END

def printWarning(s):
    print WARNING + s + END

def printError(s):
    print ERROR + s + END
