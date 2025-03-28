#! /usr/bin/env python
import colorconsole as c
import datetime
import yaml
import os
import buildconf
import execute
import utils
from platform import system
import sys

# todo: important we need to detect loops
def getDeps(cfg, pkg, deps, checked):
    if not pkg in cfg["deps"]:
        cfg["deps"][pkg] = []
    c.printWarning("get deps for " + pkg)
    f = None
    if os.path.exists(pkg):
        path = pkg
    else:
        path = os.path.join(cfg["devDir"], pkg)
    if pkg in cfg["overrides"] and "install_path" in cfg["overrides"][pkg]:
        path = os.path.join(cfg["devDir"], cfg["overrides"][pkg]["install_path"])
    manifest_path = os.path.join(path, "manifest.xml")
    print(manifest_path)
    if os.path.isfile(manifest_path):
        f = open(manifest_path, "r")
    if not f:
        # check for a manifest file in the package_set
        info = {}
        buildconf.getPackageInfo(cfg, pkg, info)
        if "remote" in info:
            s = cfg["devDir"]+"/autoproj/remotes/"+info["remote"]+"/manifests/"+pkg+".xml"
            if os.path.isfile(s):
                f = open(s, "r")
    if f:
        for line in f:
            l = line.strip()
            if l[:4] != "<!--":
                if not cfg["buildOptional"] and "optional" in line:
                    continue
                if "depend package" in line or "rosdep name" in line:
                    arrLine = l.split('"')
                    if len(arrLine) < 3:
                        continue
                    d = arrLine[1]
                    if not utils.ignorePackage(cfg, d) or ("orogen" in d and not cfg["orogen"]):
                    #d not in cfg["osdeps"] and
                        deps.append(d)
                        if not d in cfg["depsInverse"]:
                            cfg["depsInverse"][d] = []
                        if not pkg in cfg["depsInverse"][d]:
                            cfg["depsInverse"][d].append(pkg)
                        if not d in cfg["deps"][pkg]:
                            cfg["deps"][pkg].append(d)
                        if checked != None:
                            if d not in checked:
                                checked.append(d)
                                getDeps(cfg, d, deps, checked)
        f.close()
    if pkg in cfg["overrides"] and "additional_deps" in cfg["overrides"][pkg]:
        for d in cfg["overrides"][pkg]["additional_deps"]:
            deps.append(d)
            if not d in cfg["depsInverse"]:
                cfg["depsInverse"][d] = []
            if not pkg in cfg["depsInverse"][d]:
                cfg["depsInverse"][d].append(pkg)
            if not d in cfg["deps"][pkg]:
                cfg["deps"][pkg].append(d)
            if checked != None:
                if d not in checked:
                    checked.append(d)
                    getDeps(cfg, d, deps, checked)

def installPythonPackage(cfg, p):
    if utils.ignorePackage(cfg, p) or (not cfg["orogen"] and "orogen" in p):
        return
    path = cfg["devDir"]+"/"+p
    if p in cfg["overrides"] and "install_path" in cfg["overrides"][p]:
        path = os.path.join(cfg["devDir"], cfg["overrides"][p]["install_path"])
    if not os.path.isdir(path):
        cfg["errors"].append("install: "+path+" path not found")
        return
    if cfg["rebuild"]:
        execute.do(["rm", "-rf", path+"/build"])
    start = datetime.datetime.now()
    if not os.path.isdir(path+"/build"):
        execute.makeDir(path+"/build")
    pythonExecutable = "python"+str(sys.version_info.major)+"."+str(sys.version_info.minor)
    cmd = [pythonExecutable, "-m", "pip", "install", "--upgrade", ".", "--target="+cfg["devDir"]+"/install/lib/"+pythonExecutable+"/site-packages"]
    #working on apple:
    cmd = [pythonExecutable, "setup.py", "install", "--prefix="+cfg["devDir"]+"/install", "--single-version-externally-managed",  "--root=/"]
    print(" ".join(cmd))
    out, err, r = execute.do(cmd, cfg , None, path, p.replace("/", "_")+"_build.txt")
    if r != 0:
        print(p + c.ERROR + " build error" + c.END)
        cfg["errors"].append("build: "+p)
        return
    end = datetime.datetime.now()
    diff = end - start
    print(p + c.WARNING + " installed" + c.END)
    cfg["profiling"].append([p, {"configure time": "0"}, {"compile time": str(diff)}])
    cfg["installed"].append(p)

