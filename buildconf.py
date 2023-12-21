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
            cfg["server"] = yaml.safe_load(f)

    # load the package information if not already done
    path = cfg["devDir"]+"/autoproj/bob"
    if not os.path.isdir(path):
        execute.makeDir(path)
    if not "packages" in cfg and os.path.isfile(path+"/packages.yml"):
        with open(path+"/packages.yml") as f:
            cfg["packages"] = yaml.safe_load(f)

def listPackages(cfg):
    path = cfg["devDir"]+"/autoproj/";
    packages = []
    wildcard_packages = []
    folders = []
    with open(path+"manifest") as f:
        manifest = yaml.safe_load(f)
    for packageSet in manifest["package_sets"]:
        if not isinstance(packageSet, dict):
            p = os.path.join(path, packageSet)
            if os.path.exists(p):
                folders.append([p, packageSet])

    for d in os.listdir(path+"remotes"):
        if os.path.isdir(path+"remotes/"+d):
            packages.append([d, ""])
            with open(path+"remotes/"+d+"/source.yml") as f:
                source = yaml.safe_load(f)
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
                        if "metapackage" in line:
                            l = line.split()
                            if len(l) == 3:
                                l1 = l[1].strip().replace('"', "").replace("'", "").replace(',', "")
                                l2 = l[2].strip().replace('"', "").replace("'", "").replace(',', "")
                                packages.append([d, l1, l2])

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
            info["gitPackage"] = info["gitPackage"].replace("$PACKAGE",
                                                            package.split("/")[-1])

