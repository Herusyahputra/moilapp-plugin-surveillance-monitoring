# Form implementation generated from reading ui file 'ui_monitor.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Monitor(object):
    def setupUi(self, Monitor):
        Monitor.setObjectName("Monitor")
        Monitor.setEnabled(True)
        Monitor.resize(506, 337)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Monitor)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.display = QtWidgets.QVBoxLayout()
        self.display.setSpacing(0)
        self.display.setObjectName("display")
        self.scrollArea = QtWidgets.QScrollArea(parent=Monitor)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 504, 280))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.displayLab = QtWidgets.QLabel(parent=self.scrollAreaWidgetContents)
        self.displayLab.setMinimumSize(QtCore.QSize(300, 260))
        self.displayLab.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.displayLab.setText("")
        self.displayLab.setObjectName("displayLab")
        self.horizontalLayout_2.addWidget(self.displayLab)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.display.addWidget(self.scrollArea)
        self.menuFrame = QtWidgets.QFrame(parent=Monitor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.menuFrame.sizePolicy().hasHeightForWidth())
        self.menuFrame.setSizePolicy(sizePolicy)
        self.menuFrame.setMinimumSize(QtCore.QSize(0, 55))
        self.menuFrame.setMaximumSize(QtCore.QSize(500, 55))
        self.menuFrame.setObjectName("menuFrame")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.menuFrame)
        self.horizontalLayout_3.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMaximumSize)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.setupButton = QtWidgets.QPushButton(parent=self.menuFrame)
        self.setupButton.setMinimumSize(QtCore.QSize(20, 30))
        self.setupButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/setup.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.setupButton.setIcon(icon)
        self.setupButton.setIconSize(QtCore.QSize(40, 30))
        self.setupButton.setObjectName("setupButton")
        self.horizontalLayout_3.addWidget(self.setupButton)
        self.captureButton = QtWidgets.QPushButton(parent=self.menuFrame)
        self.captureButton.setMinimumSize(QtCore.QSize(20, 30))
        self.captureButton.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icon/camera.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.captureButton.setIcon(icon1)
        self.captureButton.setIconSize(QtCore.QSize(40, 30))
        self.captureButton.setObjectName("captureButton")
        self.horizontalLayout_3.addWidget(self.captureButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.deleteButton = QtWidgets.QPushButton(parent=self.menuFrame)
        self.deleteButton.setMinimumSize(QtCore.QSize(20, 30))
        self.deleteButton.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icon/minus-circle.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.deleteButton.setIcon(icon2)
        self.deleteButton.setIconSize(QtCore.QSize(30, 25))
        self.deleteButton.setObjectName("deleteButton")
        self.horizontalLayout_3.addWidget(self.deleteButton)
        self.display.addWidget(self.menuFrame)
        self.horizontalLayout.addLayout(self.display)

        self.retranslateUi(Monitor)
        QtCore.QMetaObject.connectSlotsByName(Monitor)

    def retranslateUi(self, Monitor):
        _translate = QtCore.QCoreApplication.translate
        Monitor.setWindowTitle(_translate("Monitor", "Form"))
