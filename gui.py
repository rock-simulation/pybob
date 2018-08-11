#! /usr/bin/env python

import os
import sys
import execute as ex
import subprocess

haveQT5 = True
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
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

left = QWidget()
right = QWidget()

hLayout = QHBoxLayout(window)
vLayout = QVBoxLayout()
hLayout.addWidget(left)
hLayout.addWidget(right)
left.setLayout(vLayout)
spLeft = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
spLeft.setHorizontalStretch(1)
left.setSizePolicy(spLeft)

checkDeps = QCheckBox("check dependencies")
checkDeps.setChecked(True)
buildconfPush = QPushButton("update buildconf")
lineEdit = QLineEdit()
listWidget = QListWidget()

vLayout2 = QVBoxLayout()
right.setLayout(vLayout2)
spRight = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
spRight.setHorizontalStretch(3)
right.setSizePolicy(spRight)
#hLayout.addLayout(vLayout2)
outConsole = QTextEdit()
outConsole.setReadOnly(True)
outConsole.ensureCursorVisible()
debugConsole = outConsole

font = QFont()
font.setPointSize(16)
outConsole.setFont(font)

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

process = None
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
    print(pFile)
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
    global process
    global debugConsole

    cursor = debugConsole.textCursor()
    if haveQT5:
        cursor.setPosition(len(debugConsole.toPlainText()))
    else:
        cursor.setPosition(debugConsole.toPlainText().size())
    debugConsole.setTextCursor(cursor)

    if len(currentPackage) == 0:
        return
    cmd = ["python", "pybob.py", action, currentPackage]
    if not checkDeps.isChecked():
        cmd.append("-n")

    process = subprocess.Popen(" ".join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def bootstrap():
    execute("bootstrap")

def fetch():
    execute("fetch")

def rebuild():
    execute("rebuild")

def build():
    execute("install")

def log():
    global debugConsole
    debugConsole = errConsole
    execute("show-log")

def cmd():
    os.system(str(cmdEdit.text()))

def update():
    global process, debugConsole, outConsole

    if process:
        line = process.stdout.readline()
        if line == "":
            process = None
            debugConsole.insertPlainText("\n")
            debugConsole = outConsole
        else:
            arrLine = line.split("\033")
            for l in arrLine:
                if l[:3] == "[0m":
                    l = l[3:]
                    debugConsole.setTextColor(QColor("black"))
                elif l[:6] == "[32;1m":
                    l = l[6:]
                    debugConsole.setTextColor(QColor("#228822"))
                elif l[:6] == "[31;1m":
                    l = l[6:]
                    debugConsole.setTextColor(QColor("#882222"))
                elif l[:10] == "[38;5;166m":
                    l = l[10:]
                    debugConsole.setTextColor(QColor("#aa5522"))
                debugConsole.insertPlainText(l)
                debugConsole.verticalScrollBar().setValue(
                    debugConsole.verticalScrollBar().maximum())

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
    rebuildPush.connect(rebuildPush, SIGNAL("clicked()"), rebuild)
    logPush.connect(logPush, SIGNAL("clicked()"), log)
    cmdPush.connect(cmdPush, SIGNAL("clicked()"), cmd)

window.resize(800, 500)
window.show()

timer = QTimer()
timer.timeout.connect(update)
timer.start(20)

sys.exit(app.exec_())
