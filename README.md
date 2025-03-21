# NOTES:

  - pybob is a preliminary implementation of an project build system compatible
     to autoproj, if you have problem you might consider using autoproj

# Prepare Windows for pybob:

  1. install msys2 (https://msys2.github.io/ *preferable 64bit version*)
  2. perform the update steps listed on the msys2 website
  3. open mingw64 shell from msys2 intalled folder
     (**important** do not use the msys shell)
  4. perform following steps in the shell:

          pacman -S wget
          wget https://raw.githubusercontent.com/rock-simulation/pybob/master/prepare_msys2.sh
          bash prepare_msys2.sh

  5. continue with general install notes

# Prepare Ubuntu for pybob:

       sudo apt-get install git python-yaml python-distro
  or (using python3)

       sudo apt install git python3-yaml python3-distro

You can exclude the distro module by

       export QT5_UBUNTU=True
or `False` if you have a older system which is incompatible with QT5.

       sudo apt install git python3-yaml python3-distro

On newer Ubuntu versions it is recommended to use a virtual env for python packages:

       sudo apt install python3-venv
       
# Prepare macOS for pybob:

  For OS X it is recommended to use python3.6 and Qt5, although the tools generally are compatible to python2.7 and Qt4.
  
  1. Install MacPorts (https://www.macports.org), which is used by pybob to install system dependencies.
     **Note**: follow the install instructions on the macports website carefully.
  2. Install git and wget:
  
          sudo port install git wget
    
  3. Install python38 and python yaml package via MacPorts:
  
          sudo port install py38-yaml
  
  4. It is recommended to select python3.8 as default for the terminal:
  
          sudo port select --set python python3.8
  
  5. To use the pybob gui and exported plot gui of MARS:
  
          sudo port install py38-sip py38-pyqt5
  
  6. To use the exported plot gui of MARS some more packages are needed:
  
          sudo port install py38-scipy py38-matplotlib
  
  7. To generate pdf plots with latex support:
  
          sudo port install texlive texlive-latex-extra

# Install MARS via pybob

       mkdir mars-dev
       cd mars-dev
       git clone https://github.com/rock-simulation/pybob.git
create venv:
       python3 -m venv install/venv
activate venv:
       . install/venv/bin/activate
intall deps into venv:
       pip install PyYaml
       pip install setuptools
continue with pybob
       cd pybob
       ./pybob.py buildconf path="https://github.com/rock-simulation/simulation-buildconf.git"
       cd ..
       source env.sh

       bob-fetch
       bob-install

  You can start MARS in the terminal via `mars_app`.
  Once you open a new terminal you have to `source env.sh` again.

# Rock/orogen support

## macOS Notes:

To be able to build Rock core libs on macOS one have to install ruby2.7 via macports, since the system ruby library is not compatible. Also the macports ruby version have to be selected: `sudo port select ruby ruby27` – and restart the terminal.

Install castxml: `sudo port install castxml`
needed gems:
  sudo gem install rice -v 3.0.0
  sudo gem isntall eigen

# Todo:
  - check if "git pull" fails
  - add submodule support
  - add override links from package sets
  - add override handling of package sets
