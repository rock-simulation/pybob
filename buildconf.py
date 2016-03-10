#! /usr/bin/env python
import os
import sys
import yaml
import colorconsole as c
import multiprocessing
import execute
import re

def setupCfg(cfg):
    # todo: handle this files differently
    path = cfg["pyScriptDir"]
    # load server information if not already done
    if not "server" in cfg:
        with open(path+"/server.yml") as f:
            cfg["server"] = yaml.load(f)

    # load the package information if not already done
    path = cfg["devDir"]+"/autoproj/"
    if not "packages" in cfg and os.path.isfile(path+"packages.yml"):
        with open(path+"packages.yml") as f:
            cfg["packages"] = yaml.load(f)

def listPackages(cfg):
    path = cfg["devDir"]+"/autoproj/";
    packages = []
    wildcard_packages = []
    for d in os.listdir(path+"remotes"):
        if os.path.isdir(path+"remotes/"+d):
            packages.append([d, ""])
            with open(path+"remotes/"+d+"/source.yml") as f:
                source = yaml.load(f)
            if "version_control" in source:
                for p in source["version_control"]:
                    # some rock configuration files are not well formated
                    # which results in a list with one key having no value
                    # instead of a dict
                    key = ""
                    items = p.items()
                    if len(items) == 1:
                        key, value = items[0]
                    else:
                        for k, v in items:
                            if not v:
                                key = k
                                break
                    if "*" not in key:
                        packages.append([d, key])
                    else:
                        wildcard_packages.append([d, key])
            if os.path.isfile(path+"remotes/"+d+"/libs.autobuild"):
                with open(path+"remotes/"+d+"/libs.autobuild") as f:
                    for line in f:
                        if "_package" in line:
                            l = line.split("_package")[1]
                            arrLine = None
                            if '"' in l:
                                arrLine = line.split('"')
                            elif "'" in l:
                                arrLine = line.split("'")
                            if arrLine:
                                if "#" not in arrLine[0]:
                                    packages.append([d, arrLine[1]])

    return (packages, wildcard_packages)

def checkBaseName(package, info):
    if "$" in info["gitPackage"] and "*" not in package:
        info["basename"] = info["gitPackage"]
        info["gitPackage"] = info["gitPackage"].replace("$PACKAGE_BASENAME",
                                                        package.split("/")[-1])

def clonePackage(cfg, package, server, gitPackage):
    clonePath = package
    if package[-3:] == "/.*":
        clonePath = package[:-2] + gitPackage.split("/")[1].split(".")[0]
    if package in cfg["updated"]:
        return
    else:
        cfg["updated"].append(package)
    clonePath = cfg["devDir"]+"/"+clonePath
    if os.path.isdir(clonePath):
        if cfg["update"]:
            print "Updating "+clonePath+" ... "+c.END,
            execute.do(["git", "-C", clonePath, "pull"], cfg)
    else:
        if not cfg["update"]:
            c.printError(package+" is not cloned, call mars_fetch to update or clone the packages.")
            cfg["errors"].append("missing: "+package)
        else:
            print "Fetching "+clonePath+" ... "+c.END,
            sys.stdout.flush()
            execute.do(["git", "clone", "-q", server+gitPackage, clonePath], cfg)

def getServerInfo(cfg, pDict, info):
    # todo:
    #    - parse type git / url / etc.
    setupCfg(cfg)
    if len(pDict) == 1:
        package, pInfo = pDict.items()[0]
        for key,server in cfg["server"].items():
            if key in pInfo:
                info["server"] = server
                info["gitPackage"] = pInfo[key]
                info["package"] = package
                return True
    haveKey = False
    haveServer = False
    for key, value in pDict.items():
        if not value:
            info["package"] = key
            if haveServer:
                return
            haveKey = True
        if key in cfg["server"]:
            info["server"] = cfg["server"][key]
            info["gitPackage"] = value
            if haveKey:
                return True
            haveServer = True
    info.clear()
    return False

def getPackageInfoHelper(cfg, package, base, info):
    matches = {}
    with open(cfg["devDir"]+"/autoproj/remotes/"+cfg["packages"][base]+"/source.yml") as f:
        source = yaml.load(f)
        if "version_control" in source:
            for pDict in source["version_control"]:
                info2 = {}
                getServerInfo(cfg, pDict, info2)
                if "package" in info2:
                    r = re.compile(info2["package"])
                    m = r.match(base)
                    if m and m.group() == base:
                        i2 = dict(info2)
                        i2["base"] = package
                        i2["remote"] = cfg["packages"][base]
                        checkBaseName(package, i2)
                        if package in matches:
                            matches[package].append(i2)
                        else:
                            matches[package] = [i2]

    for key, value in matches.items():
        e = 0
        g = {}
        for l in value:
            if len(l["base"]) > e:
                g = l

        info.update(g)
        return True
    return False

