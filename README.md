# NOTES:

  - pybob is a preliminary implementation of an project build system compatible
     to autoproj, if you have problem you might consider using autoproj

# Prepare Windows for pybob:

  1. install msys2 (https://msys2.github.io/ *preferable 64bit version*)
  2. perform the update steps listed on the msys2 website
  3. open mingw64 shell from msys2 intalled folder
     (**important** do not use the msys shell)
  4. perform following steps in the shell:

          pacman -S git wget tar unzip which patch
          pacman -S mingw-w64-x86_64-cmake
          pacman -S mingw-w64-x86_64-pkg-config
          pacman -S mingw-w64-x86_64-python2
          pacman -S mingw-w64-x86_64-python2-pyqt5
          pacman -S mingw-w64-x86_64-libyaml
          pacman -S mingw-w64-x86_64-gcc
          pacman -S mingw-w64-x86_64-make
          wget http://pyyaml.org/download/pyyaml/PyYAML-3.12.tar.gz
          tar -xzvf PyYAML-3.12.tar.gz
          cd PyYAML-3.12
          python setup.py --with-libyaml install

  5. continue with general install notes

# Prepare Ubuntu for pybob:

       sudo apt-get install git python-yaml

# Install MARS via pybob

       mkdir mars-dev
       cd mars-dev
       git clone https://github.com/rock-simulation/pybob.git
       cd pybob
       ./pybob.py buildconf path="https://github.com/rock-simulation/simulation-buildconf.git"
       cd ..
       source env.sh

       bob-fetch
       bob-install

  You can start MARS in the terminal via `mars_app`.
  Once you open a new terminal you have to `source env.sh` again.
  
# Todo:
  - check if "git pull" fails
