#! /usr/bin/env python
from __future__ import print_function
from platform import system
import sys
import os
import colorconsole as c
import execute
import yaml
import bob_package
import utils
from environment import QT5_UBUNTU

def dummy(cfg):
    pass

def uninstall_ode(cfg):
    execute.do(["make", "-C", cfg["devDir"] + "/simulation/ode", "clean"])

def uninstall_ode_16(cfg):
    execute.do(["make", "-C", cfg["devDir"] + "/simulation/ode-16", "clean"])


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
    targetPath = cfg["devDir"] + "/simulation/ode-16"
    cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]

    out, err, r = execute.do(cmd + [srcPath + "ode-0.16-lambda.patch"])
    # this patch is used to inherit of dJoint wich is normaly not done by MARS
    #out, err, r = execute.do(cmd + [srcPath + "ode-0.12-export_joint_internals.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.16-abort.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.16-heightfield.patch"])
    out, err, r = execute.do(cmd + [srcPath + "ode-0.16-cmakelists.patch"])


def check_ode(cfg):
    return os.path.isfile(cfg["devDir"] + "/simulation/ode/ode.pc.in")

def check_ode_16(cfg):
    return os.path.isfile(cfg["devDir"] + "/simulation/ode-16/ode.pc.in")

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
    print(c.BOLD + "Fetching " + "external/ode-16 ... " + c.END, end="")
    sys.stdout.flush()
    cwd = os.getcwd()
    execute.makeDir(path)
    os.chdir(path)
    if not os.path.isfile(path + "/ode-0.16.tar.gz"):
        if os.path.isdir(path + "/ode-16"):
            uninstall_ode(cfg)
        execute.do(
            [
                "wget",
                "-q",
                "https://bitbucket.org/odedevs/ode/downloads/ode-0.16.tar.gz",
            ]
        )
        execute.do(["tar", "-xzf", "ode-0.16.tar.gz"])
        execute.do(["mv", "ode-0.16", "ode-16"])
        patch_ode_16(cfg)
        if not os.path.isfile("ode-16/ode.pc.in"):
            cfg["errors"].append("fetch: simulation/ode")
    os.chdir(cwd)
    cfg["installed"].append("simulation/ode-16")
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
    print(execute.decode(out))
    print(execute.decode(err))
    print(r)
    print(c.BOLD + "simulation/ode" + c.WARNING + " installed" + c.END)
    sys.stdout.flush()

# temporary used until all systems build with cmake
def install_ode_16(cfg):
    if os.path.isfile(cfg["devDir"] + "/install/lib/pkgconfig/ode.pc"):
        print(c.BOLD + "simulation/ode-16" + c.WARNING + " installed" + c.END)
        sys.stdout.flush
        return
    path = cfg["devDir"] + "/simulation/ode-16"
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

    out, err, r = execute.do(cmd, cfg, None, path, "simulation_ode-16_configure.txt")

    print(c.BOLD + "simulation/ode-16" + c.WARNING + " configured" + c.END)
    sys.stdout.flush()
    if system() == "Linux":
        libtool = os.popen("which libtool").read()
        if len(libtool) > 0:
            execute.do(["mv", "libtool", "libtool_old"], None, None, path)
            execute.do(["ln", "-s", libtool, "libtool"], None, None, path)
    cmd = ["make", "-C", path, "install", "-j", str(cfg["numCores"])]
    print(" ".join(cmd))
    out, err, r = execute.do(cmd, cfg, None, None, "simulation_ode-16_install.txt")
    print(execute.decode(out))
    print(execute.decode(err))
    print(r)
    print(c.BOLD + "simulation/ode-16" + c.WARNING + " installed" + c.END)
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

def fetch_general_git(cfg, path, package, url, hashId=None):
    path = os.path.join(cfg["devDir"], path)
    path2 = os.path.join(cfg["devDir"], package)
    print(c.BOLD + "Fetching " + package +" ... " + c.END, end="")
    sys.stdout.flush
    cwd = os.getcwd()
    if not os.path.exists(path2):
        execute.makeDir(path)
        os.chdir(path)
        execute.do(["git", "clone", url])
        if hashId:
            os.chdir(path2)
            execute.do(["git", "checkout", hashId])
    else:
        os.chdir(path2)
        execute.do(["git", "update"])
        if hashId:
            execute.do(["git", "checkout", hashId])
    os.chdir(cwd)
    return True

