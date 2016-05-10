#! /usr/bin/env python

from platform import system
import sys
import os
import colorconsole as c
import execute
import bob_package

def uninstall_ode(cfg):
    execute.do(["make", "-C", cfg["devDir"]+"/simulation/ode", "clean"])

def patch_ode(cfg):
    srcPath = cfg["pyScriptDir"]+"/patches/"
    targetPath = cfg["devDir"]+"/simulation/ode-0.12"
    cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]
    execute.do(cmd+[srcPath+"ode-0.12-va_end.patch"])
    execute.do(cmd+[srcPath+"ode-0.12-lambda.patch"])
    execute.do(cmd+[srcPath+"ode-0.12-export_joint_internals.patch"])
    execute.do(cmd+[srcPath+"ode-0.12-abort.patch"])

def check_ode(cfg):
    return os.path.isfile(cfg["devDir"]+"/simulation/ode/ode.pc.in")

def fetch_ode(cfg):
    path = cfg["devDir"]+"/simulation"
    print c.BOLD+"Fetching "+"external/ode ... "+c.END,
    sys.stdout.flush
    cwd = os.getcwd()
    execute.do(["mkdir -p "+ path])
    os.chdir(path)
    if not os.path.isfile(path+"/ode-0.12.tar.gz"):
        if os.path.isdir(path+"/ode"):
            uninstall_ode(cfg)
        execute.do(["wget", "-q", "http://sourceforge.net/projects/opende/files/ODE/0.12/ode-0.12.tar.gz"])
        execute.do(["tar", "-xzf", "ode-0.12.tar.gz"])
        patch_ode(cfg)
        execute.do(["mv", "ode-0.12", "ode"])
        if not os.path.isfile("ode/ode.pc.in"):
            cfg["errors"].append("fetch: simulation/ode")
    os.chdir(cwd)
    cfg["installed"].append("simulation/ode")
    return True

def install_ode(cfg):
    if os.system("pkg-config --exists ode") == 0:
        print c.BOLD + "simulation/ode"+c.WARNING+" installed"+c.END
        return
    path = cfg["devDir"]+"/simulation/ode"
    cmd = ["./configure", 'CPPFLAGS="-DdNODEBUG"', 'CXXFLAGS="-O2 -ffast-math -fPIC"', 'CFLAGS="-O2 -ffast-math -fPIC"', "--enable-double-precision", "--prefix="+cfg["devDir"]+"/install", "--with-drawstuff=none", "--disable-demos"]
    execute.do(cmd, cfg, None, path, "simulation_ode_configure.txt")
    print c.BOLD + "simulation/ode"+c.WARNING+" configured"+c.END
    if system() == "Linux":
        libtool = os.popen('which libtool').read()
        if len(libtool) > 0:
            execute.do(["mv", "libtool", "libtool_old"], None, None, path)
            execute.do(["ln", "-s", libtool, "libtool"], None, None, path)
    execute.do(["make", "-C", path, "install", "-j", str(cfg["numCores"])], cfg, None, None, "simulation_ode_configure.txt")
    print c.BOLD + "simulation/ode"+c.WARNING+" installed"+c.END

def uninstall_minizip(cfg):
    path = cfg["devDir"]+"/external"
    cwd = os.getcwd()
    os.chdir(path+"/minizip")
    execute.do(["make", "clean"])
    os.chdir(cwd)

def patch_minizip(cfg):
    srcPath = cfg["pyScriptDir"]+"/patches/"
    targetPath = cfg["devDir"]+"/external/"
    cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]
    execute.do(cmd+[srcPath+"minizip.patch"])
    execute.do(cmd+[srcPath+"minizip_unzip.patch"])

def check_minizip(cfg):
    return os.path.isfile(cfg["devDir"]+"/external/minizip/minizip.pc.in")

def fetch_minizip(cfg):
    path = cfg["devDir"]+"/external"
    print c.BOLD+"Fetching "+"external/minizip ... "+c.END,
    sys.stdout.flush
    cwd = os.getcwd()
    os.system("mkdir -p "+ path)
    os.chdir(path)
    if not os.path.isfile(path+"/unzip101e.zip"):
        if os.path.isdir(path+"/minizip"):
            uninstall_minizip(cfg)
        execute.do(["wget", "-q", "http://www.winimage.com/zLibDll/unzip101e.zip"])
        execute.do(["unzip", "unzip101e.zip", "-d", "minizip"])
        if not os.path.isfile("minizip/minizip.c"):
            cfg["errors"].append("fetch: external/minizip")
    os.chdir(cwd)
    patch_minizip(cfg)
    return True

def install_kdl(cfg):
    bob_package.installPackage(cfg, "control/kdl/orocos_kdl")

def install_blloader(cfg):
    bob_package.installPackage(cfg, "learning/bolero/src/bl_loader", ["-DPYTHON_SUPPORT=OFF"])

def loadOverrides(cfg):
    cfg["overrides"] = {"simulation/ode": {"fetch": fetch_ode,
                                           "patch": patch_ode,
                                           "check": check_ode,
                                           "uninstall": uninstall_ode,
                                           "install": install_ode},
                        "external/minizip": {"fetch": fetch_minizip,
                                             "patch": patch_minizip,
                                             "check": check_minizip,
                                             "uninstall": uninstall_minizip},
                        "minizip": {"fetch": fetch_minizip,
                                             "patch": patch_minizip,
                                             "check": check_minizip,
                                             "uninstall": uninstall_minizip},
                        "learning/bolero/src/bl_loader": {"install": install_blloader},
                        "control/kdl": {"install": install_kdl}}
    cfg["ignorePackages"] = ["autotools", "gui/vizkit3d", "external/sisl", "rice", "boost", "dummy-dependency-n", "dummy-dependency-n-1", "dummy-dependency-0", "tools/catch", "external/yaml-cpp"]
