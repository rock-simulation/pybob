#! /usr/bin/env python

import sys
import os
import config
import buildconf
import environment as env
import colorconsole as c
import overrides
import osdeps
import execute
import datetime
import yaml
from threading import Thread
import pipes

start = datetime.datetime.now()

commands = ["buildconf", "list", "bootstrap", "fetch", "update", "install",
            "rebuild", "clean", "diff", "envsh", "uninstall", "help"]
if len(sys.argv) < 2 or sys.argv[1] not in commands:
    print c.printError("Please specify an action. Your options are:\n" +
                       ", ".join(commands) + "\n")
    exit(0)

cfg = config.getConfiguration()
cfg["updated"] = []
cfg["update"] = True
cfg["errors"] = []
cfg["continueOnError"] = True
cfg["overrides"] = {}
cfg["rebuild"] = False
cfg["profiling"] = []
cfg["checkDeps"] = True
cfg["deps"] = {}
cfg["multiprocessing"] = True

overrides.loadOverrides(cfg)
osdeps.loadOsdeps(cfg)

def printErrors():
    if len(cfg["errors"]) > 0:
        c.printError("\nErrors:")
        for e in cfg["errors"]:
            c.printError(" - "+e)

def buildconf_():
    global cfg
    buildconf.fetchBuildconf(cfg)
    buildconf.updatePackageSets(cfg)

def envsh_():
    global cfg
    env.setupEnv(cfg, True)
    c.printBold("  Recreated env.sh.")

# todo: important we need to detect loops
def getDeps(cfg, pkg, deps, checked):
    if not pkg in cfg["deps"]:
        cfg["deps"][pkg] = []
    #c.printWarning("get deps for " + pkg)
    if os.path.isfile(cfg["devDir"]+"/"+pkg+"/manifest.xml"):
        f = open(cfg["devDir"]+"/"+pkg+"/manifest.xml", "r")
        for line in f:
            l = line.strip()
            if l[:4] != "<!--":
                if "depend package" in line:
                    d = l.split('"')[1]
                    if d not in cfg["ignorePackages"] and d not in cfg["osdeps"]:
                        deps.append(d)
                        if not d in cfg["deps"][pkg]:
                            cfg["deps"][pkg].append(d)
                    if d not in checked:
                        getDeps(cfg, d, deps, checked)
                        #checked.append(d)
        f.close()

def fetch_(returnPackages = False):
    layout_packages = []
    if len(sys.argv) < 3:
        buildconf.fetchPackages(cfg, layout_packages)
    else:
        buildconf.fetchPackage(cfg, sys.argv[2], layout_packages)
    if not cfg["continueOnError"] and len(cfg["errors"]) > 0:
        printErrors()
        return

    # track dependencies and do the same for build and rebuild
    deps = []
    mans = list(layout_packages)
    handled = []
    while len(mans) > 0:
        p = mans.pop()
        if os.path.isfile(cfg["devDir"]+"/"+p+"/manifest.xml"):
            f = open(cfg["devDir"]+"/"+p+"/manifest.xml", "r")
            for line in f:
                l = line.strip()
                if l[:4] != "<!--":
                    if "depend package" in line:
                        deps.append(l.split('"')[1])
            f.close()
        while len(deps) > 0:
            d = deps.pop()
            if d not in layout_packages and d not in handled:
                mans2 = list(layout_packages)
                buildconf.fetchPackage(cfg, d, mans2)
                handled.append(d)
                for m in mans2:
                    if m not in layout_packages:
                        layout_packages.append(m)
                    else:
                        mans.append(m)
    if returnPackages:
        return layout_packages
    c.printBold("Buildable packages:\n "+"\n ".join(layout_packages))

