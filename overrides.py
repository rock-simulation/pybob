#! /usr/bin/env python
from __future__ import print_function
from platform import system
import sys
import os
import colorconsole as c
import execute
import yaml
import bob_package
from platform import system


def uninstall_ode(cfg):
    execute.do(["make", "-C", cfg["devDir"] + "/simulation/ode", "clean"])


def patch_ode(cfg):
    srcPath = cfg["pyScriptDir"] + "/patches/"
    targetPath = cfg["devDir"] + "/simulation/ode-0.12"
    cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]
    out, err, r = execute.do(cmd + [srcPath + "ode-0.12-va_end.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.12-lambda.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.12-export_joint_internals.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.12-abort.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.12-heightfield.patch"])

def patch_ode_16(cfg):
    srcPath = cfg["pyScriptDir"] + "/patches/"
    targetPath = cfg["devDir"] + "/simulation/ode-0.16"
    cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]

    out, err, r = execute.do(cmd + [srcPath + "ode-0.16-lambda.patch"])
    # this patch is used to inherit of dJoint wich is normaly not done by MARS
    #out, err, r = execute.do(cmd + [srcPath + "ode-0.12-export_joint_internals.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.16-abort.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.16-heightfield.patch"])


def check_ode(cfg):
    return os.path.isfile(cfg["devDir"] + "/simulation/ode/ode.pc.in")


def fetch_ode(cfg):
    path = cfg["devDir"] + "/simulation"
    print(c.BOLD + "Fetching " + "external/ode ... " + c.END, end="")
    sys.stdout.flush()
    cwd = os.getcwd()
    execute.makeDir(path)
    os.chdir(path)
    if not os.path.isfile(path + "/ode-0.12.tar.gz"):
        if os.path.isdir(path + "/ode"):
            uninstall_ode(cfg)
        execute.do(
            [
                "wget",
                "-q",
                "http://sourceforge.net/projects/opende/files/ODE/0.12/ode-0.12.tar.gz",
            ]
        )
        execute.do(["tar", "-xzf", "ode-0.12.tar.gz"])
        patch_ode(cfg)
        execute.do(["mv", "ode-0.12", "ode"])
        if not os.path.isfile("ode/ode.pc.in"):
            cfg["errors"].append("fetch: simulation/ode")
    os.chdir(cwd)
    cfg["installed"].append("simulation/ode")
    return True

def fetch_ode_16(cfg):
    path = cfg["devDir"] + "/simulation"
    print(c.BOLD + "Fetching " + "external/ode ... " + c.END, end="")
    sys.stdout.flush()
    cwd = os.getcwd()
    execute.makeDir(path)
    os.chdir(path)
    if not os.path.isfile(path + "/ode-0.16.tar.gz"):
        if os.path.isdir(path + "/ode"):
            uninstall_ode(cfg)
        execute.do(
            [
                "wget",
                "-q",
                "https://bitbucket.org/odedevs/ode/downloads/ode-0.16.tar.gz",
            ]
        )
        execute.do(["tar", "-xzf", "ode-0.16.tar.gz"])
        patch_ode_16(cfg)
        execute.do(["mv", "ode-0.16", "ode"])
        if not os.path.isfile("ode/ode.pc.in"):
            cfg["errors"].append("fetch: simulation/ode")
    os.chdir(cwd)
    cfg["installed"].append("simulation/ode")
    return True


