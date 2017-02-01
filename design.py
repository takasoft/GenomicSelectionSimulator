# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
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
        self.gridLayout.addWidget(self.listWidgetOrgPopulation, 1, 0, 1, 1)
        self.listWidgetSelectionApproach = QtWidgets.QListWidget(self.centralwidget)
        self.listWidgetSelectionApproach.setMaximumSize(QtCore.QSize(16777215, 100))
        self.listWidgetSelectionApproach.setObjectName("listWidgetSelectionApproach")
        self.gridLayout.addWidget(self.listWidgetSelectionApproach, 1, 1, 1, 1)
        self.btnStart = QtWidgets.QPushButton(self.centralwidget)
        self.btnStart.setObjectName("btnStart")
        self.gridLayout.addWidget(self.btnStart, 1, 2, 1, 1)
        #self.canvas = QtWidgets.QWidget(self.centralwidget)
        #self.canvas.setObjectName("canvas")
        #self.gridLayout.addWidget(self.canvas, 2, 0, 1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 640, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Genomic Selection Simulation"))
        self.labelOrgPopulation.setText(_translate("MainWindow", "Original Population"))
        self.labelSelectionApproach.setText(_translate("MainWindow", "Selection Approach"))
        self.btnStart.setText(_translate("MainWindow", "Start"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))

