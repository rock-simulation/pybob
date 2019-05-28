#! /usr/bin/env python
from __future__ import print_function
import os
import sys
import yaml
import colorconsole as c
import multiprocessing
import execute
import re

rockBranches = ["$ROCK_BRANCH", "$ROCK_FLAVOR"]

def setupCfg(cfg):
    # todo: handle this files differently
    path = cfg["pyScriptDir"]
    # load server information if not already done
    if not "server" in cfg:
        with open(path+"/server.yml") as f:
            cfg["server"] = yaml.load(f)

    # load the package information if not already done
    path = cfg["devDir"]+"/autoproj/bob"
    if not os.path.isdir(path):
        execute.makeDir(path)
    if not "packages" in cfg and os.path.isfile(path+"/packages.yml"):
        with open(path+"/packages.yml") as f:
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
                        key, value = list(items)[0]
                    else:
                        for k, v in items:
                            if not v:
                                key = k
                                break
                    if "*" not in key:
                        packages.append([d, key])
                    else:
                        wildcard_packages.append([d, key])
            files = getAutobuildFiles(path+"remotes/"+d)
            for i in files:
                with open(i) as f:
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

def getAutobuildFiles(path):
    files = []
    if os.path.isdir(path):
        for d in os.listdir(path):
            if os.path.isfile(path+"/"+d):
                if ".autobuild" in d:
                    files.append(path+"/"+d)
    return files

def checkBaseName(package, info):
    if "gitPackage" in info:
        if "$" in info["gitPackage"] and "*" not in package:
            info["basename"] = info["gitPackage"]
            info["gitPackage"] = info["gitPackage"].replace("$PACKAGE_BASENAME",
                                                            package.split("/")[-1])

def clonePackage(cfg, package, server, gitPackage, branch):
    clonePath = package
    if package[-2:] == ".*":
        arrPackage = package.split("/")[:-1]
        p = gitPackage.split("/")[-1].split(".")[0]
        if arrPackage[-1] != p:
            arrPackage.append(p)
        clonePath = "/".join(arrPackage)
    if package in cfg["updated"]:
        return False
    else:
        cfg["updated"].append(package)
    clonePath = cfg["devDir"]+"/"+clonePath
    if os.path.isdir(clonePath):
        if cfg["update"]:
            print("Updating " + clonePath + " ... " + c.END, end="")
            # todo: check branch
            out, err, r = execute.do(["git", "-C", clonePath, "pull"], cfg)
            if r != 0:
                cfg["errors"].append("update: "+package)
                c.printError("\ncan't update \""+clonePath+"\":\n" + err)
            c.printWarning("done")
            return True
    else:
        if not cfg["fetch"]:
            c.printError(package+" is not cloned, call bob-fetch to update or clone the packages.")
            cfg["errors"].append("missing: "+package)
            c.printError("error")
            return True
        else:
            print("Fetching " + clonePath + " ... " + c.END, end="")
            sys.stdout.flush()
            cmd = ["git", "clone", "-o", "autobuild", "-q", server+gitPackage, clonePath]
            if branch:
                cmd += ["-b", branch]
            execute.do(cmd, cfg)
            # apply patch if we have one
            patch = cfg["pyScriptDir"] + "/patches/" + package.split("/")[-1] + ".patch"
            print("check for patches", end="")
            if os.path.exists(patch):
                cmd = ["patch", "-N", "-p0", "-d", clonePath, "-i", patch]
                print(" ".join(cmd))
                out, err, r = execute.do(cmd)
                print(out)
                print(err)
                print(r)
            c.printWarning("done")
            return True
    return False

def getServerInfo(cfg, pDict, info):
    # todo:
    #    - parse patches
    #    - impelment clean tag support
    # tag can be used as branches with git clone if no branch with
    # the same name exists
    setupCfg(cfg)
    if len(pDict) == 1:
        package, pInfo = list(pDict.items())[0]
        info["package"] = package
        haveServer = False
        if "type" in pInfo:
            if pInfo["type"] == "git" and "url" in pInfo:
                haveServer = True
                info["server"] = pInfo["url"]
                info["gitPackage"] = ""
        if not haveServer:
            for key,server in cfg["server"].items():
                if key in pInfo:
                    info["server"] = server
                    info["gitPackage"] = pInfo[key]
        if "branch" in pInfo:
            if pInfo["branch"] in rockBranches:
                info["branch"] = cfg["rockFlavor"]
            else:
                info["branch"] = pInfo["branch"]
        if "tag" in pInfo:
            info["branch"] = pInfo["tag"]
        return True
    haveKey = False
    haveServer = False
    if "branch" in pDict:
        if pDict["branch"] in rockBranches:
            info["branch"] = cfg["rockFlavor"]
        else:
            info["branch"] = pDict["branch"]
    if "tag" in pDict:
        info["branch"] = pDict["tag"]

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

    if "type" in pDict:
        if pDict["type"] == "git" and "url" in pDict:
            info["server"] = pDict["url"]
            info["gitPackage"] = ""
            return True
    #info.clear()
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
                        if "gitPackage" in i2:
                            if "basename" in matches:
                                del matches["basename"]
                        checkBaseName(package, i2)
                        matches.update(i2)
    if "package" in matches:
        info.update(matches)
        return True
    # for key, value in matches.items():
    #     e = 0
    #     g = {}
    #     for l in value:
    #         if len(l["base"]) > e:
    #             g = l
    #    info.update(g)
    #    return True
    return False