def fetch_rtt(cfg):
    r = fetch_general_git(cfg, "tools", "tools/rtt", "https://github.com/orocos-toolchain/rtt.git", "baaea5022b")
    if r:
        srcPath = cfg["pyScriptDir"] + "/patches/"
        targetPath = cfg["devDir"] + "/tools/rtt"
        cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]
        out, err, r = execute.do(cmd + [srcPath + "rtt.patch"])
    return r
    path = cfg["devDir"] + "/tools"
    print(c.BOLD + "Fetching " + "tools/rtt ... " + c.END, end="")
    sys.stdout.flush
    cwd = os.getcwd()
    execute.makeDir(path)
    os.chdir(path)

    if not os.path.isfile(path + "/rtt/CMakeLists.txt"):
        if os.path.isdir(path + "/rtt"):
            execute.do(["rm", "-rf", "rtt"])
        execute.do(["git", "clone", "https://github.com/orocos-toolchain/rtt.git"])
        execute.do(["git", "checkout", "baaea5022b"])

        if not os.path.isfile("rtt/CMakeLists.txt"):
            cfg["errors"].append("fetch: tools/rtt")
        srcPath = cfg["pyScriptDir"] + "/patches/"
        targetPath = cfg["devDir"] + "/tools/rtt"
        cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]
        out, err, r = execute.do(cmd + [srcPath + "rtt.patch"])

    os.chdir(cwd)
    return True

def install_rtt(cfg):
    bob_package.installPackage(cfg, "tools/rtt", ["-DENABLE_CORBA=ON -DCORBA_IMPLEMENTATION=OMNIORB"])

def fetch_typelib(cfg):
    if fetch_general_git(cfg, "tools", "tools/typelib",
                         "git@github.com:orocos-toolchain/typelib.git"):
        source = os.path.join(cfg["devDir"], "pybob/cmake/FindRuby.cmake")
        target = os.path.join(cfg["devDir"], "tools/typelib/cmake")
        execute.do(["cp", source, target])
        srcPath = cfg["pyScriptDir"] + "/patches/"
        targetPath = cfg["devDir"] + "/tools/typelib"
        cmd = ["patch", "-N", "-p0", "-d", targetPath, "-i"]
        out, err, r = execute.do(cmd + [srcPath + "typelib.patch"])
        return True
    return False

def fetch_orogen(cfg):
    folder = "orocos-toolchain"
    if system() == "Darwin":
        folder = "malter"
    return fetch_general_git(cfg, "tools", "tools/orogen",
                             "git@github.com:"+folder+"/orogen.git")

def fetch_rtt_typelib(cfg):
    folder = "orocos-toolchain"
    return fetch_general_git(cfg, "tools", "tools/rtt_typelib",
                             "git@github.com:"+folder+"/rtt_typelib.git")

def install_orocos(cfg):
    path = cfg["devDir"] + "/tools/orocos.rb"
    print(c.BOLD + "Installing " + "tools/orocos.rb ... " + c.END, end="")
    sys.stdout.flush
    cwd = os.getcwd()
    os.chdir(path)
    execute.do(["rake"])
    # todo: put ruby pat to cfg; get correct ruby version and add it to path
    major,minor = utils.get_ruby_verison()
    execute.do(["cp", "-r", "lib/orocos/orocos/*", "lib/orocos/"])
    execute.do(["cp", "-r", "lib/*", "../../install/lib/ruby"+major+"."+minor+"/"+major+"."+minor+".0"])
    execute.do(["cp", "-r", "bin/*", "../../install/bin"])