def installRubyPackage(cfg, p):
    if utils.ignorePackage(cfg, p) or (not cfg["orogen"] and "orogen" in p):
        return
    path = cfg["devDir"]+"/"+p
    if p in cfg["overrides"] and "install_path" in cfg["overrides"][p]:
        path = os.path.join(cfg["devDir"], cfg["overrides"][p]["install_path"])
    if not os.path.isdir(path):
        cfg["errors"].append("install: "+path+" path not found")
        return
    #if cfg["rebuild"]:
    #    execute.do(["rm", "-rf", path+"/build"])
    start = datetime.datetime.now()
    #if not os.path.isdir(path+"/build"):
    #    execute.makeDir(path+"/build")
    #pythonExecutable = "python"+str(sys.version_info.major)+"."+str(sys.version_info.minor)
    out, err, r = execute.do(["rake"], cfg , None, path, p.replace("/", "_")+"_build.txt")
    if r != 0:
        print(p + c.ERROR + " build error" + c.END)
        cfg["errors"].append("build: "+p)
        return
    major,minor = utils.get_ruby_verison()
    ruby_lib_path = cfg["devDir"]+"/install/lib/ruby"+major+"."+minor+"/"+major+"."+minor+".0"
    if not os.path.isdir(ruby_lib_path):
        execute.makeDir(ruby_lib_path)
    execute.do(["cp", "-r", "lib/*", ruby_lib_path])
    execute.do(["cp", "-r", "bin/*", cfg["devDir"]+"/install/bin"])
    # apple version
    # cmd = ["cp", "-r", "lib/*", cfg["devDir"]+"/install/lib/ruby/"+major+"."+minor+".0"]
    # print(" ".join(cmd))
    # execute.do(cmd)
    # cmd = ["cp", "-r", "bin/*", cfg["devDir"]+"/install/bin"]
    # print(" ".join(cmd))
    # execute.do(cmd)
    end = datetime.datetime.now()
    diff = end - start
    print(p + c.WARNING + " installed" + c.END)
    cfg["profiling"].append([p, {"configure time": "0"}, {"compile time": str(diff)}])
    cfg["installed"].append(p)


def installPackage(cfg, p, cmake_options=[]):
    # todo: handle path override
    if utils.ignorePackage(cfg, p) or ("orogen" in p and not cfg["orogen"]):
        return

    path = cfg["devDir"]+"/"+p
    if p in cfg["overrides"] and "install_path" in cfg["overrides"][p]:
        path = os.path.join(cfg["devDir"], cfg["overrides"][p]["install_path"])
    if not os.path.isdir(path):
        cfg["errors"].append("install: "+path+" path not found")
        return
    if not os.path.isfile(os.path.join(path,"CMakeLists.txt")):
        if os.path.isfile(os.path.join(path, "setup.py")):
            installPythonPackage(cfg, p)
            return
        if os.path.isfile(os.path.join(path, "Rakefile")):
            installRubyPackage(cfg, p)
            return
        print(p + c.WARNING + " skip \"no cmake package\"" + c.END)
        sys.stdout.flush()
        return
    if cfg["rebuild"]:
        execute.do(["rm", "-rf", path+"/build"])
    start = datetime.datetime.now()
    orogenFilename = None
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            arrF = f.split(".")
            if len(arrF) == 2 and arrF[1] == "orogen":
                orogenFilename = f
    if orogenFilename:
        # build orogen package
        orogenPath = os.path.join(path, ".orogen")
        if os.path.exists(orogenPath) and cfg["rebuild"]:
            execute.do(["rm", "-rf", orogenPath])
        transport = "corba,typelib"
        if system() == "Linux":
            transport += ",mqueue"
        if not os.path.exists(orogenPath):
            cmd = ["orogen", "--transport="+transport, "--import=std", "--extensions=cpp_proxies,modelExport --no-rtt-scripting", orogenFilename]
            if p == "base/orogen/std":
                cmd = ["orogen", "--transport="+transport, "--extensions=cpp_proxies,modelExport", orogenFilename]
            print(" ".join(cmd))
            out, err, r = execute.do(cmd, cfg, None, path, p.replace("/", "_")+"_orogen.txt")
            if r != 0:
                print(p + c.ERROR + " orogen error" + c.END)
                sys.stdout.flush()
                cfg["errors"].append("orogen: "+p)
                return

    if os.path.isdir(path+"/build"):
        cmd = ["cmake", path]
    else:
        execute.makeDir(path+"/build")
        #cmd = ["cmake", "..", "-DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install", "-DCMAKE_BUILD_TYPE=DEBUG", "-Wno-dev"]
    cmake = "cmake_"+cfg["defBuildType"]
    cmd = [cmake] + cmake_options
    if system() == "Windows":
        cmd = ["bash"] + cmd
    out, err, r = execute.do(cmd, cfg, None, path+"/build", p.replace("/", "_")+"_configure.txt")
    if r != 0:
        print(p + c.ERROR + " configure error" + c.END)
        sys.stdout.flush()
        cfg["errors"].append("configure: "+p)
        return
    print(p + c.WARNING + " configured" + c.END)
    sys.stdout.flush()
    end = datetime.datetime.now()
    diff1 = end - start
    start = end
    out, err, r = execute.do(["make", "install", "-j", str(cfg["numCores"]), "-C", path+"/build"], cfg , None, None, p.replace("/", "_")+"_build.txt")
    if r != 0:
        print(p + c.ERROR + " build error" + c.END)
        cfg["errors"].append("build: "+p)
        return
    end = datetime.datetime.now()
    diff2 = end - start
    print(p + c.WARNING + " installed" + c.END)
    cfg["profiling"].append([p, {"configure time": str(diff1)}, {"compile time": str(diff2)}])
    cfg["installed"].append(p)
