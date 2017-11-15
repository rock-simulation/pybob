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

    log = cfg["devDir"] + "/autoproj/bob/logs/os_deps.txt"
    path = cfg["devDir"]+"/autoproj/bob/logs"
    if not os.path.isdir(path):
        execute.makeDir(path)
    with open(log, "a") as f:
        f.write(" "+pkg)

    if platform == "Windows":
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
        print c.BOLD + "Installing os dependency: "+pkg + c.END,
        execute.do(["sudo", "port", "install", pkg])
    else:
        out, err, r = execute.do(['dpkg', '-l', pkg])
        if len(err) >  5:
            print c.BOLD + "Installing os dependency: "+pkg + c.END,
            os.system("sudo apt-get install -y " + pkg)
        else:
            for line in out.split("\n"):
                arrLine = line.split()
                if len(arrLine) > 2 and arrLine[1] == pkg:
                    if arrLine[0] != "ii":
                        print c.BOLD + "Installing os dependency: "+pkg + c.END,
                        os.system("sudo apt-get install -y " + pkg)
                    break


def loadOsdeps(cfg):
    platform = system()
    cfg["osdeps"] = {"cmake": [install]}

    if platform == "Linux":
        cfg["osdeps"].update({"opencv": [install, "libcvaux-dev libhighgui-dev libopencv-dev"],
                              "eigen3": [install, "libeigen3-dev"],
                              "yaml-cpp": [install, "libyaml-cpp-dev"],
                              "yaml": [install, "libyaml-dev"],
                              "external/yaml-cpp": [install, "libyaml-cpp-dev"],
                              "external/tinyxml": [install, "libtinyxml-dev"],
                              "qwt": [install, "libqwt-qt4-dev"],
                              "qwt5-qt4": [install, "libqwt-qt4-dev"],
                              "pkg-config": [install], "cmake": [install],
                              "qt4": [install, "qt4-default"],
                              "qt": [install, "qt4-default"],
                              "osg": [install, "libopenscenegraph-dev"],
                              "boost": [install, "libboost-all-dev"],
                              "python": [install, "python-dev"],
                              "python-dev": [install],
                              "python-yaml": [install],
                              "python-numpy": [install],
                              "numpy": [install, "python-numpy"],
                              "cython": [install],
                              "zlib": [install, "zlib1g-dev"],
                              "jsoncpp": [install, "libjsoncpp-dev"],
                              "curl": [install, "libcurl4-gnutls-dev"]})
        if not cfg["buildOptional"]:
            cfg["osdeps"]["qt4"] = [install, "libqt4-dev"]
            cfg["osdeps"]["qt"] = [install, "libqt4-dev"]
            cfg["osdeps"]["boost"] = [install, "libboost-system-dev libboost-thread-dev libboost-test-dev"]
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
                              "osgQt": [install, "osgQt"],
                              "boost": [install],
                              "jsoncpp": [install],
                              "python-numpy": [install, "python2-numpy"],
                              "numpy": [install, "python2-numpy"],
                              "cython": [install],
                              "yaml": [install, "libyaml"],
                              "zlib": [install]})
    else:
        cfg["osdeps"].update({"opencv": [install],
                              "eigen3": [install],
                              "yaml-cpp": [install],
                              "jsoncpp": [install],
                              "external/tinyxml": [install, "tinyxml"],
                              "qwt": [install],
                              "qwt5-qt4": [install, "qwt"],
                              "pkg-config": [install],
                              "qt4": [install, ""], "cmake": [install],
                              "pkg-config": [install],
                              "boost": [install],
                              "osg": [install, ""],
                              "numpy": [install, "py-numpy"],
                              "cython": [install, "py-cython"],
                              "yaml": [install, "libyaml"]})