def installPackage(p):
    if p in cfg["ignorePackages"]:
        return
    path = cfg["devDir"]+"/"+p
    if not os.path.isdir(cfg["devDir"]+"/"+p):
        cfg["errors"].append("install: "+p+" path not found")
        return
    if cfg["rebuild"]:
        execute.doSilent(["rm", "-rf", path+"/build"])
    start = datetime.datetime.now()
    if os.path.isdir(path+"/build"):
        cmd = ["cmake", path]
    else:
        execute.doSilent(["mkdir", "-p", path+"/build"])
        #cmd = ["cmake", "..", "-DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install", "-DCMAKE_BUILD_TYPE=DEBUG", "-Wno-dev"]
    out, err, r = execute.do(["cmake_debug"], cfg, None, path+"/build", p.replace("/", "_")+"_configure.txt")
    if r != 0:
        print c.BOLD + p+c.ERROR+" configure error"+c.END
        cfg["errors"].append("configure: "+p)
        return
    print c.BOLD + p+c.WARNING+" configured"+c.END
    end = datetime.datetime.now()
    diff1 = end - start
    start = end
    out, err, r = execute.do(["make", "install", "-j", str(cfg["numCores"]), "-C", path+"/build"], cfg , None, None, p.replace("/", "_")+"_build.txt")
    if r != 0:
        print c.BOLD + p+c.ERROR+" build error"+c.END
        cfg["errors"].append("build: "+p)
        return
    end = datetime.datetime.now()
    diff2 = end - start
    print c.BOLD + p+c.WARNING+" installed"+c.END
    cfg["profiling"].append([p, {"configure time": str(diff1)}, {"compile time": str(diff2)}])

def install_():
    global cfg
    layout_packages = []
    cfg["update"] = False
    if len(sys.argv) < 3:
        buildconf.fetchPackages(cfg, layout_packages)
    else:
        if "-n" in sys.argv:
            cfg["checkDeps"] = False
        buildconf.fetchPackage(cfg, sys.argv[2], layout_packages)
    deps = []
    checked = []
    if cfg["checkDeps"]:
        for p in layout_packages:
            getDeps(cfg, p, deps, checked)
    #print deps
    toInstall = []
    for d in deps[::-1]:
        if d not in toInstall:
            toInstall.append(d)
    for p in layout_packages:
        toInstall.append(p)
    while len(toInstall) > 0:
        threads = []
        jobs = []
        iList = list(toInstall)
        toInstall = []
        for p in iList:
            wait = False
            #c.printWarning(str(cfg["deps"][p]))
            if p in cfg["deps"]:
                for d in cfg["deps"][p]:
                    if d in iList:
                        wait = True
                        break
            if not wait:
                jobs.append(p)
                if p in cfg["overrides"] and "install" in cfg["overrides"][p]:
                    if cfg["multiprocessing"]:
                        threads.append(Thread(target=cfg["overrides"][p]["install"], args=(cfg,)))
                    else:
                        c.printBold("Install: "+p)
                        le = len(cfg["errors"])
                        cfg["overrides"][p]["install"](cfg)
                        if len(cfg["errors"]) <= le:
                            c.printWarning("done")
                        else:
                            c.printError("error")
                else:
                    if cfg["multiprocessing"]:
                        threads.append(Thread(target=installPackage, args=(p,)))
                    else:
                        c.printBold("Install: "+p)
                        le = len(cfg["errors"])
                        installPackage(p)
                        if len(cfg["errors"]) <= le:
                            c.printWarning("done")
                        else:
                            c.printError("error")
            else:
                toInstall.append(p)
        if cfg["multiprocessing"]:
            c.printBold("Install: "+str(jobs))
            le = len(cfg["errors"])
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if len(cfg["errors"]) > le:
                c.printError("error")
        

def list_():
    global cfg
    packages, w = buildconf.listPackages(cfg)
    for p in packages:
        if len(p[1]) > 0:
            print p[0],
            c.printBold(p[1])
        else:
            print p[0],
            c.printWarning(p[0])

def rebuild_():
    cfg["rebuild"] = True
    install_()

# bootstrap always updates the package information
def bootstrap_():
    cfg["rebuild"] = True
    envsh_()
    buildconf_()
    fetch_()
    install_()

def help_():
    print
    print("  The following commands are available:\n  "),
    c.printBold(", ".join(commands))
    print('\n  Once you have the env.sh sourced, most commands\n  can also be used with "mars_command" to have\n  autocompletion (e.g. mars_install)\n')

globals()[sys.argv[1]+"_"]()
printErrors()

if len(cfg["profiling"]) > 0:
    with open(cfg["devDir"]+"/autoproj/profiling.yml", "w") as f:
        yaml.dump(cfg["profiling"], f, default_flow_style=False)

diff = datetime.datetime.now() - start
print "Time: "+str(diff)