def getPackageInfo(cfg, package, info):
    if package in cfg["ignorePackages"]:
        return
    if package in cfg["osdeps"]:
        return
    if package in cfg["overrides"]:
        return
    setupCfg(cfg)
    if package in cfg["packages"]:
        if getPackageInfoHelper(cfg, package, package, info):
            return True

    base = package
    while "/" in base:
        base = base[:base.rindex("/")]
        if base+"/.*" in cfg["packages"]:
            base = base + "/.*"
            #c.printNormal("found wildcard packages: "+package+" ("+base+")")
            return getPackageInfoHelper(cfg, package, base, info)
    return False

def getPackageInfoFromRemoteFolder(cfg, package, folder, info):
    with open(folder+"/source.yml") as f:
        source = yaml.load(f)
    if "version_control" in source:
        for pDict in source["version_control"]:
            info2 = {}
            if getServerInfo(cfg, pDict, info2):
                info.append(info2)
    # todo: add parsing of libs.autobuild (which is a ruby script)
    matches = {}
    with open(folder+"/libs.autobuild") as f:
        info3 = []
        for line in f:
            if "_package" in line:
                l = line.split("_package")[1]
                arrLine = None
                if '"' in l:
                    arrLine = l.split('"')
                elif "'" in l:
                    arrLine = l.split("'")
                if arrLine:
                    if "#" not in arrLine[0]:
                        p = arrLine[1]
                        for i in info:
                            r = re.compile(i["package"])
                            m = r.match(p)
                            if m and m.group() == p:
                                i2 = dict(i)
                                i2["base"] = i2["package"]
                                i2["package"] = p
                                checkBaseName(p, i2)
                                if p in matches:
                                    matches[p].append(i2)
                                else:
                                    matches[p] = [i2]
    for key, value in matches.items():
        e = 0
        g = {}
        for l in value:
            if len(l["base"]) > e:
                g = l

        info.append(g)
        #print g["package"] + ": " + g["base"]
    return True

def fetchPackage(cfg, package, layout_packages):
    print "Check: " + package + " ... " + c.END,
    sys.stdout.flush()
    setupCfg(cfg)
    if package in cfg["ignorePackages"]:
        c.printWarning("done")
        return True
    if package in cfg["osdeps"]:
        if cfg["update"]:
            if len(cfg["osdeps"][package]) > 1:
                cfg["osdeps"][package][0](cfg, cfg["osdeps"][package][1])
            else:
                cfg["osdeps"][package][0](cfg, package)
            c.printWarning("done")
        return True
    if package in cfg["overrides"] and "fetch" in cfg["overrides"][package]:
        le = len(cfg["errors"])
        if cfg["update"]:
            cfg["overrides"][package]["fetch"](cfg)
        else:
            cfg["overrides"][package]["check"](cfg)
        if len(cfg["errors"]) == le:
            layout_packages.append(package)
            c.printWarning("done")
            return True
        else:
            cfg["errors"].append("missing: "+package)
            c.printError("error")
            return False

    path = cfg["devDir"]+"/autoproj/remotes/"

    if package in cfg["packages"] and package == cfg["packages"][package]:
        info = []
        print "\n ",
        if getPackageInfoFromRemoteFolder(cfg, package, path+package, info):
            error = False
            for i in info:
                le = len(cfg["errors"])
                if "$" not in i["gitPackage"]:
                    if cfg["update"]:
                        clonePackage(cfg, i["package"], i["server"],
                                     i["gitPackage"]);
                    if "*" not in i["package"]:
                        layout_packages.append(i["package"])
                if cfg["update"]:
                    if len(cfg["errors"]) <= le:
                        c.printWarning("done")
                    else:
                        c.printError("error")
            if error:
                if not cfg["update"]:
                    c.printError("error")
                return False
            else:
                if not cfg["update"]:
                    c.printWarning("done")
                return True
    else:
        info = {}
        if getPackageInfo(cfg, package, info):
            le = len(cfg["errors"])
            if cfg["update"]:
                if "basename" in info:
                    clonePackage(cfg, package, info["server"], info["gitPackage"])
                else:
                    clonePackage(cfg, info["package"], info["server"], info["gitPackage"])
            layout_packages.append(package)
            if len(cfg["errors"]) <= le:
                c.printWarning("done")
                return True
            else:
                c.printError("error")
                return False
    cfg["errors"].append("fetch: "+package)
    c.printError("error")
    return False

