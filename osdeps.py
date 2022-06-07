#! /usr/bin/env python
from __future__ import print_function
import os
import colorconsole as c
import execute
from platform import system
import sys
from environment import QT5_UBUNTU

def gemInstall(cfg, pkg):
    cmd = ["sudo", "gem", "install", pkg]

    print(" ".join(cmd))
    out, err, r = execute.do(cmd)
    if len(out) > 0:
        return

def pipInstall(cfg, pkg):
    """PIP installation command."""
    platform = system()
    log = cfg["devDir"] + "/autoproj/bob/logs/os_deps.txt"
    path = cfg["devDir"]+"/autoproj/bob/logs"
    if not os.path.isdir(path):
        execute.makeDir(path)
    with open(log, "a") as f:
        f.write("@pip "+pkg+"\n")

    if platform == "Windows":
        if not os.popen('which pip').read():
            out,err,r = execute.do(["pacman", "--noconfirm", "-S", "mingw-w64-x86_64-python2-pip"])
            if len(out) > 0:
                return
        cmd = ["pip", "install", "-U", "--noinput", pkg]
    else:
        pipCmd = "pip" + str(sys.version_info.major)
        cmd = ["yes", "|", pipCmd, "install", "-U", pkg]

    print(" ".join(cmd))
    out, err, r = execute.do(cmd)
    if len(out) > 0:
        return


def install(cfg, pkg):
    """Standard system package manager installation command."""
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
        f.write(pkg+"\n")

    if platform == "Windows":
        out,err,r = execute.do(["pacman", "-Qq", "mingw-w64-x86_64-"+pkg])
        if len(out) > 0:
            return
    elif os.system('pkg-config --exists '+pkg) == 0:
        return

    if platform == "Windows":
        if pkg == "cython":
            execute.do(["pacman", "--noconfirm", "-S", "mingw-w64-x86_64-cython2"])
        execute.do(["pacman", "--noconfirm", "-S", "mingw-w64-x86_64-"+pkg])
    elif platform == "Darwin":
        pkgstr = '" '+pkg+' "'
        out, err, r = execute.do(['port', 'installed', '|' ,'grep', pkgstr])
        if len(out) > len(pkg):
            return
        print(c.BOLD + "Installing os dependency: "+pkg + c.END, end="")
        execute.do(["sudo", "port", "install", pkg])
    else:
        out, err, r = execute.do(['dpkg', '-s', pkg])
        if r != 0:
            print(c.BOLD + "Installing os dependency: "+pkg + c.END, end="")
            arrPkg = pkg.split()
            for p in arrPkg:
                os.system("sudo apt-get install -y " + p)
        else:
            for line in out.split(b"\n"):
                arrLine = line.split()
                if len(arrLine) > 2 and arrLine[1] == pkg:
                    if arrLine[0] != "ii":
                        print(c.BOLD + "Installing os dependency: " + pkg + c.END, end="")
                        arrPkg = pkg.split()
                        for p in arrPkg:
                            os.system("sudo apt-get install -y " + p)
                    break


