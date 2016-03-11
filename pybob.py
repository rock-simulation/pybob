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
import pipes
import bob_package
from threading import Thread

# todo:
#       - skip orogen project (on install)
#       - handle branches from source.yml
#       - extend information for matching patterns instead of taking longest match
#       - handle autoproj env.sh

start = datetime.datetime.now()

commands = ["buildconf", "list", "bootstrap", "fetch", "update", "install",
            "rebuild", "clean", "diff", "envsh", "uninstall", "help"]
if len(sys.argv) < 2 or sys.argv[1] not in commands:
    print c.printBold("Please specify an action. Your options are:\n" +
                       ", ".join(commands) + "\n")
    exit(0)

cfg = config.getConfiguration()
cfg["installed"] = []
cfg["updated"] = []
cfg["update"] = True
cfg["fetch"] = True
cfg["errors"] = []
cfg["continueOnError"] = True
cfg["overrides"] = {}
cfg["rebuild"] = False
cfg["profiling"] = []
cfg["checkDeps"] = True
cfg["deps"] = {}
cfg["multiprocessing"] = True
cfg["depsInverse"] = {}

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
    c.printNormal("  Recreated env.sh.")


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
    output = []
    checked = []

    while len(mans) > 0:
        p = mans.pop()
        bob_package.getDeps(cfg, p, deps, None)
        while len(deps) > 0:
            d = deps.pop()
            if d not in layout_packages and d not in handled:
                mans2 = list(layout_packages)
                if not buildconf.fetchPackage(cfg, d, mans2):
                    if d in cfg["depsInverse"]:
                        output.append([d, cfg["depsInverse"][d]])
                handled.append(d)
                for m in mans2:
                    if m not in layout_packages:
                        layout_packages.append(m)
                        mans.append(m)
    print
    for i in output:
        print c.ERROR + i[0] + c.END + " is dep from: " + ", ".join(i[1])
    if returnPackages:
        return layout_packages
    #c.printBold("Buildable packages:\n "+"\n ".join(layout_packages))

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
            bob_package.getDeps(cfg, p, deps, checked)
    #print deps
    toInstall = []
    for d in deps[::-1]:
        if d not in toInstall:
            toInstall.append(d)
    for p in layout_packages:
        if p not in toInstall:
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
                        c.printNormal("Install: "+p)
                        le = len(cfg["errors"])
                        cfg["overrides"][p]["install"](cfg)
                        if len(cfg["errors"]) <= le:
                            c.printWarning("done")
                        else:
                            c.printError("error")
                else:
                    if cfg["multiprocessing"]:
                        threads.append(Thread(target=bob_package.installPackage, args=(cfg, p)))
                    else:
                        c.printNormal("Install: "+p)
                        le = len(cfg["errors"])
                        bob_package.installPackage(cfg, p)
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
                foo = ""

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
    cfg["rebuild"] = False
    cfg["update"] = False
    env.setupEnv(cfg, False)
    buildconf_()
    fetch_()
    install_()

def help_():
    print
    printNormal("  The following commands are available:\n  "),
    c.printBold(", ".join(commands))
    printNormal('\n  Once you have the env.sh sourced, most commands\n  can also be used with "mars_command" to have\n  autocompletion (e.g. mars_install)\n')

env.setupEnv(cfg, False)
globals()[sys.argv[1]+"_"]()
printErrors()

if len(cfg["profiling"]) > 0:
    with open(cfg["devDir"]+"/autoproj/bob/profiling.yml", "w") as f:
        yaml.dump(cfg["profiling"], f, default_flow_style=False)
    with open(cfg["devDir"]+"/autoproj/bob/depsInverse.yml", "w") as f:
        yaml.dump(cfg["depsInverse"], f, default_flow_style=False)

c.printBold("Installed packages: ")
c.printNormal(cfg["installed"])
diff = datetime.datetime.now() - start
print "Time: "+str(diff)