def fetchPackages(cfg, layout_packages):
    setupCfg(cfg)
    updated = []
    with open(cfg["devDir"]+"/autoproj/manifest") as f:
        manifest = yaml.load(f)
    for layout in manifest["layout"]:
        fetchPackage(cfg, layout, layout_packages)

# todo: add error handling
def clonePackageSet(cfg, package, server, path, cloned, remotes, deps):
    for key, value in package.items():
        if value not in cloned:
            # clone in tmp folder
            c.printNormal("  Fetching: "+value)
            out, err, r = execute.do(["git", "clone", server[key]+value.strip()+".git", path+"tmp"])
            if not os.path.isdir(path+"tmp/.git"):
                c.printNormal(out);
                c.printError(err);
                cfg["errors"].append("clone: "+value)
            # get the name of the remote
            with open(path+"tmp/source.yml") as f:
                info = yaml.load(f)
            os.system("rm -rf "+path+"remotes/"+info["name"])
            os.system("mv "+ path+"tmp "+path+"remotes/"+info["name"]);
            if "imports" in info and info["imports"]:
                for i in info["imports"]:
                    if i not in deps and i not in cloned:
                        deps.append(i)
            # store the info which package sets we have cloned already
            cloned.append(value)
            remotes.append(info["name"])

def updatePackageSets(cfg):
    # the server configuration are handled in the init.rb for autoproj
    setupCfg(cfg)
    path = cfg["devDir"]+"/autoproj/";
    os.system("mkdir -p "+path+"remotes")
    cloned = []
    remotes = []
    deps = []
    if os.path.isfile(path+"cloned.yml"):
        with open(path+"cloned.yml") as f:
            l = yaml.load(f)
            cloned = l["list"]
    with open(path+"manifest") as f:
        manifest = yaml.load(f)
    for packageSet in manifest["package_sets"]:
        clonePackageSet(cfg, packageSet, cfg["server"], path, cloned, remotes, deps)

    # update remotes that are not actually cloned
    for d in os.listdir(path+"remotes"):
        if os.path.isdir(path+"remotes/"+d):
            if d not in remotes:
                remotes.append(d)
                if cfg["update"]:
                    c.printNormal("  Updating: "+d)
                    out, err, r = execute.do(["git", "-C", path+"remotes/"+d, "pull"])
                    if len(err) > 0:
                        c.printError(err)
                with open(path+"remotes/"+d+"/source.yml") as f:
                    info = yaml.load(f)
                if "imports" in info and info["imports"]:
                    for i in info["imports"]:
                        if i not in deps and i not in cloned:
                            deps.append(i)
    # now handle deps
    while len(deps) > 0:
        packageSet = deps.pop(0)
        clonePackageSet(cfg, packageSet, cfg["server"], path, cloned, remotes, deps)

    with open(path+"cloned.yml", "w") as f:
        yaml.dump({"list": cloned}, f)

    # last step: write all packages int a file to speed up pybob usage
    packages, wildcards = listPackages(cfg)
    pDict = {}
    with open(path+"packages.txt", "w") as f:
        for p in packages:
            if len(p[1]) > 0:
                f.write(p[1]+"\n")
                pDict[p[1]] = p[0]
            else:
                f.write(p[0]+"\n")
                pDict[p[0]] = p[0]
        for p in wildcards:
            if len(p[1]) > 0:
                pDict[p[1]] = p[0]
            else:
                pDict[p[0]] = p[0]
    with open(path+"packages.yml", "w") as f:
        yaml.dump(pDict, f)


def fetchBuildconf(cfg):
    if os.path.isdir(cfg["devDir"]+"/autoproj"):
        if cfg["update"]:
            c.printNormal("  Update buildconf.")
            out, err, r = execute.do(["git", "-C", cfg["devDir"]+"/autoproj", "pull"])
            if len(err) > 0:
                c.printError(err)
    else:
        address = cfg["buildconfAdress"]
        if len(address) == 0:
            c.printError("no address given")
            return
        branch = cfg["buildconfBranch"]

        c.printNormal("   Fetching \""+address+branch+"\" into "+cfg["devDir"]+"/autoproj")
        command = ["git", "clone", address, cfg["devDir"]+"/autoproj"]
        if len(branch) > 0:
            command.append("-b")
            command.append(branch)
        out, err, r = execute.do(command)
        #if len(err) > 0:
            #c.printError(err)