def getPackageInfo(cfg, package, info):
    if package in cfg["ignorePackages"] :#or "orogen" in package:
        return
    if package in cfg["osdeps"]:
        return
    #if package in cfg["overrides"]:
    #    return
    setupCfg(cfg)
    if package in cfg["packages"]:
        return getPackageInfoHelper(cfg, package, package, info)

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
    files = getAutobuildFiles(folder)
    for i in files:
        with open(i) as f:
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
                                    if i2["package"] in matches:
                                        matches[i2["package"]].update(i2)
                                    else:
                                        matches[i2["package"]] = i2
    for key, value in matches.items():
        info.append(value)

    return True

def fetchPackage(cfg, package, layout_packages):
    print("Check: " + package + " ... " + c.END, end="")
    sys.stdout.flush()
    setupCfg(cfg)
    if package in cfg["ignorePackages"]:# or "orogen" in package:
        c.printWarning("done")
        return True
    if package in cfg["osdeps"]:
        if cfg["fetch"] and cfg["no_os_deps"] == False:
            if len(cfg["osdeps"][package]) > 1:
                cfg["osdeps"][package][0](cfg, cfg["osdeps"][package][1])
            else:
                cfg["osdeps"][package][0](cfg, package)
            c.printWarning("done")
        return True
    if package in cfg["overrides"] and "fetch" in cfg["overrides"][package]:
        le = len(cfg["errors"])
        if cfg["fetch"]:
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

    matches = []
    for key, value in cfg["packages"].items():
        if package in key and key not in layout_packages:
            matches.append(key)

    if package not in cfg["packages"]:
        result = True
        for match in matches:
            if not fetchPackage(cfg, match, layout_packages):
                result = False
        return result
    elif package == cfg["packages"][package]:
        info = []
        print("\n ", end="")
        if getPackageInfoFromRemoteFolder(cfg, package, path+package, info):
            le = len(cfg["errors"])
            endM = True
            for i in info:
                if "$" not in i["gitPackage"]:
                    if "*" not in i["package"]:
                        fetchPackage(cfg, i["package"], layout_packages)
            if len(cfg["errors"]) > le:
                if endM:
                    c.printError("error")
                return False
            if endM:
                c.printWarning("done")
            return True
    else:
        info = {}
        if getPackageInfo(cfg, package, info):
            endM = True
            le = len(cfg["errors"])
            branch = None
            if not "server" in info:
                cfg["errors"].append("fetch: "+package)
                return
            server = info["server"]
            server2 = info["gitPackage"]

            if "branch" in info:
                branch = info["branch"]
            if package in cfg["overrides"]:
                value = cfg["overrides"][package]
                if "branch" in value:
                    branch = value["branch"]
                if "url" in value:
                    server = value["url"]
                    server2 = ""
            else:
                for key, value in cfg["overrides"].items():
                    r = re.compile(key)
                    m = r.match(package)
                    if m and m.group() == package:
                        if "branch" in value:
                            branch = value["branch"]
                        if "url" in value:
                            server = value["url"]
                            server2 = ""

            if "basename" in info:
                if clonePackage(cfg, package, server, server2, branch):
                    endM = False
            else:
                if "server" in info:
                    if clonePackage(cfg, info["package"], server, server2, branch):
                        endM = False
            layout_packages.append(package)
            if len(cfg["errors"]) > le:
                if endM:
                    c.printError("error")
                return False
            if endM:
                c.printWarning("done")
            return True

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
def clonePackageSet(cfg, git, realPath, path, cloned, deps):
    # clone in tmp folder
    c.printNormal("  Fetching: "+git)
    out, err, r = execute.do(["git", "clone", "-o", "autobuild", git, realPath])
    if not os.path.isdir(realPath+"/.git"):
        c.printNormal(str(out));
        c.printError(str(err));
        cfg["errors"].append("clone: "+git)
        return
    # get the name of the remote
    with open(realPath+"/source.yml") as f:
        info = yaml.load(f)
    #os.system("rm -rf "+path+"remotes/"+info["name"])
    os.system("ln -s "+ realPath + " " + path+"remotes/"+info["name"]);
    if "imports" in info and info["imports"]:
        for i in info["imports"]:
            key, value = list(i.items())[0]
            realPath = cfg["devDir"]+"/.autoproj/remotes/"+key+"__"+ value.strip().replace("/", "_").replace("-", "_") + "_git"
            if i not in deps and not os.path.isdir(realPath):
                deps.append(i)
    # store the info which package sets we have cloned already
    cloned.append(info["name"])

