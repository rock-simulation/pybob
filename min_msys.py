#! /usr/bin/env python

import sys
import os

path = "/mingw64/"
binPath = path + "bin/"
libPath = path + "lib/"
includePath = path + "include/"
sharePath = path + "share/"

def remove_(s):
    print "remove " + s
    sys.stdout.flush()
    os.system("rm -rf " + s)

remove_(libPath + "libboost*")
remove_(sharePath + "qt5/doc")
remove_(sharePath + "qt5/examples")
remove_(sharePath + "qt5/qml")
remove_(sharePath + "qt5/plugins/geoservices")
remove_(sharePath + "qt5/plugins/qmltooling")
remove_(sharePath + "qt5/plugins/sensorgestures")
remove_(sharePath + "qt5/plugins/sceneparsers")

remove_(binPath + "Qt5Qml*")
remove_(binPath + "Qt5Quick*")
remove_(binPath + "Qt5Script*")
remove_(binPath + "Qt5Labs*")
remove_(binPath + "Qt53D*")
remove_(binPath + "Qt5Designer*")
remove_(binPath + "Qt5Multimedia*")
remove_(binPath + "Qt5Clucende*")
remove_(binPath + "Qt5Location*")
remove_(binPath + "Qt5Web*")

remove_(libPath + "libQt5Qml*")
remove_(libPath + "libQt5Quick*")
remove_(libPath + "libQt5Script*")
remove_(libPath + "libQt5Labs*")
remove_(libPath + "libQt53D*")
remove_(libPath + "libQt5Designer*")
remove_(libPath + "libQt5Multimedia*")
remove_(libPath + "libQt5Clucende*")
remove_(libPath + "libQt5Location*")
remove_(libPath + "libQt5Web*")

remove_(includePath + "QtQml*")
remove_(includePath + "QtQuick*")
remove_(includePath + "QtScript*")
remove_(includePath + "QtLabs*")
remove_(includePath + "Qt3D*")
remove_(includePath + "QtDesigner*")
remove_(includePath + "QtMultimedia*")
remove_(includePath + "QtClucende*")
remove_(includePath + "QtLocation*")
remove_(includePath + "QtWeb*")

print "clean pacman cache"
sys.stdout.flush()
os.system("pacman -Sc --noconfirm")

os.system("python recursive_remove_build.py .. rm")