def loadOverrides(cfg):
    cfg["overrides"] = {
        "simulation/ode": {
            "fetch": fetch_ode,
            "patch": patch_ode,
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
        "rtt": {"fetch": fetch_rtt, "install": install_rtt, "install_path": "tools/rtt"},
        "typelib": {"fetch": fetch_typelib, "install_path": "tools/typelib"},
        "rtt_typelib": {"fetch": fetch_rtt_typelib, "install_path": "tools/rtt_typelib"},
        "orogen": {"fetch": fetch_orogen, "install_path": "tools/orogen"},
        "orocos.rb": {"install": install_orocos, "install_path": "tools/orocos"},
    }
    if system() == "Darwin":
        cfg["overrides"]["tools/orogen_cpp_proxies"] =  {"url": "git@github.com:malter/orogen_cpp_proxies.git"}
        cfg["overrides"]["pybind11"] = {"additional_deps": ["external/pybind11"], "install": dummy, "fetch": dummy, "patch": dummy, "check": dummy, "uninstall": dummy}
        cfg["overrides"]["pybind11_json"] = {"additional_deps": ["external/pybind11_json", "external/pybind11"], "install": dummy, "fetch": dummy, "patch": dummy, "check": dummy, "uninstall": dummy}
        cfg["overrides"]["external/pybind11_json"] = {"additional_deps": ["external/pybind11"]}

    cfg["overrides"]["tools/orogen"] = cfg["overrides"]["orogen"]
    cfg["overrides"]["tools/rtt_typelib"] = cfg["overrides"]["rtt_typelib"]
    cfg["overrides"]["tools/rtt"] = cfg["overrides"]["rtt"]
    cfg["overrides"]["tools/typelib"] = cfg["overrides"]["typelib"]
    cfg["overrides"]["tools/orocos.rb"] = cfg["overrides"]["orocos.rb"]
    cfg["overrides"]["base/orogen/std"] = {"additional_deps": ["tools/orogen_cpp_proxies", "tools/orogen_model_exporter", "tools/service_discovery"]}

    if system() == "Windows":
        cfg["overrides"]["simulation/ode-16"] = {
            "fetch": fetch_ode_16,
            "patch": patch_ode_16,
            "check": check_ode_16,
        }
    else:
        cfg["overrides"]["simulation/ode-16"] = {
            "fetch": fetch_ode_16,
            "patch": patch_ode_16,
            "check": check_ode_16,
            "uninstall": uninstall_ode_16,
            "install": install_ode_16,
        }

    cfg["ignorePackages"] = [
        "autotools",
        #"gui/vizkit3d",
        "rice",
        "dummy-dependency-n",
        "dummy-dependency-n-1",
        "dummy-dependency-0",
        "external/yaml-cpp",
        #"rtt",
        #"typelib",
        "simulation/configmaps",
        "qt4-opengl",
        "tools/graph_analysis",
    ]

    if system() == "Darwin":
        cfg["ignorePackages"].append("python")
        cfg["ignorePackages"].append("python3")
        cfg["ignorePackages"].append("python-dev")
        cfg["ignorePackages"].append("python-yaml")
        cfg["ignorePackages"].append("zlib")
        cfg["ignorePackages"].append("dataclasses")
        cfg["ignorePackages"].append("blender")
        cfg["ignorePackages"].append("gui/vizkit3d")
        cfg["ignorePackages"].append("automake")
        cfg["ignorePackages"].append("libtool")
        cfg["ignorePackages"].append("libdw")
        cfg["ignorePackages"].append("xpath-perl")
        cfg["ignorePackages"].append("boost-python") # maybe map to boost

        # for ruby tools -> should move to gemInstall in osdeps
        cfg["ignorePackages"].append("minitest")
        cfg["ignorePackages"].append("tty-table")
        cfg["ignorePackages"].append("tty-cursor")
        cfg["ignorePackages"].append("tty-prompt")
        cfg["ignorePackages"].append("thor")
        cfg["ignorePackages"].append("ruby") # system ruby is used instead
        cfg["ignorePackages"].append("ruby-dev") # system ruby is used instead
        cfg["ignorePackages"].append("rake") # system ruby is used instead
        cfg["ignorePackages"].append("kramdown")
        cfg["ignorePackages"].append("facets")
        cfg["ignorePackages"].append("flexmock")
    elif system() == "Windows":
        cfg["ignorePackages"].append("python")
        cfg["ignorePackages"].append("python-dev")
        cfg["ignorePackages"].append("python-yaml")
    elif not QT5_UBUNTU:
        cfg["ignorePackages"].append("external/osgQt")


    path = cfg["path"] + "/autoproj/overrides.d"
    if os.path.exists(path):
        for d in os.listdir(path):
            if os.path.isfile(path+"/"+d):
                try:
                    filename = os.path.join(path, d)
                    #print("load: " + filename)
                    with open(filename) as f:
                        ov = yaml.safe_load(f)
                    #print(ov)
                    for it in ov:
                        for key, value in it.items():
                            cfg["overrides"][key] = value
                except:
                    pass
    

    filename = cfg["path"] + "/autoproj/overrides.yml"
    if os.path.isfile(filename):
        with open(filename) as f:
            ov = yaml.safe_load(f)
        if ov is not None and "overrides" in ov and ov["overrides"] is not None:
            for it in ov["overrides"]:
                for key, value in it.items():
                    cfg["overrides"][key] = value
