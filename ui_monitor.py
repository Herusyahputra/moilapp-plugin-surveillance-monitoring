# Form implementation generated from reading ui file '.\ui_monitor.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Main(object):
    def setupUi(self, Main):
        Main.setObjectName("Main")
        Main.setEnabled(True)
        Main.resize(324, 317)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Main)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.display = QtWidgets.QVBoxLayout()
        self.display.setSpacing(1)
        self.display.setObjectName("display")
        self.frame = QtWidgets.QFrame(parent=Main)
        self.frame.setMinimumSize(QtCore.QSize(300, 260))
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_74 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_74.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_74.setSpacing(0)
        self.horizontalLayout_74.setObjectName("horizontalLayout_74")
        self.displayLab = QtWidgets.QLabel(parent=self.frame)
        self.displayLab.setMinimumSize(QtCore.QSize(300, 260))
        self.displayLab.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.displayLab.setText("")
        self.displayLab.setObjectName("displayLab")
        self.horizontalLayout_74.addWidget(self.displayLab)
        self.display.addWidget(self.frame)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.setupButton = QtWidgets.QPushButton(parent=Main)
        self.setupButton.setMinimumSize(QtCore.QSize(20, 30))
        self.setupButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/setup.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.setupButton.setIcon(icon)
        self.setupButton.setIconSize(QtCore.QSize(40, 30))
        self.setupButton.setObjectName("setupButton")
        self.horizontalLayout_2.addWidget(self.setupButton)
        self.captureButton = QtWidgets.QPushButton(parent=Main)
        self.captureButton.setMinimumSize(QtCore.QSize(20, 30))
        self.captureButton.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icon/camera.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.captureButton.setIcon(icon1)
        self.captureButton.setIconSize(QtCore.QSize(40, 30))
        self.captureButton.setObjectName("captureButton")
        self.horizontalLayout_2.addWidget(self.captureButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.deleteButton = QtWidgets.QPushButton(parent=Main)
        self.deleteButton.setMinimumSize(QtCore.QSize(20, 30))
        self.deleteButton.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icon/minus-circle.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.deleteButton.setIcon(icon2)
        self.deleteButton.setIconSize(QtCore.QSize(30, 25))
        self.deleteButton.setObjectName("deleteButton")
        self.horizontalLayout_2.addWidget(self.deleteButton)
        self.display.addLayout(self.horizontalLayout_2)
        self.horizontalLayout.addLayout(self.display)

        self.retranslateUi(Main)
        QtCore.QMetaObject.connectSlotsByName(Main)

    def retranslateUi(self, Main):
        _translate = QtCore.QCoreApplication.translate
        Main.setWindowTitle(_translate("Main", "Form"))