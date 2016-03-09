#! /usr/bin/env python

import os
import sys
from platform import system
import colorconsole as c
import subprocess

def source(sourceFile):
    newenv = {}
    print sourceFile
    p = subprocess.Popen(['. '+sourceFile+' &> /dev/null; env'], stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
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
    prefix_bin = prefix + "/bin"
    prefix_lib = prefix + "/lib"
    prefix_pkg = prefix_lib + "/pkgconfig"
    prefix_config = prefix + "/configuration"

    # create env.sh
    p = subprocess.Popen(['which cmake_debug'], stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    cmakeDebugPath = out.strip()
    if len(cmakeDebugPath) > 0:
        # check if path is correct
        if cmakeDebugPath != cfg["devDir"]+"/install/bin/cmake_debug":
            c.printError('"cmake_debug" found in wrong folder.')
            c.printError('Found: '+cmakeDebugPath)
            c.printError('Expected: '+cfg["devDir"]+'/install/bin/cmake_debug')
            c.printError('Maybe you already sourced an "env.sh" from a different "dev" folder?')
            return
        elif not update:
            return

    if not update:
        if os.path.isfile(cfg["devDir"]+"/env.sh"):
            source(cfg["devDir"]+"/env.sh")
            

    with open(cfg["devDir"]+"/env.sh", "w") as f:
        f.write("#! /bin/sh\n")
        f.write('export AUTOPROJ_CURRENT_ROOT="'+cfg["devDir"]+'"\n')
        f.write('export MARS_SCRIPT_DIR="'+cfg["pyScriptDir"]+'"\n')
        f.write('export PATH="$PATH:'+prefix_bin+'"\n')
        platform = system()
        if platform == "Darwin":
            f.write('export DYLD_LIBRARY_PATH="'+prefix_lib+':$DYLD_LIBRARY_PATH"\n')
        elif platform == "Linux":
            f.write('export LD_LIBRARY_PATH="'+prefix_lib+':$DYLD_LIBRARY_PATH"\n')
        else:
            f.write('export PATH="'+prefix_lib+':$PATH"\n')
        f.write('export ROCK_CONFIGURATION_PATH="'+prefix_config+'"\n')

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
        f.write(". ${MARS_SCRIPT_DIR}/auto_complete.sh\n")
    os.system("mkdir -p "+cfg["devDir"]+"/install/bin")
    with open(cfg["devDir"]+"/install/bin/cmake_debug", "w") as f:
        f.write("#!/bin/bash\n")
        if platform == "Windows":
            f.write("cmake .. -DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install -DCMAKE_BUILD_TYPE=DEBUG  -G \"MSYS Makefiles\" $@\n")
        else:
            f.write("cmake .. -DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install -DCMAKE_BUILD_TYPE=DEBUG $@\n")
    with open(cfg["devDir"]+"/install/bin/cmake_release", "w") as f:
        f.write("#!/bin/bash\n")
        if platform == "Windows":
            f.write("cmake .. -DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install -DCMAKE_BUILD_TYPE=RELEASE  -G \"MSYS Makefiles\" $@\n")
        else:
            f.write("cmake .. -DCMAKE_INSTALL_PREFIX="+cfg["devDir"]+"/install -DCMAKE_BUILD_TYPE=RELEASE $@\n")
    os.system("chmod +x "+cfg["devDir"]+"/install/bin/cmake_debug")
    os.system("chmod +x "+cfg["devDir"]+"/install/bin/cmake_release")
    source(cfg["devDir"]+"/env.sh")