def clonePackage(cfg, package, server, gitPackage, branch, commit, recursive=False):
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
            out, err, r = execute.do(["git", "-C", clonePath, "branch"], cfg)
            if r != 0:
                cfg["errors"].append("update: "+package)
                c.printError("\ncan't get branch of git repo \""+clonePath+"\":\n" + execute.decode(err))
            else:
                branches = execute.decode(out).splitlines()
                current_branch = None
                for b in branches:
                    if b[0] == "*":
                        current_branch = b.split()[1].strip()
                if not branch:
                    out, err, r = execute.do(["git", "-C", clonePath, "remote", "show", "autobuild | sed -n '/HEAD branch/s/.*: //p'"], cfg)
                    if r != 0:
                        cfg["errors"].append("update: "+package)
                        c.printError("\ncan't get default branch of git repo \""+clonePath+"\":\n" + execute.decode(err))
                    else:
                        branch = execute.decode(out).strip()
                print(branch + " [" + current_branch + "] " + c.END, end="")
                if branch and branch != current_branch:
                    args = ["-t", "autobuild/"+branch]
                    for b in branches:
                        if branch == b.strip():
                            args = [branch]
                            break
                    out, err, r = execute.do(["git", "-C", clonePath, "checkout"]+args, cfg)
                    if r != 0:
                        cfg["errors"].append("update: "+package)
                        c.printError("\ncan't checkout given branch \""+clonePath+"\":\n" + execute.decode(err))
            out = None
            err = None
            r = None
            if commit != None:
                out, err, r = execute.do(["git", "-C", clonePath, "checkout", commit], cfg)
            else:
                out, err, r = execute.do(["git", "-C", clonePath, "pull"], cfg)
            if r != 0:
                cfg["errors"].append("update: "+package)
                c.printError("\ncan't update \""+clonePath+"\":\n" + execute.decode(err))
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
            if server == "archive":
                archivePath = "/".join(clonePath.split("/")[:-1])
                out, err, r = execute.do(["wget", "-P", archivePath, gitPackage])
                if r != 0:
                    cfg["errors"].append("wget: "+package)
                    c.printError("\ncan't fetch \""+clonePath+"\":\n" + execute.decode(err))
                    return True
                sourceFile = os.path.join(archivePath, gitPackage.split("/")[-1])
                arrFileName = gitPackage.split("/")[-1].split(".")
                ending = arrFileName[-1]
                folderName = ".".join(arrFileName[:-1])
                cmd = []
                if ending == "tar":
                    cmd = ["tar", "-xf", sourceFile, "-C", archivePath]
                elif ending == "gz":
                    cmd = ["tar", "-xzf", sourceFile, "-C", archivePath]
                    if arrFileName[-2] == "tar":
                        folderName = ".".join(arrFileName[:-2])
                elif ending == "tgz":
                    cmd = ["tar", "-xzf", sourceFile, "-C", archivePath]
                elif ending == "bz2":
                    cmd = ["tar", "-xjf", sourceFile, "-C", archivePath]
                    if arrFileName[-2] == "tar":
                        folderName = ".".join(arrFileName[:-2])
                elif ending == "zip":
                    cmd = ["unzip", sourceFile, "-d", archivePath]
                out, err, r = execute.do(cmd)
                if r != 0:
                    cfg["errors"].append("wget: "+package)
                    c.printError("\ncan't fetch (unpack) \""+clonePath+"\":\n" + execute.decode(err))
                    c.printError("\ncmd (unpack): \""+" ".join(cmd))
                    return True
                # rename folder
                cmd = ["mv", os.path.join(archivePath, folderName), clonePath]
                out, err, r = execute.do(cmd)
                if r != 0:
                    cfg["errors"].append("rename folder for: "+package)
                    c.printError("\ncan't rename (mv) \""+clonePath+"\":\n" + execute.decode(err))
                    c.printError("\ncmd (rename): \""+" ".join(cmd))
                    return True
            else:
                cmd = ["git", "clone", "-o", "autobuild", "-q", server+gitPackage, clonePath]
                if branch:
                    cmd += ["-b", branch]
                if recursive:
                    cmd += ["--recursive"]
                print(" ".join(cmd))
                out, err, r = execute.do(cmd, cfg)
                if r != 0:
                    cfg["errors"].append("clone: "+package)
                    c.printError("\ncan't clone \""+clonePath+"\":\n" + execute.decode(err))
                    return True
                if commit != None:
                    out, err, r = execute.do(["git", "-C", clonePath, "checkout", commit], cfg)
                    if r != 0:
                        cfg["errors"].append("git checkout: "+package+" "+commit)
                        c.printError("\ncan't checkout \""+clonePath+"\":\n" + execute.decode(err))
                        return True


            # apply patch if we have one
            patch = cfg["pyScriptDir"] + "/patches/" + package.split("/")[-1] + ".patch"
            print("check for patches", end="")
            if os.path.exists(patch):
                cmd = ["patch", "-N", "-p0", "-t", "-d", clonePath, "-i", patch]
                print(" ".join(cmd))
                out, err, r = execute.do(cmd)
                print(execute.decode(out))
                print(execute.decode(err))
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
            if pInfo["type"] == "archive" and "url" in pInfo:
                info["archive"] = pInfo["url"]
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
        if "commit" in pInfo:
            info["commit"] = pInfo["commit"]
        if "with_submodules" in pInfo:
            info["with_submodules"] = pInfo["with_submodules"]
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
    if "commit" in pDict:
        info["commit"] = pDict["commit"]
    if "with_submodules" in pDict:
        info["with_submodules"] = pDict["with_submodules"]

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
    path = cfg["devDir"]+"/autoproj/remotes/"+cfg["packages"][base][0]
    if not os.path.exists(path):
        path = cfg["devDir"]+"/autoproj/"+cfg["packages"][base][0]
    if not os.path.exists(path):
        cfg["errors"].append("Cannot find path for: "+cfg["packages"][base][0])
        c.printError("ERROR: Cannot find path for: "+cfg["packages"][base][0])
        return False
    with open(os.path.join(path, "source.yml")) as f:
        source = yaml.safe_load(f)
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
                        i2["remote"] = cfg["packages"][base][0]
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
    if package in cfg["ignorePackages"] or (not cfg["orogen"] and "orogen" in package):
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
        source = yaml.safe_load(f)
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
    if package in cfg["ignorePackages"] or (not cfg["orogen"] and "orogen" in package):
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

    if package in cfg["osdeps"]:
        if cfg["fetch"] and cfg["no_os_deps"] == False:
            if len(cfg["osdeps"][package]) > 1:
                cfg["osdeps"][package][0](cfg, cfg["osdeps"][package][1])
            else:
                cfg["osdeps"][package][0](cfg, package)
            c.printWarning("done")
        return True

    #if package in cfg["overrides"] and cfg["overrides"][package] == None:
    #    print(cfg["overrides"])
    #print(package)

    path = cfg["devDir"]+"/autoproj/remotes/"

    matches = []
    if cfg["name_matching"] :
        for key, value in cfg["packages"].items():
            if package in key and key not in layout_packages:
                matches.append(key)
    else:
        for key, value in cfg["packages"].items():
            if package == key and key not in layout_packages:
                matches.append(key)

    if package not in cfg["packages"]:
        result = True
        for match in matches:
            if not fetchPackage(cfg, match, layout_packages):
                result = False
        return result
    elif package == cfg["packages"][package][0]:
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
        # override package if it is a metapackage
        if len(cfg["packages"][package]) == 2:
            package = cfg["packages"][package][1]
        if getPackageInfo(cfg, package, info):
            endM = True
            le = len(cfg["errors"])
            branch = None
            commit = None
            server = None
            server2 = None
            if "archive" in info:
                server = "archive"
                server2 = info["archive"]
            elif not "server" in info:
                cfg["errors"].append("fetch: "+package)
                return
            else:
                server = info["server"]
                server2 = info["gitPackage"]

            if "branch" in info:
                branch = info["branch"]
            if "commit" in info:
                commit = info["commit"]
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
                if "with_submodules" in info and info["with_submodules"]:
                    if clonePackage(cfg, package, server, server2, branch, commit,  True):
                        endM = False
                else:
                    if clonePackage(cfg, package, server, server2, branch, commit):
                        endM = False

            else:
                if "server" in info or "archive" in info:
                    if "with_submodules" in info and info["with_submodules"]:
                        if clonePackage(cfg, info["package"], server, server2, branch, commit, True):
                            endM = False
                    else:
                        if clonePackage(cfg, info["package"], server, server2, branch, commit):
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
        manifest = yaml.safe_load(f)
    for layout in manifest["layout"]:
        fetchPackage(cfg, layout, layout_packages)

