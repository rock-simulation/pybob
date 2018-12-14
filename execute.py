#! /usr/bin/env python

import os
import errno
import colorconsole as c
import subprocess

def makeDir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        pass


def simpleExecute(cmd):
    p = subprocess.Popen(" ".join(cmd), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    p.communicate()

def do(cmd, cfg=None, errorString=None, path=None, logFile=None):
    outpipe = subprocess.PIPE
    if cfg and logFile:
        logPath = cfg["devDir"] + "/autoproj/bob/logs"
        if not os.path.isdir(logPath):
            makeDir(logPath)
        outpipe = open(logPath+"/"+logFile, "w")
    p = subprocess.Popen(" ".join(cmd), stdout=outpipe, stderr=outpipe,
                         cwd=path, shell=True)
    if cfg and logFile:
        outpipe.close()
    out = ""
    err = ""
    if cfg and logFile:
        p.wait()
    else:
        out, err = p.communicate()
    if len(err) > 0:
        if cfg and errorString:
            c.printError(err)
            cfg["errors"].append(errorString)
    return out,err,p.returncode
