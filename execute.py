#! /usr/bin/env python

import os
import colorconsole as c
import subprocess

def do(cmd, cfg=None, errorString=None, path=None, logFile=None):
    outpipe = subprocess.PIPE
    if cfg and logFile:
        logPath = cfg["devDir"] + "/autoproj/logs";
        if not os.path.isdir(logPath):
            os.system("mkdir -p "+logPath)
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
        if cfg and errorString > 0:
            c.printError(err)
            cfg["errors"].append(errorString)
    return out,err,p.returncode
