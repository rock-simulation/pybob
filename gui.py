import os
import sys
haveQT5 = True
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
except:
    haveQT5 = False
if not haveQT5:
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

cmdEdit = QLineEdit()


vLayout.addWidget(buildconfPush)
vLayout.addWidget(lineEdit)
vLayout.addWidget(listWidget)
vLayout.addWidget(checkDeps)
vLayout.addWidget(cmdEdit)

bootPush = QPushButton("bootstrap")
fetchPush = QPushButton("fetch")
rebuildPush = QPushButton("rebuild")
buildPush = QPushButton("build")
logPush = QPushButton("show-log")
cmdPush = QPushButton("run")

hLayout = QHBoxLayout()
hLayout.addWidget(bootPush)
hLayout.addWidget(fetchPush)
hLayout.addWidget(cmdPush)
vLayout.addLayout(hLayout)

hLayout = QHBoxLayout()
hLayout.addWidget(rebuildPush)
hLayout.addWidget(buildPush)
hLayout.addWidget(logPush)
vLayout.addLayout(hLayout)


#hLayout.addWidget(QSpacerItem())

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
    if haveQT5:
        currentPackage = str(item.data(0))
    else: 
        currentPackage = str(item.data(0).toString())
    print "da: " + currentPackage
    sys.stdout.flush()

def patternChanged(s):
    global pattern
    pattern = s
    updatePackageList()

def buildconf():
    os.system("python pybob.py buildconf")
    updatePackages()

def execute(action):
    global currentPackage
    global checkDeps
    if len(currentPackage) == 0:
        return
    cmd = ["python", "pybob.py", action, currentPackage]
    if not checkDeps.isChecked():
        cmd.append("-n")
    os.system(" ".join(cmd))
    
def bootstrap():
    execute("bootstrap")

def fetch():
    execute("fetch")

def rebuild():
    execute("rebuild")

def build():
    execute("install")

def log():
    execute("show-log")

def cmd():
    os.system(str(cmdEdit.text()))


updatePackages()
if haveQT5:
    lineEdit.textChanged.connect(patternChanged)
    buildconfPush.clicked.connect(buildconf)
    bootPush.clicked.connect(bootstrap)
    fetchPush.clicked.connect(fetch)
    rebuildPush.clicked.connect(rebuild)
    buildPush.clicked.connect(build)
    logPush.clicked.connect(log)
    cmdPush.clicked.connect(cmd)
    listWidget.itemPressed.connect(listItemChanged)
else:
    lineEdit.connect(lineEdit, SIGNAL("textChanged(const QString&)"), patternChanged)
    listWidget.connect(listWidget, SIGNAL("itemPressed(QListWidgetItem*)"),
                       listItemChanged)
    buildconfPush.connect(buildconfPush, SIGNAL("clicked()"), buildconf)
    bootPush.connect(bootPush, SIGNAL("clicked()"), bootstrap)
    fetchPush.connect(fetchPush, SIGNAL("clicked()"), fetch)
    buildPush.connect(buildPush, SIGNAL("clicked()"), build)
    logPush.connect(logPush, SIGNAL("clicked()"), log)
    cmdPush.connect(cmdPush, SIGNAL("clicked()"), cmd)

window.resize(500, 500)
window.show()

sys.exit(app.exec_())