# todo: add error handling
def clonePackageSet(cfg, git, realPath, path, cloned, deps, branch=None):
    # clone in tmp folder
    c.printNormal("  Fetching: "+git)
    cmd = ["git", "clone", "-o", "autobuild", git, realPath]
    if branch != None:
        cmd.append("-b")
        cmd.append(branch)
    out, err, r = execute.do(cmd)
    if not os.path.isdir(realPath+"/.git"):
        c.printNormal(execute.decode(out));
        c.printError(execute.decode(err));
        cfg["errors"].append("clone: "+git)
        return
    # get the name of the remote
    with open(realPath+"/source.yml") as f:
        info = yaml.safe_load(f)
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
        manifest = yaml.safe_load(f)
    for packageSet in manifest["package_sets"]:
        if isinstance(packageSet, dict):
            key, value = list(packageSet.items())[0]
            branch = None
            if isinstance(value, dict):
                if value["type"] != "git":
                    continue
                url = value["url"]
                key = "url"
                value = url
                if "branch" in value:
                    branch = value["branch"]
            if "branch" in packageSet:
                branch = packageSet["branch"]

            realPath = cfg["devDir"]+"/.autoproj/remotes/"+key+"__"+ value.strip().replace("/", "_").replace("-", "_") + "_git"
            if not os.path.isdir(realPath):
                if key == "url":
                    clonePackageSet(cfg, value.strip(), realPath, path, cloned, deps, branch)
                else:
                    clonePackageSet(cfg, cfg["server"][key]+value.strip()+".git", realPath, path, cloned, deps, branch)

    # update remotes that are not actually cloned
    for d in os.listdir(path+"remotes"):
        if os.path.isdir(path+"remotes/"+d):
            if d not in cloned:
                if cfg["update"]:
                    c.printNormal("  Updating: "+d)
                    out, err, r = execute.do(["git", "-C", path+"remotes/"+d, "pull"])
                    if r !=  0:
                        cfg["errors"].append("update: "+d)
                        c.printError("\ncan't update package set \""+d+"\":\n"+execute.decode(err))
                if d not in cloned:
                    with open(path+"remotes/"+d+"/source.yml") as f:
                        info = yaml.safe_load(f)
                    if "imports" in info and info["imports"]:
                        for i in info["imports"]:
                            key, value = list(i.items())[0]
                            realPath = cfg["devDir"] + "/.autoproj/remotes/" + key + "__" + value.strip().replace("/", "_").replace("-", "_") + "_git"
                            # todo: handle the update differently, maybe in clone
                            if i not in deps and not os.path.isdir(realPath):
                                deps.append(i)

    # handle local_package sets if avialable
    for packageSet in manifest["package_sets"]:
        if not isinstance(packageSet, dict):
            p = os.path.join(path, packageSet, "source.yml")
            if os.path.exists(p):
                with open(p) as f:
                    info = yaml.safe_load(f)
                    if "imports" in info and info["imports"]:
                        for i in info["imports"]:
                            key, value = list(i.items())[0]
                            realPath = cfg["devDir"] + "/.autoproj/remotes/" + key + "__" + value.strip().replace("/", "_").replace("-", "_") + "_git"
                            # todo: handle the update differently, maybe in clone
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
                if len(p) == 3:
                    pDict[p[1]] = [p[0], p[2]]
                else:
                    pDict[p[1]] = [p[0]]
            else:
                if sys.version_info.major <= 2:
                    f.write(p[0] + "\n")
                else:
                    f.write(bytes(p[0] + "\n", "utf-8"))
                pDict[p[0]] = [p[0]]
        for p in wildcards:
            if len(p[1]) > 0:
                pDict[p[1]] = [p[0]]
            else:
                pDict[p[0]] = [p[0]]
    with open(path+"/bob/packages.yml", "w") as f:
        yaml.dump(pDict, f)


def fetchBuildconf(cfg):
    if os.path.isdir(cfg["devDir"]+"/autoproj"):
        if cfg["update"]:
            c.printNormal("  Update buildconf.")
            out, err, r = execute.do(["git", "-C", cfg["devDir"]+"/autoproj", "pull"])
            if r != 0:
                cfg["errors"].append("update: buildconf")
                c.printError("\ncan't update buildconf:\n" + execute.decode(err))
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