def install_ode(cfg):
    if os.path.isfile(cfg["devDir"] + "/install/lib/pkgconfig/ode.pc"):
        print(c.BOLD + "simulation/ode" + c.WARNING + " installed" + c.END)
        sys.stdout.flush
        return
    path = cfg["devDir"] + "/simulation/ode"
    cmd = [
        'CXXFLAGS="-O2 -ffast-math -fPIC"',
        'CFLAGS="-O2 -ffast-math -fPIC"',
        "--enable-double-precision",
        "--prefix=" + cfg["devDir"] + "/install",
        "--with-drawstuff=none",
        "--disable-demos",
    ]
    # cmd = ['CPPFLAGS="-DdNODEBUG"', 'CXXFLAGS="-O2 -ffast-math -fPIC"', 'CFLAGS="-O2 -ffast-math -fPIC"', "--enable-double-precision", "--prefix="+cfg["devDir"]+"/install", "--with-drawstuff=none", "--disable-demos"]
    if system() == "Windows":
        cmd = ["bash", "configure"] + cmd
    else:
        cmd = ["./configure"] + cmd

    out, err, r = execute.do(cmd, cfg, None, path, "simulation_ode_configure.txt")

    print(c.BOLD + "simulation/ode" + c.WARNING + " configured" + c.END)
    sys.stdout.flush()
    if system() == "Linux":
        libtool = os.popen("which libtool").read()
        if len(libtool) > 0:
            execute.do(["mv", "libtool", "libtool_old"], None, None, path)
            execute.do(["ln", "-s", libtool, "libtool"], None, None, path)
    cmd = ["make", "-C", path, "install", "-j", str(cfg["numCores"])]
    print(" ".join(cmd))
    out, err, r = execute.do(cmd, cfg, None, None, "simulation_ode_install.txt")
    print(out)
    print(err)
    print(r)
    print(c.BOLD + "simulation/ode" + c.WARNING + " installed" + c.END)
    sys.stdout.flush()


def uninstall_minizip(cfg):
    path = cfg["devDir"] + "/external"
    cwd = os.getcwd()
    os.chdir(path + "/minizip")
    execute.do(["make", "clean"])
    os.chdir(cwd)


def patch_minizip(cfg):
    srcPath = cfg["pyScriptDir"] + "/patches/"
    targetPath = cfg["devDir"] + "/external/"
    cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]
    execute.do(cmd + [srcPath + "minizip.patch"])
    execute.do(cmd + [srcPath + "minizip_unzip.patch"])


def check_minizip(cfg):
    return os.path.isfile(cfg["devDir"] + "/external/minizip/minizip.pc.in")


def fetch_minizip(cfg):
    path = cfg["devDir"] + "/external"
    print(c.BOLD + "Fetching " + "external/minizip ... " + c.END, end="")
    sys.stdout.flush
    cwd = os.getcwd()
    execute.makeDir(path)
    os.chdir(path)
    if not os.path.isfile(path + "/unzip101e.zip"):
        if os.path.isdir(path + "/minizip"):
            uninstall_minizip(cfg)
        execute.do(["wget", "-q", "http://www.winimage.com/zLibDll/unzip101e.zip"])
        execute.do(["unzip", "unzip101e.zip", "-d", "minizip"])
        if not os.path.isfile("minizip/minizip.c"):
            cfg["errors"].append("fetch: external/minizip")
    os.chdir(cwd)
    patch_minizip(cfg)
    return True

def fetch_rbdl(cfg):
    path = cfg["devDir"] + "/external"
    print(c.BOLD + "Fetching " + "external/rbdl ... " + c.END, end="")
    sys.stdout.flush
    cwd = os.getcwd()
    execute.makeDir(path)
    os.chdir(path)

    if not os.path.isfile(path + "/rbdl/CMakeLists.txt"):
        if os.path.isdir(path + "/rbdl"):
            execute.do(["rm", "-rf", "rbdl"])
        execute.do(["hg", "clone", "https://bitbucket.org/rbdl/rbdl"])

        if not os.path.isfile("rbdl/CMakeLists.txt"):
            cfg["errors"].append("fetch: external/rbdl")
    os.chdir(cwd)
    return True


def install_kdl(cfg):
    bob_package.installPackage(cfg, "control/kdl/orocos_kdl")


def install_blloader(cfg):
    bob_package.installPackage(
        cfg, "learning/bolero/src/bl_loader", ["-DPYTHON_SUPPORT=OFF"]
    )


def check_protobuf(cfg):
    return os.path.isfile(cfg["devDir"] + "/external/protobuf/protobuf.pc.in")


