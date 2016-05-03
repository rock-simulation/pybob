#! /bin/bash

PACKAGES_FILE="../autoproj/bob/packages.txt"

pushd . > /dev/null 2>&1

function setScriptDir {
    if [[ x"${MARS_SCRIPT_DIR}" == "x" ]]; then
        MARS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    fi
    export MARS_SCRIPT_DIR=${MARS_SCRIPT_DIR}
}

setScriptDir

function parse_yaml {
   local s='[[:space:]]*' w='[a-zA-Z0-9_-]*' fs=$(echo @|tr @ '\034')
   sed -ne "/.:./d" \
        -e "/#/d" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\2|p" $1
}

packages1="buildconf list bootstrap install rebuild clean fetch update diff help"
packages=""
if [ -f ${MARS_SCRIPT_DIR}/${PACKAGES_FILE} ]; then
    while read package; do
        package=${package/\#*/}
        if [[ x${package} = x ]]; then
            continue
        fi

	      if [[ x${packages} != x ]]; then
	          packages+=" "
	      fi
	      packages+=${package}
    done < ${MARS_SCRIPT_DIR}/${PACKAGES_FILE}
fi

#echo "packages: ${packages1} ${packages}"

complete -o default -W "${packages1} ${packages}" pybob.py
complete -o default -W "${packages1}" bob
complete -o default -W "${packages}" bob-install
complete -o default -W "${packages}" bob-bootstrap
complete -o default -W "${packages}" bob-rebuild
complete -o default -W "${packages} buildconf" bob-diff
complete -o default -W "${packages}" bob-fetch

popd > /dev/null 2>&1
