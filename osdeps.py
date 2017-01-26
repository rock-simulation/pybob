#! /usr/bin/env python

import os
import colorconsole as c
import execute
from platform import system

def install(cfg, pkg):
    platform = system()
    if pkg == "":
      return
    if pkg == "cmake":
        if os.popen('which cmake').read():
            return
    elif pkg == "pkg-config":
        if os.popen('which pkg-config').read():
            return
    elif platform == "Windows":
        out,err,r = execute.do(["pacman", "-Qq", "mingw-w64-x86_64-"+pkg])
        if len(out) > 0:
            return
    elif os.system('pkg-config --exists '+pkg) == 0:
        return

    if platform == "Windows":
        execute.do(["pacman", "--noconfirm", "-S", "mingw-w64-x86_64-"+pkg])
    elif platform == "Darwin":
        pkgstr = '" '+pkg+' "'
        out, err, r = execute.do(['port', 'installed', '|' ,'grep', pkgstr])
        if len(out) > len(pkg):
            return
        c.printBold("Installing os dependency: "+pkg)
        execute.do(["sudo", "port", "install", pkg])
    else:
        c.printBold("Installing os dependency: "+pkg)
        os.system("sudo apt-get install " + pkg)

def loadOsdeps(cfg):
    platform = system()
    cfg["osdeps"] = {"cmake": [install]}

    if platform == "Linux":
        cfg["osdeps"].update({"opencv": [install, "libcvaux-dev libhighgui-dev libopencv-dev"],
                              "eigen3": [install, "libeigen3-dev"],
                              "yaml-cpp": [install, "libyaml-cpp-dev"],
                              "external/yaml-cpp": [install, "libyaml-cpp-dev"],
                              "external/tinyxml": [install, "libtinyxml-dev"],
                              "qwt": [install, "libqwt-qt4-dev"],
                              "qwt5-qt4": [install, "libqwt-qt4-dev"],
                              "pkg-config": [install], "cmake": [install],
                              "qt4": [install, "qt4-default"],
                              "qt": [install, "qt4-default"],
                              "osg": [install, "libopenscenegraph-dev"],
                              "boost": [install, "libboost-all-dev"]})
    elif platform == "Windows":
        cfg["osdeps"].update({"opencv": [install],
                              "eigen3": [install],
                              "yaml-cpp": [install],
                              "external/yaml-cpp": [install, "yaml-cpp"],
                              "external/tinyxml": [install, "tinyxml"],
                              "qwt": [install, "qwt-qt4"],
                              "qwt5-qt4": [install, "foo"],
                              "pkg-config": [install], "cmake": [install],
                              "qt4": [install, "foo"],
                              "qt": [install, "qt5"],
                              "osg": [install, "OpenSceneGraph"],
                              "boost": [install]})
    else:
        cfg["osdeps"].update({"opencv": [install],
                              "eigen3": [install],
                              "yaml-cpp": [install],
                              "external/tinyxml": [install, "tinyxml"],
                              "qwt": [install],
                              "qwt5-qt4": [install, "qwt"],
                              "pkg-config": [install],
                              "qt4": [install, ""], "cmake": [install],
                              "pkg-config": [install],
                              "boost": [install],
                              "osg": [install, ""]})