def install_protobuf(cfg):
    # todo add curl dependency
    cmd = ["pkg-config", "--exists", "protobuf"]
    out, err, r = execute.do(cmd)
    if r == 0:
        print(c.BOLD + "external/protobuf" + c.WARNING + " installed" + c.END)
        sys.stdout.flush()
        return
    path = cfg["devDir"] + "/external/protobuf"
    cmd = ["./autogen.sh; ./configure -prefix=" + cfg["devDir"] + "/install"]
    out, err, r = execute.do(cmd, cfg, None, path, "external_protobuf_configure.txt")

    print(c.BOLD + "external/protobuf" + c.WARNING + " configured" + c.END)
    sys.stdout.flush()
    cmd = ["make", "-C", path, "install", "-j", str(cfg["numCores"])]
    out, err, r = execute.do(cmd, cfg, None, None, "external_protobuf_build.txt")
    cmd = ["python", "setup.py", "build"]
    # print " ".join(cmd)
    out, err, r = execute.do(
        cmd, cfg, None, path + "/python", "external_protobuf_build_python.txt"
    )

    cmd = [
        "cp",
        "-r",
        "build/lib/google",
        cfg["devDir"] + "/install/lib/python2.7/site-packages",
    ]
    out, err, r = execute.do(
        cmd, cfg, None, path + "/python", "external_protobuf_build_python_install.txt"
    )

    print(c.BOLD + "external/protobuf" + c.WARNING + " installed" + c.END)
    sys.stdout.flush()


def uninstall_protobuf(cfg):
    path = cfg["devDir"] + "/external"
    cwd = os.getcwd()
    os.chdir(path + "/protobuf")
    execute.do(["make", "clean"])
    os.chdir(cwd)


def loadOverrides(cfg):
    cfg["overrides"] = {
        "simulation/ode": {
            "fetch": fetch_ode,
            "patch": patch_ode,
            "check": check_ode,
            "uninstall": uninstall_ode,
            "install": install_ode,
        },
        "simulation/ode-16": {
            "fetch": fetch_ode_16,
            "patch": patch_ode_16,
            "check": check_ode,
            "uninstall": uninstall_ode,
            "install": install_ode,
        },
        "external/minizip": {
            "fetch": fetch_minizip,
            "patch": patch_minizip,
            "check": check_minizip,
            "uninstall": uninstall_minizip,
        },
        "minizip": {
            "fetch": fetch_minizip,
            "patch": patch_minizip,
            "check": check_minizip,
            "uninstall": uninstall_minizip,
        },
        "external/protobuf": {
            "check": check_protobuf,
            "install": install_protobuf,
            "uninstall": uninstall_protobuf,
        },
        # "learning/bolero/src/bl_loader": {"install": install_blloader},
        "control/kdl": {"install": install_kdl},
        "control/urdfdom": {"additional_deps": ["base/console_bridge"]},
        "external/rbdl": {"fetch": fetch_rbdl},
    }
    cfg["ignorePackages"] = [
        "autotools",
        "gui/vizkit3d",
        "rice",
        "dummy-dependency-n",
        "dummy-dependency-n-1",
        "dummy-dependency-0",
        "external/yaml-cpp",
        "rtt",
        "typelib",
        "simulation/configmaps",
        "qt4-opengl",
    ]

    if system() == "Darwin":
        cfg["ignorePackages"].append("python")
        cfg["ignorePackages"].append("python-dev")
        cfg["ignorePackages"].append("python-yaml")
        cfg["ignorePackages"].append("zlib")
    elif system() == "Windows":
        cfg["ignorePackages"].append("python")
        cfg["ignorePackages"].append("python-dev")
        cfg["ignorePackages"].append("python-yaml")

    filename = cfg["path"] + "/autoproj/overrides.yml"
    if os.path.isfile(filename):
        with open(filename) as f:
            ov = yaml.load(f)
        if ov is not None and "overrides" in ov and ov["overrides"] is not None:
            for it in ov["overrides"]:
                for key, value in it.items():
                    cfg["overrides"][key] = value
