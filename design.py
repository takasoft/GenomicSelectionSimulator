# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(640, 480)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.labelOrgPopulation = QtWidgets.QLabel(self.centralwidget)
        self.labelOrgPopulation.setMaximumSize(QtCore.QSize(16777215, 20))
        self.labelOrgPopulation.setObjectName("labelOrgPopulation")
        self.gridLayout.addWidget(self.labelOrgPopulation, 0, 0, 1, 1)
        self.labelSelectionApproach = QtWidgets.QLabel(self.centralwidget)
        self.labelSelectionApproach.setMaximumSize(QtCore.QSize(16777215, 20))
        self.labelSelectionApproach.setObjectName("labelSelectionApproach")
        self.gridLayout.addWidget(self.labelSelectionApproach, 0, 1, 1, 1)
        self.listWidgetOrgPopulation = QtWidgets.QListWidget(self.centralwidget)
        self.listWidgetOrgPopulation.setMaximumSize(QtCore.QSize(16777215, 100))
        self.listWidgetOrgPopulation.setObjectName("listWidgetOrgPopulation")
        self.gridLayout.addWidget(self.listWidgetOrgPopulation, 3, 0, 1, 1)
        self.listWidgetSelectionApproach = QtWidgets.QListWidget(self.centralwidget)
        self.listWidgetSelectionApproach.setMaximumSize(QtCore.QSize(16777215, 100))
        self.listWidgetSelectionApproach.setObjectName("listWidgetSelectionApproach")
        self.gridLayout.addWidget(self.listWidgetSelectionApproach, 3, 1, 1, 1)
        self.canvas = QtWidgets.QWidget(self.centralwidget)
        self.canvas.setMinimumSize(QtCore.QSize(0, 167))
        self.canvas.setObjectName("canvas")
        self.gridLayout.addWidget(self.canvas, 7, 0, 1, 8)
        self.labelStatus = QtWidgets.QLabel(self.centralwidget)
        self.labelStatus.setMaximumSize(QtCore.QSize(16777215, 20))
        self.labelStatus.setText("")
        self.labelStatus.setObjectName("labelStatus")
        self.gridLayout.addWidget(self.labelStatus, 8, 0, 1, 8)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.btnGenerateData = QtWidgets.QPushButton(self.centralwidget)
        self.btnGenerateData.setObjectName("btnGenerateData")
        self.verticalLayout.addWidget(self.btnGenerateData)
        self.btnLoadData = QtWidgets.QPushButton(self.centralwidget)
        self.btnLoadData.setObjectName("btnLoadData")
        self.verticalLayout.addWidget(self.btnLoadData)
        self.btnStart = QtWidgets.QPushButton(self.centralwidget)
        self.btnStart.setObjectName("btnStart")
        self.verticalLayout.addWidget(self.btnStart)
        self.gridLayout.addLayout(self.verticalLayout, 3, 5, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 640, 25))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionOpenData = QtWidgets.QAction(MainWindow)
        self.actionOpenData.setObjectName("actionOpenData")
        self.menuFile.addAction(self.actionExit)
        self.menuFile.addAction(self.actionOpenData)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Genomic Selection Simulation"))
        self.labelOrgPopulation.setText(_translate("MainWindow", "Original Population"))
        self.labelSelectionApproach.setText(_translate("MainWindow", "Selection Approach"))
        self.btnGenerateData.setText(_translate("MainWindow", "Generate Data"))
        self.btnLoadData.setText(_translate("MainWindow", "Load Data"))
        self.btnStart.setText(_translate("MainWindow", "Start"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionOpenData.setText(_translate("MainWindow", "Open Data File"))

