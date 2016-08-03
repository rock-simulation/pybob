#! /usr/bin/env python
import os
import yaml
import colorconsole as c
import multiprocessing

def getConfiguration(cfg):
    # check wether we have a config file
    path = "../"
    if "AUTOPROJ_CURRENT_ROOT" in os.environ:
        path = os.environ["AUTOPROJ_CURRENT_ROOT"]
    cfg["path"] = path
    if os.path.isfile(path+"/pybob/pybob.yml"):
        with open(path+"/pybob/pybob.yml") as f:
            cfg.update(yaml.load(f))
    else:
        # we assume this script is executed from one folder above
        scriptDir = os.getcwd()
        cfg["pyScriptDir"] = scriptDir
        arrDevDir = scriptDir.split("/")
        arrDevDir.pop()
        if arrDevDir[-1] == "bootstrap":
            arrDevDir.pop()
        devDir = "/".join(arrDevDir)

        # get the dev dir
        c.printBold("You must set a root directory where all repositories will be checked out and all packages will be installed")
        c.printBold("On Windows you should use the mingw path and not the windows path and avoid trailing slashes (e.g. /c/dev/mars-git)")
        in_ = raw_input("Enter root directory or nothing for [\""+devDir+"\"]: ")
        if len(in_) > 0:
            devDir = in_

        if devDir[-1] ==  "/":
            devDir.pop()

        cfg["devDir"] = devDir

        # get the numbers of cores to build
        print
        c.printBold("You can specify the number of CORES you want to use when compiling packages.")
        try:
            cfg["numCores"] = multiprocessing.cpu_count()
        except:
            cfg["numCores"] = 1

        in_ = raw_input("Enter number of CORES ["+str(cfg["numCores"])+"]): ")
        if len(in_) > 0:
            cfg["numCores"] = int(in_)

        # get the default build type
        cfg["defBuildType"] = "debug"
        pattern = ["debug", "release"]
        print
        buildType = raw_input("Enter default build type (debug|release) [debug]: ")
        if buildType in pattern:
            cfg["defBuildType"] = str(buildType)

        # get the default rock flavor
        cfg["rockFlavor"] = "master"
        pattern = ["stable", "master"]
        print
        flavor = raw_input("Enter default rock flavor (stable|master) [master]: ")
        if flavor in pattern:
            cfg["rockFlavor"] = str(flavor)

        print
        if not "buildconfAddress" in cfg:
            in_ = raw_input("Enter git address of buildconf to clone: ")
            if len(in_) > 0:
                cfg["buildconfAddress"] = in_
            print
        cfg["buildconfBranch"] = ""
        in_ = raw_input("Enter branch of buildconf [default]: ")
        if len(in_) > 0:
            cfg["buildconfBranch"] = in_

        c.printBold("The configuration is written to \""+path+"/pybob/pybob.yml\".\n")
        
        with open(path+"/pybob/pybob.yml", "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)
    return cfg
