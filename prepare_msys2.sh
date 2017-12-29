#! /bin/bash

pacman --noconfirm -S git wget tar unzip which patch
pacman --noconfirm -S mingw-w64-x86_64-python2
pacman --noconfirm -S mingw-w64-x86_64-libyaml
pacman --noconfirm -S mingw-w64-x86_64-gcc
pacman --noconfirm -S mingw-w64-x86_64-make
pacman --noconfirm -S mingw-w64-x86_64-glew
wget http://pyyaml.org/download/pyyaml/PyYAML-3.12.tar.gz
tar -xzvf PyYAML-3.12.tar.gz
cd PyYAML-3.12
python setup.py --with-libyaml install
ln -s /mingw64/bin/mingw32-make.exe /mingw64/bin/make.exe
