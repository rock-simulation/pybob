#!/usr/env python

import sys
import os

show = True
path = "."
if len(sys.argv) > 1:
    if sys.argv[1] == "rm":
        show = False
    else:
        path = sys.argv[1]

if len(sys.argv) > 2:
    if sys.argv[2] == "rm":
        show = False

def removeBuild(rootDir):
    for root, dirs, files in os.walk(rootDir):
        for d in dirs:
            path = root + "/" + d
            if d == "build":
                cmd = ["rm", "-rf", path]
                if show:
                    print(" ".join(cmd))
                else:
                    os.system(" ".join(cmd))


def checkGits(rootDir):
    for root, dirs, files in os.walk(rootDir):
        for d in dirs:
            path = root + "/" + d
            if d == ".git":
                cmd = ["du", "-hd0", path]
                os.system(" ".join(cmd))



#checkGits(path)
removeBuild(path)
