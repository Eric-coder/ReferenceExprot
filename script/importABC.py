# coding=utf-8
# Description：列出材质信息json文件里记录的abc资产，并选择给回去，默认是全部
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# _author__ = 'Han Bo'


import os
import sys

try:
    from PySide2 import QtWidgets
    from PySide2 import QtCore
except ImportError:
    from PySide import QtGui as QtWidgets
    from PySide import QtCore


class MainView(QtWidgets.QDialog):
    def __init__(self, parent=None):
        import abc_mat_input_ui
        import maya.cmds as cmds
        import maya.mel as mel
        import os
        import json
        import re
        super(MainView, self).__init__(parent)
        self._cmds = cmds
        self._mel = mel
        reload(abc_mat_input_ui)
        self._maya = abc_mat_input_ui.Maya()
        self._os = os
        self._json=json
        self._re = re

        self._mainUI()

    def _mainUI(self):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setStyleSheet("QListWidget{background: #5a5a5a;}")
        # abcOutPutJsonLabel control
        self.abcOutPutJsonLabel = QtWidgets.QLabel('abc output json file path: ')
        # jsonMetlPathLineEdit jsonMetlPuthButton control
        self.jsonMetlPathLineEdit = QtWidgets.QLineEdit()
        self.jsonMetlPuthButton = QtWidgets.QPushButton(u'...')
        # assetsList control
        self.assetsList = QtWidgets.QListWidget()
        self.assetsList.setSortingEnabled(1)
        self.assetsList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.item = QtWidgets.QListWidgetItem(self.assetsList)
        # inputAbcButton inputMatlButton control
        self.inputAbcButton = QtWidgets.QPushButton(U'Input Abc')
        self.inputMatlButton = QtWidgets.QPushButton(U'Input Matl')
        # layout
        twoHboxLayput = QtWidgets.QHBoxLayout()
        twoHboxLayput.addWidget(self.inputAbcButton)
        twoHboxLayput.addStretch()
        twoHboxLayput.addWidget(self.inputMatlButton)

        pathHboxLayput = QtWidgets.QHBoxLayout()
        pathHboxLayput.addWidget(self.jsonMetlPathLineEdit)
        pathHboxLayput.addWidget(self.jsonMetlPuthButton)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.abcOutPutJsonLabel)
        mainLayout.addLayout(pathHboxLayput)
        mainLayout.addWidget(self.assetsList)
        mainLayout.addLayout(twoHboxLayput)
        # click button
        self.jsonMetlPuthButton.clicked.connect(self.getJsonPath)
        self.inputAbcButton.clicked.connect(self.inputAbc)
        self.inputMatlButton.clicked.connect(self.inputMatl)

        self.setLayout(mainLayout)

    def getJsonPath(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open file dialog", "/",
                                                          QtWidgets.QFileDialog.ShowDirsOnly).replace('\\', '/')
        self.jsonMetlPathLineEdit.setText(path)
        jsonDir = self.jsonMetlPathLineEdit.text()
        #print jsonDir
        self.jsonAbcPath = jsonDir + '/ExportReferences.json'
        self.jsonMetlPath = jsonDir + '/ExportMaterial.json'
        self.abcFileMessage()

    def abcFileMessage(self):
        with open(self.jsonAbcPath) as json_file:
            dataJson = self._json.load(json_file)
            self.assetsList.clear()
            self.finalPath = []
            for index in dataJson.keys():
                item = QtWidgets.QListWidgetItem(index + '.abc')
                item.setCheckState(QtCore.Qt.Checked)
                self.assetsList.addItem(item)
                path = dataJson[index]['path']
                self.finalPath.append(path)
            self.finalPath = list(set(self.finalPath))[0]
            #print self.finalPath
    def inputAbc(self):

        pathAbc = self.finalPath + '/References'
        pathMetl = self.finalPath + '/Material'

        checkState = []
        for index in xrange(self.assetsList.count()):  # 得到每一行的lineWidget索引
            item = self.assetsList.item(index)  # 重新获取一下每一行
            state = item.checkState()  # 得到每一行的chackState的状态
            checkState.append(state)
            # print state

        if QtCore.Qt.Unchecked not in checkState:
            #print '1'
            defaultDictAbc = {}
            for index in xrange(self.assetsList.count()):  # 得到每一行的lineWidget索引
                lineContent = self.assetsList.item(index).text()
                metlName = lineContent.split('.')[0]
                # print lineContent
                # print metlName
                defaultDictAbc[pathAbc + '/' + lineContent] = pathMetl + '/' + metlName + '.ma'
            for key, value in defaultDictAbc.items():
                self.importAbc(key)

        elif QtCore.Qt.Unchecked in checkState:
            #print '3'
            defaultDictAbc = {}
            for index in xrange(self.assetsList.count()):  # 得到每一行的lineWidget索引
                item = self.assetsList.item(index)  # 重新获取一下每一行
                state = item.checkState()  # 得到每一行的chackState的状态
                if state == QtCore.Qt.Checked:
                    lineContent = self.assetsList.item(index).text()
                    metlName = lineContent.split('.')[0]
                    defaultDictAbc[pathAbc + '/' + lineContent] = pathMetl + '/' + metlName + '.ma'
            for key, value in defaultDictAbc.items():
                self.importAbc(key)

    def inputMatl(self):
        pathAbc = self.finalPath + '/References'
        pathMetl = self.finalPath + '/Material'
        jsonAbcPath = self.jsonAbcPath
        checkState = []
        for index in xrange(self.assetsList.count()):  # 得到每一行的lineWidget索引
            item = self.assetsList.item(index)  # 重新获取一下每一行
            state = item.checkState()  # 得到每一行的chackState的状态
            checkState.append(state)
            # print state

        if QtCore.Qt.Unchecked not in checkState:
            #print '1'
            defaultDictAbc = {}
            for index in xrange(self.assetsList.count()):  # 得到每一行的lineWidget索引
                lineContent = self.assetsList.item(index).text()
                metlName = lineContent.split('.')[0]
                defaultDictAbc[pathAbc + '/' + lineContent] = pathMetl + '/' + metlName + '.ma'
            for key, value in defaultDictAbc.items():
                # self.checkMatlShape(pathMetl,metlName)
                self._maya.importMetl(value,jsonAbcPath)
            self._maya.assignMaterials(self.jsonMetlPath)
        elif QtCore.Qt.Unchecked in checkState:
            #print '3'
            defaultDictAbc = {}
            for index in xrange(self.assetsList.count()):  # 得到每一行的lineWidget索引
                item = self.assetsList.item(index)  # 重新获取一下每一行
                state = item.checkState()  # 得到每一行的chackState的状态
                if state == QtCore.Qt.Checked:
                    lineContent = self.assetsList.item(index).text()
                    metlName = lineContent.split('.')[0]
                    defaultDictAbc[pathAbc + '/' + lineContent] = pathMetl + '/' + metlName + '.ma'
            for key, value in defaultDictAbc.items():
                # self.checkMatlShape(pathMetl,metlName)
                self._maya.importMetl(value,jsonAbcPath)
            self._maya.assignMaterials(self.jsonMetlPath)

            
    def importAbc(self, path, groupOption=None, displayMode=None):
        self._cmds.loadPlugin("AbcImport")
        #self._cmds.AbcImport(path, mode=True)
        nameSpace = path.split('/')[-1].split('.')[0]
        cmd = 'file -import -type "Alembic"  -ignoreVersion -ra true -mergeNamespacesOnClash false -namespace %s -pr %s;' % ('"'+nameSpace+'"', '"' + path + '"')
        self._mel.eval(cmd)
        return True
    '''    
    def importAbc(self, path, groupOption=None, displayMode=None):
        self._cmds.loadPlugin("AbcImport")
        self._cmds.AbcImport(path, mode=True)
        return True'''
win = MainView()
win.show()     

