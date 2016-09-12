import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import subprocess
packages = []
pattern = ""
currentPackage = ""

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("PyBob")
vLayout = QVBoxLayout(window)

checkDeps = QCheckBox("check dependencies")
checkDeps.setChecked(True)
buildconfPush = QPushButton("update buildconf")
lineEdit = QLineEdit()
listWidget = QListWidget()

vLayout.addWidget(buildconfPush)
vLayout.addWidget(lineEdit)
vLayout.addWidget(listWidget)
vLayout.addWidget(checkDeps)

hLayout = QHBoxLayout()
bootPush = QPushButton("bootstrap")
buildPush = QPushButton("build")
logPush = QPushButton("show-log")
hLayout.addWidget(bootPush)
hLayout.addWidget(buildPush)
hLayout.addWidget(logPush)
#hLayout.addWidget(QSpacerItem())
vLayout.addLayout(hLayout)

def updatePackageList():
    global packages
    listWidget.clear()
    exp = QRegExp(pattern)
    for p in packages:
        if exp.indexIn(p) != -1:
            listWidget.addItem(p)

def updatePackages():
    global packages
    path = "../"

    if "AUTOPROJ_CURRENT_ROOT" in os.environ:
        path = os.environ["AUTOPROJ_CURRENT_ROOT"]

    pFile = path+"/autoproj/bob/packages.txt"
    print pFile
    del packages[:]
    if os.path.isfile(pFile):
        with open(pFile) as f:
            for line in f:
                if len(line) > 0:
                    packages.append(line.strip())
    updatePackageList()


def listItemChanged(item):
    global currentPackage
    currentPackage = str(item.data(0).toString())
    print "da: " + currentPackage

def patternChanged(s):
    pattern = s
    updatePackages()

def buildconf():
    os.system("python pybob.py buildconf")
    updatePackages()

def bootstrap():
    global currentPackage
    global checkDeps
    add = ""
    if not checkDeps.isChecked():
        add += " -n"
    if len(currentPackage) > 0:
        os.system("python pybob.py bootstrap " + currentPackage + add)

def build():
    global currentPackage
    add = ""
    if not checkDeps.isChecked():
        add += " -n"
    if len(currentPackage) > 0:
        os.system("python pybob.py install " + currentPackage + add)

def log():
    global currentPackage
    if len(currentPackage) > 0:
        os.system("python pybob.py show-log " + currentPackage)




updatePackages()
lineEdit.connect(lineEdit, SIGNAL("textChanged(const QString&)"), patternChanged)
listWidget.connect(listWidget, SIGNAL("itemPressed(QListWidgetItem*)"),
                   listItemChanged)
buildconfPush.connect(buildconfPush, SIGNAL("clicked()"), buildconf)
bootPush.connect(bootPush, SIGNAL("clicked()"), bootstrap)
buildPush.connect(buildPush, SIGNAL("clicked()"), build)
logPush.connect(logPush, SIGNAL("clicked()"), log)

window.resize(500, 500)
window.show()

sys.exit(app.exec_())
