#! /usr/bin/env python

import os
import sys
from platform import system
import colorconsole as c
import subprocess
import execute

def source(sourceFile):
    newenv = {}
    cmd = ["bash", "print_env.sh", sourceFile, "&>", "/dev/null;", "env"]
    cmdString = " ".join(cmd)
    p = subprocess.Popen(cmdString, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    for line in out.split("\n"):
        try:
            k,v = line.strip().split('=',1)
        except:
            continue  # bad line format, skip it
        newenv[k] = v
    os.environ.update(newenv)

def setupEnv(cfg, update=False):
    global os
    prefix = cfg["devDir"] + "/install"
    if system() == "Windows":
        if prefix[1] == ':':
            prefix = prefix.replace(prefix[:2], "/"+prefix[0])
    prefix_bin = prefix + "/bin"
    prefix_lib = prefix + "/lib"
    prefix_pkg = prefix_lib + "/pkgconfig"
    pythonpath = prefix_lib + "/python%d.%d/site-packages" % (sys.version_info.major, sys.version_info.minor)
    platform = system()
    if platform == "Windows":
        # todo: make this more generic
        pythonpath = "/mingw64/lib/python2.7:/mingw64/lib/python2.7/plat-win32:/mingw64/lib/python2.7/lib-tk:/mingw64/lib/python2.7/lib-dynload:/mingw64/lib/python2.7/site-packages:"+pythonpath
    elif platform == "Linux":
        prefix_lib += ":" + prefix + "/lib/x86_64-linux-gnu"
        prefix_pkg += ":" + prefix + "/lib/x86_64-linux-gnu/pkgconfig"
    prefix_config = prefix + "/configuration"

    # create env.sh
    p = subprocess.Popen("which cmake_debug", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    cmakeDebugPath = out.strip()
    if len(cmakeDebugPath) > 0:
        # check if path is correct
        expectPath = cfg["devDir"]+"/install/bin/cmake_debug"
        if platform == "Windows":
            c.printWarning("cmake_debug path check is not working on Windows currently (please always ensure that you only sourced the env.sh in your current dev folder!")
        else :
            if cmakeDebugPath != expectPath:
                c.printError('"cmake_debug" found in wrong folder.')
                c.printError('Found: '+cmakeDebugPath)
                c.printError('Expected: '+expectPath)
                c.printError('Maybe you already sourced an "env.sh" from a different "dev" folder?')
                return
        if not update:
            return

    if not update:
        if os.path.isfile(cfg["devDir"]+"/env.sh"):
            source(cfg["devDir"]+"/env.sh")

    p = subprocess.Popen("which autoproj", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    aPath = out.strip()
    if len(aPath) > 0:
        with open(cfg["devDir"]+"/bobenv.sh", "w") as f:
            f.write("#! /bin/sh\n")
            f.write(". env.sh\n")
            f.write('export MARS_SCRIPT_DIR="'+cfg["pyScriptDir"]+'"\n')
            f.write("alias bob='${MARS_SCRIPT_DIR}/pybob.py'\n")
            f.write("alias bob-bootstrap='${MARS_SCRIPT_DIR}/pybob.py bootstrap'\n")
            f.write("alias bob-install='${MARS_SCRIPT_DIR}/pybob.py install'\n")
            f.write("alias bob-rebuild='${MARS_SCRIPT_DIR}/pybob.py rebuild'\n")
            f.write("alias bob-build='${MARS_SCRIPT_DIR}/pybob.py'\n")
            f.write("alias bob-diff='${MARS_SCRIPT_DIR}/pybob.py diff'\n")
            f.write("alias bob-list='${MARS_SCRIPT_DIR}/pybob.py list'\n")
            f.write("alias bob-fetch='${MARS_SCRIPT_DIR}/pybob.py fetch'\n")
            f.write("alias bob-show-log='${MARS_SCRIPT_DIR}/pybob.py show-log'\n")
            f.write(". ${MARS_SCRIPT_DIR}/auto_complete.sh\n")
    else:
        with open(cfg["devDir"]+"/env.sh", "w") as f:
            f.write("#! /bin/sh\n")
            f.write('export AUTOPROJ_CURRENT_ROOT="'+cfg["devDir"]+'"\n')
            f.write('export MARS_SCRIPT_DIR="'+cfg["pyScriptDir"]+'"\n')

            f.write('export PATH="$PATH:'+prefix_bin+'"\n')
            if platform == "Darwin":
                f.write('export DYLD_LIBRARY_PATH="'+prefix_lib+':$DYLD_LIBRARY_PATH"\n')
            elif platform == "Linux":
                f.write('export LD_LIBRARY_PATH="'+prefix_lib+':$LD_LIBRARY_PATH"\n')
            else:
                f.write('export PATH="'+prefix_lib+':$PATH"\n')
            f.write('export ROCK_CONFIGURATION_PATH="'+prefix_config+'"\n')
            f.write('export PYTHONPATH="' + pythonpath + ':$PYTHONPATH"\n')

            # todo: handle python path
            f.write('if [ x${PKG_CONFIG_PATH} = "x" ]; then\n')
            f.write('  export PKG_CONFIG_PATH="'+prefix_pkg+'"\n')
            f.write('else\n')
            f.write('  export PKG_CONFIG_PATH="'+prefix_pkg+':$PKG_CONFIG_PATH"\n')
            f.write('fi\n')
            f.write("alias bob='${MARS_SCRIPT_DIR}/pybob.py'\n")
            f.write("alias bob-bootstrap='${MARS_SCRIPT_DIR}/pybob.py bootstrap'\n")
            f.write("alias bob-install='${MARS_SCRIPT_DIR}/pybob.py install'\n")
            f.write("alias bob-rebuild='${MARS_SCRIPT_DIR}/pybob.py rebuild'\n")
            f.write("alias bob-build='${MARS_SCRIPT_DIR}/pybob.py'\n")
            f.write("alias bob-diff='${MARS_SCRIPT_DIR}/pybob.py diff'\n")
            f.write("alias bob-list='${MARS_SCRIPT_DIR}/pybob.py list'\n")
            f.write("alias bob-fetch='${MARS_SCRIPT_DIR}/pybob.py fetch'\n")
            f.write("alias bob-show-log='${MARS_SCRIPT_DIR}/pybob.py show-log'\n")
            f.write(". ${MARS_SCRIPT_DIR}/auto_complete.sh\n")

    execute.makeDir(cfg["devDir"]+"/install/bin")
    with open(cfg["devDir"]+"/install/bin/cmake_debug", "w") as f:
        f.write("#!/bin/bash\n")
        options = "-DROCK_TEST_ENABLED=OFF"
        if not "autoprojEnv" in cfg or not cfg["autoprojEnv"]:
            options += " -DBINDINGS_RUBY=OFF "
        if platform == "Windows":
            f.write("cmake .. "+options+"-DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install -DCMAKE_BUILD_TYPE=DEBUG  -G \"MSYS Makefiles\" $@\n")
        else:
            f.write("cmake .. "+options+"-DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install -DCMAKE_BUILD_TYPE=DEBUG $@\n")
    with open(cfg["devDir"]+"/install/bin/cmake_release", "w") as f:
        f.write("#!/bin/bash\n")
        if platform == "Windows":
            f.write("cmake .. "+options+"-DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install -DCMAKE_BUILD_TYPE=RELEASE  -G \"MSYS Makefiles\" $@\n")
        else:
            f.write("cmake .. "+options+"-DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install -DCMAKE_BUILD_TYPE=RELEASE $@\n")

    cmd = ["chmod", "+x", cfg["devDir"]+"/install/bin/cmake_debug"]
    execute.simpleExecute(cmd)

    cmd = ["chmod", "+x", cfg["devDir"]+"/install/bin/cmake_release"]
    execute.simpleExecute(cmd)
    source(cfg["devDir"]+"/env.sh")
