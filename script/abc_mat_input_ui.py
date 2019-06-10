# coding=utf-8
# Description������һ�����ߵ�����abc�Լ����ʵ��벢�ҿ�ѡ���Ƿ��벢�������


#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Description�����ڲ��Ե�api

import os

class Maya(object):
    def __init__(self):
        import maya.cmds as cmds
        import maya.mel as mel
        import os
        import json
        import re

        self._cmds = cmds
        self._mel = mel
        self._os = os
        self._json = json
        self._re = re



    def importMetl(self, value,jsonAbcPath):
        if self._os.path.exists(value):
            with open(jsonAbcPath) as json_file:
                dataJson = self._json.load(json_file)
                firstAllMetls = self._cmds.ls(mat=1)#�õ��տ�ʼ�����ڵĲ���
                nameSpace = value.split('/')[-1].split('.')[0]
                
                cmd = 'file -import -type "mayaAscii"  -ignoreVersion -ra true -mergeNamespacesOnClash false -namespace %s -options "v=0;p=17;f=0"  -pr %s;' % ('"'+nameSpace+'"','"' + value + '"')
                self._mel.eval(cmd)
                secondAllMetls = self._cmds.ls(mat=1)#�õ�������ʺ󳡾��ڵĲ���

                subtractaMetls = list(set(firstAllMetls)^set(secondAllMetls))#�ò�õ��յ���Ĳ���

                for a in subtractaMetls:



                    maNamespace = value.split('/')[-1].split('.')[0]#�õ�ma�ļ������ƣ�ȥ��ma��׺
                    #print maNamespace
                    metlNamespace = a.split(':')[0]#�õ�ÿ�����ʵ������ռ�
                    #print metlNamespace


                    #print dataJson[maNamespace]['namespace']
                    space = dataJson[maNamespace]['namespace']

                    # �жϣ���Ϊ��ͬ�����޸ģ���ͬ���޸�
                    if metlNamespace==maNamespace:
                        pass
                    else:

                        sgName = self._cmds.listConnections(a, type="shadingEngine")#�õ�sg�ڵ�����
                        if sgName!=None:
                        #print sgName
                            newNamespace = space+':'+sgName[0].split(':')[-1]
                            #print newNamespace

                            nameSpace=self._cmds.namespace(add=newNamespace)#������µ������ռ�
                            self._cmds.namespace(rm=nameSpace)#��ɾ����������ռ䣬��ֹ��׺�������
                            self._cmds.rename(sgName[0], nameSpace)#����sg�ڵ�����Ϊ�µ������ռ�
                        elif sgName==None:
                            pass
        else:
            return False
    def addObjectNamespace(self, name, namespace):
        '''
        Adds namespaces to the name.
        For instance:
            name: |dog|base|box|boxShape
            namespace: dog
            return: |dog:dog|dog:base|dog:box|dog:boxShape

            name: |box.f[10:13]
            namespace: dog
            return: |dog:box.f[10:13]
        '''
        splitter = '|'

        pat = self._re.compile('[a-zA-Z0-9]+\.f\[\d+:\d+\]')

        split = name.split(splitter)
        temp = []
        for i in split:
            new = i
            if i and namespace:
                new = ':'.join([namespace, i])

            temp.append(new)

        return splitter.join(temp)

    def parseConfigs(self, configs):
        if type(configs) in (str, unicode) and os.path.isfile(configs):
            f = open(configs, 'r')
            t = f.read()
            f.close()
            configs = self._json.loads(t)

        return configs

    def assignMaterials(self, mapping, geoNamespace='', matNamespace=''):
        '''
        mapping is a dictionary or a file with geometry and materials mapping.

        Example of mapping:
            {
                "blinn1SG": {
                    "|dog|base|box|boxShape": [
                        "|box.f[0:5]",
                        "|box.f[7:9]"
                    ]
                },
                "blinn2SG": {
                    "|dog|base|pCone1|pConeShape1": []
                }
            }

            {
                "blinn1SG": {
                    "|dog|base|body|bodyShape": [
                        "|body.f[200:359]",
                        "|body.f[380:399]"
                    ]
                },
                "blinn2SG": {
                    "|dog|base|body|bodyShape": [
                        "|body.f[0:199]",
                        "|body.f[360:379]"
                    ]
                }
            }
        '''
        #print mapping
        mapping = self.parseConfigs(mapping)
        #print mapping
        if not type(mapping) == dict:
           # print mapping
            print 'type mapping is not dict'
            return

        for mat in mapping.keys():
            for shape in mapping[mat].keys():
                # The material is assigned to object faces
                if mapping[mat][shape]:
                    # shape: |dog|base|body|bodyShape
                    faces = []
                    for i in mapping[mat][shape]:
                        # i: |body.f[200:359]
                        f = i.split('.')[-1]
                        # f: f[200:359]
                        newI = '%s.%s' % (shape, f)

                        new = self.addObjectNamespace(newI, geoNamespace)
                        # new: |dog:dog|dog:base|dog:body|dog:bodyShape.f[200:359]
                        new = new.lstrip('|')

                        faces.append(new)

                    faces = ' '.join(faces)

                # The material is assigned to the object
                else:
                    faces = ''

                # Source is the material
                src = self.addObjectNamespace(mat, matNamespace)
                # Destination is the geometry
                dst = "%s.instObjGroups[0]" % shape
                dst = self.addObjectNamespace(dst, geoNamespace)
                dst = dst.lstrip('|')

                kwargs = {
                    'source': src,
                    'destination': dst,
                    'connectToExisting': True,
                }
                if faces:
                    kwargs['navigatorDecisionString'] = faces

                try:
                    self._cmds.defaultNavigation(**kwargs)
                except:
                    pass
