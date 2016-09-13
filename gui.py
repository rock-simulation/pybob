import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
#import pybob

packages = []
pattern = ""
currentPackage = ""

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("PyBob")
hLayout = QHBoxLayout(window)
vLayout = QVBoxLayout()
hLayout.addLayout(vLayout)

checkDeps = QCheckBox("check dependencies")
checkDeps.setChecked(True)
buildconfPush = QPushButton("update buildconf")
lineEdit = QLineEdit()
listWidget = QListWidget()

vLayout2 = QVBoxLayout()
hLayout.addLayout(vLayout2)
outConsole = QTextEdit()
outConsole.setReadOnly(True)
vLayout2.addWidget(outConsole)
errConsole = QTextEdit()
errConsole.setReadOnly(True)
vLayout2.addWidget(errConsole)


vLayout.addWidget(buildconfPush)
vLayout.addWidget(lineEdit)
vLayout.addWidget(listWidget)
vLayout.addWidget(checkDeps)

hLayout = QHBoxLayout()
bootPush = QPushButton("bootstrap")
fetchPush = QPushButton("fetch")
buildPush = QPushButton("build")
logPush = QPushButton("show-log")
hLayout.addWidget(bootPush)
hLayout.addWidget(fetchPush)
hLayout.addWidget(buildPush)
hLayout.addWidget(logPush)


#hLayout.addWidget(QSpacerItem())
vLayout.addLayout(hLayout)

def updatePackageList():
    global pattern
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
    global pattern
    pattern = s
    updatePackageList()

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

def fetch():
    global currentPackage
    global checkDeps
    #cfg["checkDeps"] = checkDeps.isChecked()
    add = ""
    if not checkDeps.isChecked():
        add += " -n"
    if len(currentPackage) > 0:
        #call(["python", "pybob.py", "fetch", currentPackage, add])
        os.system("python pybob.py fetch " + currentPackage + add)
        #fetch_(

def build():
    global currentPackage
    add = ""
    if not checkDeps.isChecked():
        add += " -n"
    if len(currentPackage) > 0:
        #call(["python", "pybob.py", "install", currentPackage, add])
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
fetchPush.connect(fetchPush, SIGNAL("clicked()"), fetch)
buildPush.connect(buildPush, SIGNAL("clicked()"), build)
logPush.connect(logPush, SIGNAL("clicked()"), log)

window.resize(500, 500)
window.show()

sys.exit(app.exec_())
