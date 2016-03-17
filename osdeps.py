#! /usr/bin/env python

import os
import colorconsole as c
import execute
from platform import system

def install(cfg, pkg):
    platform = system()
    if pkg == "cmake":
        if os.popen('which cmake').read():
            return
    else:
        if os.system('pkg-config --exists '+pkg) != 0:
            if platform == "Windows":
                c.printError("Os dependency not fount: "+pkg)
            elif platform == "Darwin":
                c.printBold("Installing os dependency: "+pkg)
                execute.do(["sudo", "port", "install", pkg])
            else:
                c.printBold("Installing os dependency: "+pkg)
                execute.do(["sudo", "apt-get", "install", pkg])

def loadOsdeps(cfg):
    platform = system()
    cfg["osdeps"] = {"cmake": [install]}
    if platform == "Linux":
        cfg["osdeps"].update({"opencv": [install, "libcvaux-dev libhighgui-dev libopencv-dev"],
                              "eigen3": [install],
                              "yaml-cpp": [install],
                              "external/tinyxml": [install, "tinyxml-dev"],
                              "qwt": [install, "libqwt-qt4-dev"]})
    else:
        cfg["osdeps"].update({"opencv": [install],
                              "eigen3": [install],
                              "yaml-cpp": [install],
                              "external/tinyxml": [install, "tinyxml"],
                              "qwt": [install]})
