#! /usr/bin/env python
from __future__ import print_function
import os
import yaml
import colorconsole as c
import multiprocessing
import sys
from platform import system


def raw_input_(s):
  print(s, end="")
  sys.stdout.flush()
  if sys.version_info[0] < 3:
    return raw_input()
  else:
    return input()

def getConfiguration(cfg):
    platform = system()
    # check wether we have a config file
    path = ".."
    if "AUTOPROJ_CURRENT_ROOT" in os.environ:
        path = os.environ["AUTOPROJ_CURRENT_ROOT"]
    if os.path.isfile(path+"/pybob/pybob.yml"):
        try:
            cfg["numCores"] = multiprocessing.cpu_count()
        except:
            cfg["numCores"] = 1
        with open(path+"/pybob/pybob.yml") as f:
            cfg.update(yaml.safe_load(f))
    else:
        # check if we have an autoproj environment
        if os.path.isfile(path+"/autoproj/config.yml"):
            acfg = {}
            with open(path+"/autoproj/config.yml") as f:
                acfg = yaml.safe_load(f)
            cfg["pyScriptDir"] = path+"/pybob"
            cfg["devDir"] = path
            cfg["numCores"] = multiprocessing.cpu_count()
            if(acfg["autoproj_use_prerelease"]):
                cfg["defBuildType"] = "release"
            else:
                cfg["defBuildType"] = "debug"
            cfg["rockFlavor"] = acfg["ROCK_FLAVOR"]
            cfg["autoprojEnv"] = True
        else:
            cfg["autoprojEnv"] = False
            # we assume this script is executed from one folder above
            scriptDir = os.getcwd()
            # convert cwd on windows if neseccary
            cfg["pyScriptDir"] = scriptDir
            arrDevDir = scriptDir.split("/")
            arrDevDir.pop()
            if arrDevDir[-1] == "bootstrap":
                arrDevDir.pop()
            devDir = "/".join(arrDevDir)

            # get the dev dir
            c.printBold("You must set a root directory where all repositories will be checked out and all packages will be installed")
            in_ = raw_input_("Enter root directory or nothing for [\""+devDir+"\"]: ")
            if len(in_) > 0:
                devDir = in_

            if devDir[-1] ==  "/":
                devDir.pop()

            cfg["devDir"] = devDir

            # get the numbers of cores to build
            print()
            c.printBold("You can specify the number of CORES you want to use when compiling packages.")
            try:
                cfg["numCores"] = multiprocessing.cpu_count()
            except:
                cfg["numCores"] = 1

            in_ = raw_input_("Enter number of CORES ["+str(cfg["numCores"])+"]): ")
            if len(in_) > 0:
                cfg["numCores"] = int(in_)

            # get the default build type
            cfg["defBuildType"] = "debug"
            pattern = ["debug", "release"]
            print()
            buildType = raw_input_("Enter default build type (debug|release) [debug]: ")
            if buildType in pattern:
                cfg["defBuildType"] = str(buildType)

            # get the default rock flavor
            cfg["rockFlavor"] = "master"
            pattern = ["stable", "master"]
            print()
            flavor = raw_input_("Enter default rock flavor (stable|master) [master]: ")
            if flavor in pattern:
                cfg["rockFlavor"] = str(flavor)

            print()
            if not "buildconfAddress" in cfg:
                in_ = raw_input_("Enter git address of buildconf to clone: ")
                if len(in_) > 0:
                    cfg["buildconfAddress"] = in_
                print()
            cfg["buildconfBranch"] = ""
            in_ = raw_input_("Enter branch of buildconf [default]: ")
            if len(in_) > 0:
                cfg["buildconfBranch"] = in_

            cfg["orogen"] = "no"
            pattern = ["yes", "no"]
            print()
            orogen = raw_input_("Enable orogen support? (yes|no) [no]: ")
            if orogen in pattern:
                if orogen == "yes" or orogen == "y" or orogen == "1":
                    cfg["orogen"] = True
                else:
                    cfg["orogen"] = False

            c.printBold("The configuration is written to \""+path+"/pybob/pybob.yml\".\n")

            with open(path+"/pybob/pybob.yml", "w") as f:
                yaml.dump(cfg, f, default_flow_style=False)
    cfg["path"] = path
    return cfg
