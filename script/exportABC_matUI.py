# -*- coding=utf-8 -*-
# Description：列出maya里所有refrence资产，可选择要导出的资产，默认是导出所有，导出的时候除了要导出每个reference的abc外还有导出对应的材质方便下一个工具再把材质给回去
import os
import json
import sys
import re

try:
    from PySide2 import QtWidgets
    from PySide2 import QtCore
    from PySide2 import QtGui
except ImportError:
    from PySide import QtGui as QtWidgets
    from PySide import QtCore
    from PySide import QtGui


class MyLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(MyLineEdit, self).__init__(parent)
        # self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            urls[0].setScheme("")
            filepath = str(urls[0].toString())[1:]
            filepath = filepath.decode('utf-8')
            self.setText(filepath)


class MainView(QtWidgets.QDialog):
    def __init__(self, parent=None):
        import maya.cmds as cmds
        import maya.mel as mel
        import pymel.core as pm

        self._pm = pm
        self._mel = mel
        self._cmds = cmds
        super(MainView, self).__init__(parent)
        self._mainUI()

    def _mainUI(self):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setStyleSheet("QListWidget{background: #5a5a5a;}")
        self.assetsList = QtWidgets.QListWidget()

        self.assetsList.setSortingEnabled(1)
        self.assetsList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.Contrast=self._cmds.ls(rf=1)
        New=[]
        for i in self.Contrast:
            try:
                self._cmds.referenceQuery(i, nodes=True)
            except RuntimeError:
                New.append(i)
        self.Contrast=list(set(self.Contrast) ^ set(New)) 
        
        for i in range(len(self.Contrast)):
            item = QtWidgets.QListWidgetItem(self.Contrast[i])
            item.setCheckState(QtCore.Qt.Checked)
            self.assetsList.addItem(item)
        
        startFrame = QtWidgets.QLabel(U"startFrame")
        self.start = QtWidgets.QLineEdit()
        endFrame = QtWidgets.QLabel(U"endFrame")
        self.end = QtWidgets.QLineEdit()
        abcOutPut = QtWidgets.QLabel(U"abc output path")
        self.abcOutputPath = MyLineEdit()
        self.setPath = QtWidgets.QPushButton(U"...")

        self.Out = QtWidgets.QPushButton(U'Out')

        self.setPath.clicked.connect(self.getPath)
        self.Out.clicked.connect(self.export)

        oneHboxLayput1 = QtWidgets.QHBoxLayout()
        oneHboxLayput1.addWidget(startFrame)
        oneHboxLayput1.addWidget(self.start)
        oneHboxLayput1.addWidget(endFrame)
        oneHboxLayput1.addWidget(self.end)
        oneHboxLayput = QtWidgets.QHBoxLayout()
        oneHboxLayput.addWidget(self.abcOutputPath)
        oneHboxLayput.addWidget(self.setPath)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.assetsList)
        mainLayout.addLayout(oneHboxLayput1)
        mainLayout.addWidget(abcOutPut)
        mainLayout.addLayout(oneHboxLayput)
        mainLayout.addWidget(self.Out)

        self.setLayout(mainLayout)

    def msg(self):
        QtWidgets.QMessageBox.about(self, "Title",  "Export Successful !!!")
    
    def getPath(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open file dialog", "/",
                                                          QtWidgets.QFileDialog.ShowDirsOnly).replace('\\','/')
        self.abcOutputPath.setText(path)

    # def is_group(self, node=None):  # 查找group
    #     # if node == None:
    #     #     node = self._cmds.ls(selection=True)[0]
    #     if self._cmds.nodeType(node) != "transform":
    #         return False
    #     children = self._cmds.listRelatives(node, c=True)
    #     if children == None:
    #         return True
    #     for c in children:
    #         try :
    #             cmds.nodeType(c)
    #         except RuntimeError:
    #             return False
    #         if self._cmds.nodeType(c) == 'joint':
    #             return True
    #         if self._cmds.nodeType(c) != 'transform':
    #             return False
    #     else:
    #         return True
    def getNameSp(self,Name):
        namespace = self._cmds.ls(Name,sns=True)
        return namespace[1]   
        
    def getOutName(self,Name):
        if ':' in Name:
            result=Name.split(':')[-1]
            return result
        else:
            return Name
    def export(self):
        M_Folder = self.newM_Folder(self.abcOutputPath.text())
        R_Folder = self.newR_Folder(self.abcOutputPath.text())
        stateL = []
        self.referencesL = []
        for index in xrange(self.assetsList.count()):  # 得到每一行的lineWidget索引
            item = self.assetsList.item(index)  # 重新获取一下每一�?
            state = item.checkState()  # 得到每一行的chackState的状�?
            stateL.append(state)

        if QtCore.Qt.CheckState.Unchecked not in stateL:  # 不存在没有勾选的
            for i in xrange(self.assetsList.count()):
                item = self.assetsList.item(i)
                itemName = item.text()
                Ref_Node = self._cmds.referenceQuery(itemName, nodes=True)
                Ref_shape = self._cmds.ls(Ref_Node, type='transform',sn=True)
                Ref_shape=list(set(Ref_shape))
                bb=[]      
                for j in Ref_shape:
                    y=self._cmds.listRelatives(j,parent=True)
                    if y!=None:
                        bb.append(j)
                Ref_shape=list(set(Ref_shape) ^ set(bb))                                     
                Ref_groups = Ref_shape
 
                self.NameSpace =self.getOutName(self.getNameSp(Ref_groups[0]))
                self.exportAbc(R_Folder + "/" + self.NameSpace + ".abc", 0, [self.start.text(), self.end.text()], Ref_groups)
                self.exportMaterialsaa(M_Folder + "/" + self.NameSpace + ".ma", removeNamespace=True,name=self.NameSpace)             
            self.getReferences()
            self._outJson(self.abcOutputPath.text() + "/", removeNamespace=True)
            print "Successful!!"
            self.msg()
        else:
            for index in xrange(self.assetsList.count()):  # 得到每一行的lineWidget索引
                item = self.assetsList.item(index)  # 重新获取一下每一�?
                state = item.checkState()  # 得到每一行的chackState的状�?
                if state == QtCore.Qt.Checked:  # 当勾选则执行
                    itemName = item.text()

                    Ref_Node = self._cmds.referenceQuery(itemName, nodes=True)
                    Ref_shape = self._cmds.ls(Ref_Node, type='transform')                                
                    bb=[]      
                    for j in Ref_shape:
                        y=self._cmds.listRelatives(j,parent=True)
                        if y!=None:
                            bb.append(j)
                    Ref_shape=list(set(Ref_shape) ^ set(bb))            
                    Ref_groups = Ref_shape

                    self.referencesL.append(itemName)
                    
                    
                    self.NameSpace =self.getOutName(self.getNameSp(Ref_groups[0]))
                    
                    self.exportAbc(R_Folder + "/" + self.NameSpace + ".abc", 0, [self.start.text(), self.end.text()], Ref_groups)
                    self.exportMaterialsaa(M_Folder + "/" + self.NameSpace + ".ma", removeNamespace=True,name=self.NameSpace)
                    

            self.getReferences()
            self._outJson(self.abcOutputPath.text() + "/", removeNamespace=True)
            print "Successful!!"
            self.msg()

    def currentFrame(self):
        return self._cmds.currentTime(query=True)

    def newM_Folder(self, path):
        if os.path.exists(path):
            if os.path.exists(path + "/Material"):
                pass
            else:
                os.makedirs(path + "/Material")
        return path + "/Material"

    def newR_Folder(self, path):
        if os.path.exists(path):
            if os.path.exists(path + "/References"):
                pass
            else:
                os.makedirs(path + "/References")
        return path + "/References"

    def getReferences(self):
        result = {}
        if len(self.referencesL) == 0:
            allRe = self.Contrast
        else:
            allRe = self.referencesL
        if allRe:
            for indexs, rn in enumerate(allRe):
                Ref_Nodes = self._cmds.referenceQuery(rn, nodes=True)
                Ref_shapes = self._cmds.ls(Ref_Nodes, type='transform')
                bb=[]      
                for j in Ref_shapes:
                    y=self._cmds.listRelatives(j,parent=True)
                    if y!=None:
                        bb.append(j)
                Ref_groups=list(set(Ref_shapes) ^ set(bb)) 
                
                refPath = self._cmds.referenceQuery(Ref_groups[0], filename=True)
                NameSpace =self.getNameSp(Ref_groups[0])        
                outName = self.getOutName(NameSpace)
                # print 'refPath:',refPath

                if "{" in refPath:
                    path = refPath[:refPath.index("{")]
                else:
                    path = refPath

                if os.path.exists(path):
                    namespace = self._cmds.referenceQuery(Ref_groups[0], namespace=True)
                else:
                    namespace = os.path.splitext(os.path.basename(path))[0]
                info = {
                    # 'node': rn,
                    'parent': '',
                    'ref_path': refPath,
                    'path': self.abcOutputPath.text(),
                    'name': outName + '.abc',
                    'namespace': NameSpace,
                    'filetype': os.path.splitext(path)[-1].replace('.', ''),
                    'node_type': 'reference',
                }               
                result[outName] = info

        if os.path.exists(self.abcOutputPath.text() + '/ExportReferences.json'):
            f = open(self.abcOutputPath.text() + '/ExportReferences.json', "r")
            model = json.load(f)
            new = model.copy()
            new.update(result)
            f.close()
            f = open(self.abcOutputPath.text() + '/ExportReferences.json', "w")
            model1 = json.dumps(new, indent=4)
            f.write(model1)
            f.close()

        else:
            f = open(self.abcOutputPath.text() + '/ExportReferences.json', "w")
            model = json.dumps(result, indent=4)
            f.write(model)
            f.close()

    def exportAbc(self, path, singleFrame=False, frameRange=[], objects=[],
                  options=['-stripNamespaces', '-uvWrite', '-worldSpace', '-dataFormat ogawa']):
        '''Exports abc cache file.'''
        # AbcExport -j "-frameRange 1 34 -dataFormat ogawa -root |camera:tst_001_01 -root |dog:dog -file C:/Users/nian/Documents/maya/projects/default/cache/alembic/test.abc";
        self._cmds.loadPlugin("AbcExport")

        # Get arguments
        if singleFrame:
            frameRange = [self.currentFrame(), self.currentFrame()]
            frameRange = [1, 1]
        elif frameRange == None:
            frameRange = self.frameRange()

        args = '-frameRange %s %s ' % (frameRange[0], frameRange[1])

        if type(options) in (list, tuple):
            options = ' '.join(options)

        if options:
            args += options + ' '

        for obj in objects:
            args += '-root %s ' % obj

        args += '-file %s' % path

        # Get cmd
        cmd = 'AbcExport -j "%s";' % args

        self._pm.mel.eval(cmd)

    def select(self, path, replace=True, add=False, noExpand=False):
        if path and type(path) in (str, unicode, list):
            self._cmds.select(path, replace=replace, add=add,
                              noExpand=noExpand)

    def removeStringNamespace(self, name):
        '''
        Removes namespaces of the name.
        For instance:
            name: |dog:dog|dog:base|dog:box|dog:boxShape
            return: |dog|base|box|boxShape

            name: |dog:box.f[10:13]
            return: |box.f[10:13]
        '''
        splitter = '|'

        pat = re.compile('[a-zA-Z0-9]+\.f\[\d+:\d+\]')

        split = name.split(splitter)
        temp = []
        for i in split:
            if i:
                # i: dog:box.f[10:13]
                find = pat.findall(i)
                if find:
                    new = find[-1]

                # Keep the last item
                else:
                    new = i.split(':')[-1]

            else:
                new = i

            temp.append(new)

        return splitter.join(temp)

    def getMaterials(self, name='', removeNamespace=False):
        '''
        Gets materials to a dictionary of which keys are materials and values are
        shapes and faces.
        Example of the returned dictionary:
            {
                'metal': {
                    'box': ['box.face[1-29]', 'box.face[33]']  ,
                    'sphere': [],
                }
            }
        '''
        shapList = []
        materDic = {}

        all = self._cmds.ls(materials=True)

        try:
            all.remove("lambert1")
        except:
            pass

        try:
            all.remove("particleCloud1")
        except:
            pass

        for i in all:
            shad = self._cmds.listConnections(i, type="shadingEngine")
            if name != '':
                #print name
                #print shad
                if shad != None:
                    if name == self.getOutName(self.getNameSp(shad[0])):
                        meshlist = self._cmds.sets(shad[0], int=shad[0])
                        # print meshlist
                        if meshlist != []:
                            materDic[shad[0]] = meshlist
            else:
                if shad != None:
                    meshlist = self._cmds.sets(shad[0], int=shad[0])
                    # print meshlist
                    if meshlist != []:
                        materDic[shad[0]] = meshlist
        return materDic
    def filepath(self):
        return self._cmds.file(query=True, location=True)

    def fileType(self, path=''):
        if not path:
            path = self.filepath()

        exts = {
            'ma': 'mayaAscii',
            'mb': 'mayaBinary',
        }
        ext = os.path.splitext(path)[1].replace('.', '')
        if exts.has_key(ext):
            typ = exts[ext]
        else:
            typ = ''
        return typ

    def exportSelected(self, path):
        typ = self.fileType(path)

        if typ:
            self._cmds.file(path, force=True, exportSelected=True, typ=typ)
        else:
            #print path
            self._cmds.file(path, force=True, exportSelected=True)

    def exportMaterialsaa(self, path, generateMapping=True, mappingFilename='ExportMaterial',
                          removeNamespace=False, name=''):
        '''Exports all materials to a new ma file.'''
        materials = self.getMaterials(name, removeNamespace=removeNamespace)
        if materials!={}:
            self._cmds.select(materials.keys(), replace=True, noExpand=True)
            self.exportSelected(path)
            return materials.keys()
        else:
            pass
    def removeStringNamespaceV1(self,name):
        '''
        delete the first namespace
        
        For instance:
            name: |three:two:group|three:two:group5|three:two:group4
            return: |two:group|two:group5|two:group4

            name: |two:dog:box.f[10:13]
            return: |dog:box.f[10:13]
        
        '''
        splitter = '|'

        pat = re.compile('[a-zA-Z0-9]+\.f\[\d+:\d+\]')

        split = name.split(splitter)
        
        #print split
        temp = []
        for i in split:
            if i:
                # i: dog:box.f[10:13]
                find = pat.findall(i)
                if find:
                    new = find[-1]
                # Keep the last item
                else:
                    judge=split[-1].split(':')
                    if len(judge)>2:                  
                        new = i.split(':')[1]+':'+i.split(':')[-1]
                    else:
                        #new = i.split(':')[-1]
                        new = i
            else:
                new = i
            temp.append(new)
        return splitter.join(temp)
        
    def outJson(self, removeNamespace=False):
        shapList = []
        materDic = {}
        all = self._cmds.ls(materials=True)
        try:
            all.remove("lambert1")
        except:
            pass
        try:
            all.remove("particleCloud1")
        except:
            pass
        for i in all:
            shad = self._cmds.listConnections(i, type="shadingEngine")
            if shad != None:
                meshlist = self._cmds.sets(shad[0], int=shad[0])
                if meshlist != []:
                    materDic[shad[0]] = meshlist

        for key in materDic.keys():
            for i in materDic[key]:
                if ".f[" in i:
                    shape = self._cmds.listHistory(i, q=1, historyAttr=True)[0].replace(".inMesh", "")
                    shapList.append(shape)
                else:
                    shapList.append(i)
        shapList = list(set(shapList))
       
        for key in materDic.keys():
            shapeDic = {}
            gMainProgressBar = self._mel.eval('$tmp = $gMainProgressBar')
            self._cmds.progressBar( gMainProgressBar,
                            edit=True,
                            beginProgress=True,
                            isInterruptable=True,
                            status='Exporting Material...',
                            maxValue=len(shapList) )
            for st in shapList:
                A = []
                for i in materDic[key]:
                    if ".f[" in i:
                        shape = self._cmds.listHistory(i, q=1, historyAttr=True)[0].replace(".inMesh", "")
                        root = self._pm.PyNode(shape)
                        mesh = root.listRelatives(ap=True)
                        newH = mesh[0].longName()
                        if "|" in shape:
                            newSha = newH + "|" + shape.split("|")[-1]
                        else:
                            newSha = newH + "|" + shape
                        if shape == st:
                            A.append("|" + i)
                            shapeDic[newSha] = A
                    else:
                        root = self._pm.PyNode(i)
                        mesh = root.listRelatives(ap=True)
                        newH = mesh[0].longName()

                        if "|" in i:
                            newSha = newH + "|" + i.split("|")[-1]
                        else:
                            newSha = newH + "|" + i
                        shapeDic[newSha] = []
                if self._cmds.progressBar(gMainProgressBar, query=True, isCancelled=True ) :
                    break
                self._cmds.progressBar(gMainProgressBar, edit=True, step=1) 
            materDic[key] = shapeDic
            self._cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        result = {}
        if removeNamespace:
            for mat in materDic.keys():
                result[mat] = {}
                for shape in materDic[mat].keys():
                    # print shape
                    #print shape
                    newShape = self.removeStringNamespaceV1(shape)
                    #print newShape
                    result[mat][newShape] = []
                    for i in range(len(materDic[mat][shape])):
                        value = materDic[mat][shape][i]
                        newValue = self.removeStringNamespaceV1(value)
                        result[mat][newShape].append(newValue)
        return result

    def _outJson(self, path, mappingFilename='ExportMaterial', generateMapping=True, removeNamespace=False):
        JSonWrite = self.outJson(removeNamespace=removeNamespace)
        if generateMapping:
            txt = json.dumps(JSonWrite, indent=4)
            root = os.path.dirname(path)
            jsonPath = '%s/%s.json' % (root, mappingFilename)
            f = open(jsonPath, 'w')
            f.write(txt)
            f.close()
win = MainView()
win.show()