def loadOsdeps(cfg):
    platform = system()
    cfg["osdeps"] = {"cmake": [install]}

    if platform == "Linux":
        if sys.version_info.major >= 3:
            cfg["osdeps"].update({
                "python": [install, "python3-dev"],
                "python-dev": [install, "python3-dev"],
                "python-yaml": [install, "python3-yaml"],
                "pyyaml": [install, "python3-yaml"],
                "python-numpy": [install, "python3-numpy"],
                "python-scipy": [install, "python3-scipy"],
                "scipy": [install, "python3-scipy"],
                "python-sklearn": [install, "python3-sklearn"],
                "scikit-learn": [install, "python3-sklearn"],
                "python-matplotlib": [install, "python3-matplotlib"],
                "matplotlib": [install, "python3-matplotlib"],
                "numpy": [install, "python3-numpy"],
                "python3-pkgconfig": [install],
                "cython": [install, "cython3"],
                })
        else:
            cfg["osdeps"].update({
                "python": [install, "python-dev"],
                "python-dev": [install],
                "python-yaml": [install],
                "pyyaml": [install, "python-yaml"],
                "python-numpy": [install],
                "python-scipy": [install],
                "scipy": [install],
                "python-sklearn": [install],
                "scikit-learn": [install, "python-sklearn"],
                "python-matplotlib": [install],
                "matplotlib": [install, "python-matplotlib"],
                "numpy": [install, "python-numpy"],
                "cython": [install],
                })

        cfg["osdeps"].update({
            "urdf-parser-py": [pipInstall, "urdf-parser-py"],
            "torch": [pipInstall],
            "torch-vision": [pipInstall],
            "torchdiffeq": [pipInstall, "git+https://github.com/rtqichen/torchdiffeq"],
            "torchsummary": [pipInstall],
            "tensorboard": [pipInstall],
            "pyswarms": [pipInstall],
            "eigen3": [install, "libeigen3-dev"],
            "yaml-cpp": [install, "libyaml-cpp-dev"],
            "yaml": [install, "libyaml-dev"],
            "external/yaml-cpp": [install, "libyaml-cpp-dev"],
            "external/tinyxml": [install, "libtinyxml-dev"],
            "qwt": [install, "libqwt-qt4-dev"],
            "qwt5-qt4": [install, "libqwt-qt4-dev"],
            "pkg-config": [install], "cmake": [install],
            "osg": [install, "libopenscenegraph-dev"],
            "boost": [install, "libboost-all-dev"],
            "zlib": [install, "zlib1g-dev"],
            "jsoncpp": [install, "libjsoncpp-dev"],
            "lua51": [install, "liblua5.1-0-dev"],
            "curl": [install, "libcurl4-gnutls-dev"],
            "utilrb": [gemInstall],
            "hoe": [gemInstall],
            "hoe-yard": [gemInstall],
            "yard": [gemInstall],
            "rake-compiler": [gemInstall],
            "omniorb": [install, "omniorb-nameserver libomniorb4-dev libomniorb4-2"],
            })
        if QT5_UBUNTU:
            cfg["osdeps"]["qt"] = [install, "qt5-default"]
            cfg["osdeps"]["qtwebkit"] = [install, "libqt5webkit5-dev"]
            cfg["osdeps"]["opencv"] = [install, "libopencv-dev"]
            # also override qt4 deps
            cfg["osdeps"]["qt4"] = [install, "qt5-default"]
            cfg["osdeps"]["qt4-webkit"] = [install, "libqt5webkit5-dev"]

        else:
            cfg["osdeps"]["qt"] = [install, "qt4-default"]
            cfg["osdeps"]["qtwebkit"] = [install, "libqtwebkit-dev"]
            cfg["osdeps"]["opencv"] = [install, "libcvaux-dev libhighgui-dev libopencv-dev"]
            cfg["osdeps"]["qt4"] = [install, "qt4-default"]
            cfg["osdeps"]["qt4-webkit"] = [install, "libqtwebkit-dev"]

        if not cfg["buildOptional"]:
            cfg["osdeps"]["qt4"] = [install, "libqt4-dev"]
            cfg["osdeps"]["qt"] = [install, "libqt4-dev"]
            cfg["osdeps"]["boost"] = [install, "libboost-system-dev libboost-thread-dev libboost-test-dev  libboost-filesystem-dev"]
    elif platform == "Windows":
        cfg["osdeps"].update({"opencv": [install],
                              "eigen3": [install],
                              "yaml-cpp": [install],
                              "external/yaml-cpp": [install, "yaml-cpp"],
                              "external/tinyxml": [install, "tinyxml"],
                              "external/protobuf": [install, "protobuf"],
                              "qwt": [install, "qwt-qt4"],
                              "qwt5-qt4": [install, "foo"],
                              "pkg-config": [install], "cmake": [install],
                              "qt4": [install, "foo"],
                              #"qtwebkit": [install, "todo"],
                              #"qt4-webkit": [install, "todo"],
                              "qt": [install, "qt5"],
                              "osg": [install, "OpenSceneGraph"],
                              "osgQt": [install, "osgQt"],
                              "boost": [install],
                              "jsoncpp": [install],
                              "python-numpy": [install, "python2-numpy"],
                              "numpy": [install, "python2-numpy"],
                              "python-scipy": [install, "python2-scipy"],
                              "scipy": [install, "python2-scipy"],
                              "python-sklearn": [pipInstall, "sklearn"],
                              "scikit-learn": [pipInstall, "sklearn"],
                              "urdf-parser-py": [pipInstall, "urdf-parser-py"],
                              "python-matplotlib": [install, "python2-matplotlib"],
                              "matplotlib": [install, "python2-matplotlib"],
                              "cython": [install],
                              "yaml": [install, "libyaml"],
                              "utilrb": [gemInstall, "utilrb"],
                              "zlib": [install]})
    else: # Darwin
        pyprefix = "py"+str(sys.version_info.major)+str(sys.version_info.minor)+"-"
        cfg["osdeps"].update({"opencv": [install],
                              "eigen3": [install],
                              "yaml-cpp": [install],
                              "jsoncpp": [install],
                              "external/tinyxml": [install, "tinyxml"],
                              "qwt": [install],
                              "qwt5-qt4": [install, "qwt"],
                              "pkg-config": [install],
                              "qt4": [install, "qt5"], "cmake": [install],
                              "qtwebkit": [install, "qt5-qtwebkit"],
                              "qt4-webkit": [install, "qt5-qtwebkit"],
                              "qt": [install, "qt5"],
                              "pkg-config": [install],
                              "boost": [install],
                              "osg": [install, "OpenSceneGraph"],
                              "numpy": [install, pyprefix+"numpy"],
                              "cython": [install, pyprefix+"cython"],
                              "cython3": [install, pyprefix+"cython"],
                              "yaml": [install, "libyaml"],
                              "curl": [install],
                              "python-numpy": [install, pyprefix+"numpy"],
                              "python-scipy": [install, pyprefix+"scipy"],
                              "pyyaml": [install, pyprefix+"yaml"],
                              "python3-yaml": [install, pyprefix+"yaml"],
                              "scipy": [install, pyprefix+"scipy"],
                              "python-sklearn": [install, pyprefix+"scikit-learn"],
                              "scikit-learn": [install, pyprefix+"scikit-learn"],
                              "urdf-parser-py": [pipInstall, "urdf-parser-py"],
                              "omniorb": [install, "omniorb"],
                              "utilrb": [gemInstall, "utilrb"],
                              "ruby-backports": [gemInstall, "backports"],
                              "metaruby": [gemInstall, "metaruby"],
                              "lemon": [install, "lemon"],
                              "fftw3": [install, "fftw-3"],
                              "uriparser": [install],
                              "python-matplotlib": [install, pyprefix+"matplotlib"],
                              "matplotlib": [install, pyprefix+"matplotlib"],
                              "python3-pip": [install, pyprefix+"pip"],
                              "python3-setuptools": [install, pyprefix+"setuptools"],
                              "python3-setuptools_48": [install, pyprefix+"setuptools=4.8"],
                              "python3-pkgconfig": [install, pyprefix+"pkgconfig"],
                              "python3-nose": [install, pyprefix+"nose"],
                              "python3-git": [install, pyprefix+"git"],
                              "python3-path": [install, pyprefix+"path"],
                              "python3-jinja2": [install, pyprefix+"jinja2"],
                              "python-markdown": [install, "py-markdown2"],
                              "pandas": [pipInstall, "pandas"],
                              "tensorflow": [pipInstall, "tensorflow"],
                              "keras": [install, pyprefix+"keras"],
                              "torch": [install, pyprefix+"pytorch"],
                              "python3-requests": [install, pyprefix+"requests"],
                              "python3-flask_restful": [install, pyprefix+"flask"],
                              "pyswarms": [pipInstall, "pyswarms"],
                              "torchdiffeq": [pipInstall, "torchdiffeq"],
                              "torch-optimizer": [pipInstall, "torch-optimizer"],
                              "ai": [pipInstall, "ai ai.cs"],
                              "pymock": [pipInstall, "pymock"],
                              "pylxml": [install, pyprefix+"lxml"],
                              "torchsummary": [pipInstall, "torchsummary"],
                              "colorlog": [pipInstall, "colorlog"],
                              "gremlinpython3_4_6": [pipInstall, "gremlinpython=3.4.6"],
                              "owlready2": [pipInstall, "Owlready2"],
                              "sigc": [install, "libsigcxx2"],
                              "hoe": [gemInstall],
                              "hoe-yard": [gemInstall],
                              "yard": [gemInstall],
                              "rake-compiler": [gemInstall],
                              "concurrent-ruby": [gemInstall],
                              "pastel": [gemInstall],
                              "hooks": [gemInstall],
                              "rgl": [gemInstall],
                              "websocket-gem": [gemInstall, "websocket"],
                              "binding_of_caller": [gemInstall],
                              "state_machine": [gemInstall],
                              "avahi": [install],
                              "poco": [install],
                              "nlohmann-json": [install],
                              "libgit2": [install],
                              "xdot": [install, "graphviz"],
                              "libxml2": [install],
})