def updatePackageSets(cfg):
    # the server configuration are handled in the init.rb for autoproj
    setupCfg(cfg)
    path = cfg["devDir"]+"/autoproj/";
    execute.makeDir(path+"remotes")
    execute.makeDir(cfg["devDir"]+"/.autoproj/remotes")
    cloned = []
    deps = []
    with open(path+"manifest") as f:
        manifest = yaml.load(f)
    for packageSet in manifest["package_sets"]:
        key, value = list(packageSet.items())[0]
        realPath = cfg["devDir"]+"/.autoproj/remotes/"+key+"__"+ value.strip().replace("/", "_").replace("-", "_") + "_git"
        if not os.path.isdir(realPath):
            if key == "url":
                clonePackageSet(cfg, value.strip(), realPath, path, cloned, deps)
            else:
                clonePackageSet(cfg, cfg["server"][key]+value.strip()+".git", realPath, path, cloned, deps)

    # update remotes that are not actually cloned
    for d in os.listdir(path+"remotes"):
        if os.path.isdir(path+"remotes/"+d):
            if d not in cloned:
                if cfg["update"]:
                    c.printNormal("  Updating: "+d)
                    out, err, r = execute.do(["git", "-C", path+"remotes/"+d, "pull"])
                    if r !=  0:
                        cfg["errors"].append("update: "+d)
                        c.printError("\ncan't update package set \""+d+"\":\n"+err)
                if d not in cloned:
                    with open(path+"remotes/"+d+"/source.yml") as f:
                        info = yaml.load(f)
                    if "imports" in info and info["imports"]:
                        for i in info["imports"]:
                            key, value = list(i.items())[0]
                            realPath = cfg["devDir"] + "/.autoproj/remotes/" + key + "__" + value.strip().replace("/", "_").replace("-", "_") + "_git"
                            if i not in deps and not os.path.isdir(realPath):
                                deps.append(i)
    # now handle deps
    while len(deps) > 0:
        packageSet = deps.pop(0)
        key, value = list(packageSet.items())[0]
        realPath = cfg["devDir"]+"/.autoproj/remotes/"+key+"__"+ value.strip().replace("/", "_").replace("-", "_") + "_git"
        clonePackageSet(cfg, cfg["server"][key]+value.strip()+".git", realPath, path, cloned, deps)

    # last step: write all packages int a file to speed up pybob usage
    packages, wildcards = listPackages(cfg)
    pDict = {}
    with open(path + "/bob/packages.txt", "wb") as f:
        for p in packages:
            if len(p[1]) > 0:
                if sys.version_info.major <= 2:
                    f.write(p[1] + "\n")
                else:
                    f.write(bytes(p[1] + "\n", "utf-8"))
                pDict[p[1]] = p[0]
            else:
                if sys.version_info.major <= 2:
                    f.write(p[0] + "\n")
                else:
                    f.write(bytes(p[0] + "\n", "utf-8"))
                pDict[p[0]] = p[0]
        for p in wildcards:
            if len(p[1]) > 0:
                pDict[p[1]] = p[0]
            else:
                pDict[p[0]] = p[0]
    with open(path+"/bob/packages.yml", "w") as f:
        yaml.dump(pDict, f)


def fetchBuildconf(cfg):
    if os.path.isdir(cfg["devDir"]+"/autoproj"):
        if cfg["update"]:
            c.printNormal("  Update buildconf.")
            out, err, r = execute.do(["git", "-C", cfg["devDir"]+"/autoproj", "pull"])
            if r != 0:
                cfg["errors"].append("update: buildconf")
                c.printError("\ncan't update buildconf:\n" + str(err))
    else:
        address = cfg["buildconfAddress"]
        if len(address) == 0:
            c.printError("no address given")
            return
        branch = cfg["buildconfBranch"]

        c.printNormal("   Fetching \""+address+branch+"\" into "+cfg["devDir"]+"/autoproj")
        command = ["git", "clone", "-o", "autobuild", address, cfg["devDir"]+"/autoproj"]
        if len(branch) > 0:
            command.append("-b")
            command.append(branch)
        execute.do(command)
