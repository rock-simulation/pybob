#! /usr/bin/env python

import os
import sys
from platform import system
import colorconsole as c
import subprocess
import execute
import utils

QT5_UBUNTU = False
UBUNTU_MAJOR = 20

if system() == "Linux":
    qt5_ubuntu_env_var = os.environ.get("QT5_UBUNTU")
    if qt5_ubuntu_env_var is None:
        try:
            import distro
        except ImportError:
            raise ImportError("please install the distro package: pip install distro\n"
                              "(or set QT5_UBUNTU to True or False prior to using pybob)")
        UBUNTU_MAJOR = int(distro.major_version(best=True))
        QT5_UBUNTU = distro.id() == "ubuntu" and UBUNTU_MAJOR >= 20
    else:
        QT5_UBUNTU = bool(qt5_ubuntu_env_var)


def source(sourceFile):
    newenv = {}
    cmd = ["echo", "'source", sourceFile, "&>", "/dev/null", ";", "env'", "|", "bash"]
    cmdString = " ".join(cmd)
    p = subprocess.Popen(cmdString, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    for line in out.split(b"\n"):
        try:
            k,v = line.strip().split('=',1)
        except:
            continue  # bad line format, skip it
        newenv[k] = v

    os.environ.update(newenv)

def setupEnv(cfg, update=False):
    global os
    prefix = cfg["devDir"] + "/install"
    platform = system()
    if platform == "Windows":
        if prefix[1] == ':':
            prefix = prefix.replace(prefix[:2], "/"+prefix[0])
    prefix_bin = prefix + "/bin"
    prefix_lib = prefix + "/lib"
    prefix_pkg = prefix_lib + "/pkgconfig"
    # if platform == "Darwin":
    #     prefix_pkg = "/opt/local/share/pkgconfig:/opt/local/lib/pkgconfig:"+prefix_pkg
    pythonver = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
    pythonpath = prefix_lib + "/python%d.%d/site-packages" % (sys.version_info.major, sys.version_info.minor)
    if platform == "Windows":
        # todo: make this more generic
        pythonpath = "/mingw64/lib/python"+pythonver+":/mingw64/lib/python"+pythonver+"/plat-win32:/mingw64/lib/python"+pythonver+"/lib-tk:/mingw64/lib/python"+pythonver+"/lib-dynload:/mingw64/lib/python"+pythonver+"/site-packages:"+pythonpath
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
            if cmakeDebugPath.decode("utf-8") != expectPath:
                c.printError('"cmake_debug" found in wrong folder.')
                c.printError('Found: ' + cmakeDebugPath.decode("utf-8"))
                c.printError('Expected: ' + expectPath)
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

    p = subprocess.Popen("pkg-config --variable pc_path pkg-config", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    pkg_config_pathes = out.strip()
    if len(pkg_config_pathes) > 0:
        prefix_pkg += ":"+pkg_config_pathes.decode("utf-8")

    if len(aPath) > 0:
        with open(cfg["devDir"]+"/bobenv.sh", "w") as f:
            f.write("#! /bin/bash\n")
            f.write(". env.sh\n")
            f.write('export MARS_SCRIPT_DIR="'+cfg["pyScriptDir"]+'"\n')
            _make_pybob_aliases(f)
    else:
        with open(cfg["devDir"]+"/env.sh", "w") as f:
            f.write("#! /bin/bash\n")
            f.write('export AUTOPROJ_CURRENT_ROOT="'+cfg["devDir"]+'"\n')
            f.write('if [ x${CMAKE_PREFIX_PATH} = "x" ]; then\n')
            f.write('  export CMAKE_PREFIX_PATH="'+cfg["devDir"]+'/install"\n')
            f.write('else\n')
            f.write('  export CMAKE_PREFIX_PATH="'+cfg["devDir"]+'/install:$CMAKE_PREFIX_PATH"\n')
            f.write('fi\n')
            f.write('export MARS_SCRIPT_DIR="'+cfg["pyScriptDir"]+'"\n')

            f.write('export PATH="$PATH:'+prefix_bin+'"\n')
            prefix_lib_orocos = os.path.join(prefix_lib, "orocos") + ":" + os.path.join(prefix_lib, "orocos/types")
            if platform == "Darwin":
                f.write('export DYLD_LIBRARY_PATH="'+prefix_lib+':'+prefix_lib_orocos+':$DYLD_LIBRARY_PATH"\n')
                f.write('export MYLD_LIBRARY_PATH="$DYLD_LIBRARY_PATH"\n')
                f.write('export USE_QT5=1\n')
            elif platform == "Linux":
                f.write('export LD_LIBRARY_PATH="'+prefix_lib+':'+prefix_lib_orocos+':$LD_LIBRARY_PATH"\n')
                if QT5_UBUNTU:
                    f.write('export USE_QT5=1\n')
            else:
                f.write('export PATH="'+prefix_lib+':'+prefix_lib_orocos+':$PATH"\n')
                f.write('export USE_QT5=1\n')
            f.write('export CXXFLAGS="-std=c++14"\n')
            f.write('export ROCK_CONFIGURATION_PATH="'+prefix_config+'"\n')
            f.write('export PYTHONPATH="' + pythonpath + ':$PYTHONPATH"\n')

            f.write('if [ x${PKG_CONFIG_PATH} = "x" ]; then\n')
            f.write('  export PKG_CONFIG_PATH="'+prefix_pkg+'"\n')
            f.write('else\n')
            f.write('  export PKG_CONFIG_PATH="'+prefix_pkg+':$PKG_CONFIG_PATH"\n')
            f.write('fi\n')

            if platform == "Darwin":
                major,minor = utils.get_ruby_verison()
                ruby_subpath = "/ruby"+major+"."+minor+"/"+major+"."+minor+".0"
                ruby_subpath2 = "/ruby/"+major+"."+minor+".0"
                ruby_archdir = utils.get_ruby_archdir()
                f.write('export RUBYLIB="'+prefix_lib+ruby_subpath+':'+prefix_lib+ruby_subpath2+':'+prefix_lib+ruby_subpath+'/'+ruby_archdir+':'+prefix_lib+ruby_subpath2+'/'+ruby_archdir+':'+prefix_lib+'/ruby/vendor_ruby"\n')
                f.write('export USE_QT5=1\n')
                f.write('export OROCOS_TARGET="macosx"\n')
                f.write('export TYPELIB_RUBY_PLUGIN_PATH="'+prefix+'/share/typelib/ruby"\n')

                f.write('export CXXFLAGS="-fPIC -std=c++14"\n')
                f.write('export TYPELIB_CASTXML_DEFAULT_OPTIONS="-I/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/include/c++/v1 -I/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include -I/opt/local/include"\n')
            elif platform == "Linux":
                major,minor = utils.get_ruby_verison()
                ruby_subpath = "ruby"+major+"."+minor+"/"+major+"."+minor+".0"
                ruby_subpath2 = "ruby/"+major+"."+minor+".0"
                ruby_archdir = utils.get_ruby_archdir()
                arr_prefix = prefix_lib.split(":")
                castxml_pathes = ["/usr/include/c++/13", "/usr/include/x86_64-linux-gnu/c++/13",
                                  "/usr/include/c++/13/backward", "/usr/local/include",
                                  "/usr/include/x86_64-linux-gnu", "/usr/include"]
                castxml_default_options = ""
                for p in castxml_pathes:
                    castxml_default_options += "-I"+p+" "
                f.write('export TYPELIB_CASTXML_DEFAULT_OPTIONS="'+castxml_default_options+'"\n')
                pathes = []
                print(ruby_subpath)
                print(ruby_subpath2)
                print(ruby_archdir)
                for p in arr_prefix:
                    print(p)
                    pathes.append(os.path.join(p, ruby_subpath))
                    pathes.append(os.path.join(p, ruby_subpath2))
                    pathes.append(os.path.join(p, "ruby", "vendor_ruby"))
                    pathes.append(os.path.join(p, ruby_archdir, ruby_subpath2))
                f.write('export RUBYLIB="'+":".join(pathes)+'"\n')
                f.write('export OROCOS_TARGET="gnulinux"\n')

            f.write('export TYPELIB_CXX_LOADER="castxml"\n')
            f.write('export TYPELIB_RUBY_PLUGIN_PATH="'+prefix+'/share/typelib/ruby"\n')
            f.write('export OROGEN_PLUGIN_PATH="'+prefix+'/share/orogen/plugins"\n')
            f.write('export OROGEN_MODEL_PATH="'+prefix+'/share/orogen/models"\n')
            f.write('export ROCK_BUNDLE_PATH="'+prefix+'/../bundles"\n')
            f.write('export ORBInitRef="NameService=corbaname::localhost"\n')
            f.write('export RTT_COMPONENT_PATH="'+prefix+'/lib/orocos/plugins"\n')
            f.write('export QT_PLUGIN_DIR="'+prefix+'/lib/qt"\n')
            f.write('export QT_PLUGIN_PATH="'+prefix+'/lib/qt"\n')
            f.write('export VIZKIT_PLUGIN_RUBY_PATH="'+prefix+'/lib"\n')
            f.write('source base/scripts/shell/zsh\n')
            _make_pybob_aliases(f)

    execute.makeDir(cfg["devDir"]+"/install/bin")
    if len(aPath) == 0:
        with open(cfg["devDir"]+"/install/bin/amake", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("${AUTOPROJ_CURRENT_ROOT}/pybob/pybob.py install $@\n")
        cmd = ["chmod", "+x", cfg["devDir"]+"/install/bin/amake"]
        execute.simpleExecute(cmd)
        with open(cfg["devDir"]+"/install/bin/aup", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("${AUTOPROJ_CURRENT_ROOT}/pybob/pybob.py fetch $@\n")
        cmd = ["chmod", "+x", cfg["devDir"]+"/install/bin/aup"]
        execute.simpleExecute(cmd)

    with open(cfg["devDir"]+"/install/bin/cmake_debug", "w") as f:
        f.write("#!/bin/bash\n")
        options = "-DROCK_TEST_ENABLED=OFF"
        if not "autoprojEnv" in cfg or not cfg["autoprojEnv"]:
            options += " -DBINDINGS_RUBY=OFF "
        if platform == "Windows":
            f.write("cmake .. "+options+"-DCMAKE_INSTALL_PREFIX=$AUTOPROJ_CURRENT_ROOT/install -DCMAKE_BUILD_TYPE=Debug  -G \"MSYS Makefiles\" $@\n")
        else:
            f.write("cmake .. "+options+"-DCMAKE_INSTALL_PREFIX=$AUTOPROJ_CURRENT_ROOT/install -DCMAKE_BUILD_TYPE=Debug $@\n")
    with open(cfg["devDir"]+"/install/bin/cmake_release", "w") as f:
        f.write("#!/bin/bash\n")
        if platform == "Windows":
            f.write("cmake .. "+options+"-DCMAKE_INSTALL_PREFIX=$AUTOPROJ_CURRENT_ROOT/install -DCMAKE_BUILD_TYPE=Release  -G \"MSYS Makefiles\" $@\n")
        else:
            f.write("cmake .. "+options+"-DCMAKE_INSTALL_PREFIX=$AUTOPROJ_CURRENT_ROOT/install -DCMAKE_BUILD_TYPE=Release $@\n")

    with open(cfg["devDir"]+"/.bundle_env.sh", "w") as f:
        f.write("unset ROCK_BUNDLE\n")

    cmd = ["chmod", "+x", cfg["devDir"]+"/install/bin/cmake_debug"]
    execute.simpleExecute(cmd)

    cmd = ["chmod", "+x", cfg["devDir"]+"/install/bin/cmake_release"]
    execute.simpleExecute(cmd)
    source(cfg["devDir"]+"/env.sh")


def _make_pybob_aliases(f):
    env_variables = []
    if "PYTHON" in os.environ:
        PYTHON_ALIAS_PREFIX = "$PYTHON "
    else:
        PYTHON_ALIAS_PREFIX = ""

    f.write("alias bob='%s${MARS_SCRIPT_DIR}/pybob.py'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-bootstrap='%s${MARS_SCRIPT_DIR}/pybob.py bootstrap'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-install='%s${MARS_SCRIPT_DIR}/pybob.py install'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-rebuild='%s${MARS_SCRIPT_DIR}/pybob.py rebuild'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-build='%s${MARS_SCRIPT_DIR}/pybob.py'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-diff='%s${MARS_SCRIPT_DIR}/pybob.py diff'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-list='%s${MARS_SCRIPT_DIR}/pybob.py list'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-fetch='%s${MARS_SCRIPT_DIR}/pybob.py fetch'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-show-log='%s${MARS_SCRIPT_DIR}/pybob.py show-log'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-info='%s${MARS_SCRIPT_DIR}/pybob.py info'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write("alias bob-envsh='%s${MARS_SCRIPT_DIR}/pybob.py envsh'\n"
            % PYTHON_ALIAS_PREFIX)
    f.write(". ${MARS_SCRIPT_DIR}/auto_complete.sh\n")

    if "PYTHON" in os.environ:
        f.write("export PYTHON=%s\n" % os.environ["PYTHON"])
    if "CYTHON" in os.environ:
        f.write("export CYTHON=%s\n" % os.environ["CYTHON"])
