import shutil
import os
import subprocess
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import requests
import json
from datetime import datetime
from dateutil import tz

# with open("settings.json", "r") as read_file:
#     data1 = json.load(read_file)





URL = 'https://gpinvest.cnssoft.ru/'




class PortalAttribute:
    def __init__(self, id, name, type, system):
        self.id = id
        self.name = name
        self.type = type
        self.system = system


class ObjMass:
    def __init__(self):
        self.idDict = {}
        self.nameDict = {}
        self.count = 0
        self.attrMass = []

    def append(self, attr):
        self.attrMass.append(PortalAttribute(attr['id'], attr['name'], attr['type'], attr['system']))

    def getIdNameDict(self):
        for i in self.attrMass:
            self.idDict[i.id] = i.name

        return self.idDict

    def getNameIdDict(self):
        for i in self.attrMass:
            self.nameDict[i.name] = i.id
            # if i.type == 6:
            #     self.nameDict[i.name] = 'a_dtm_guid_' + i.id
            # elif i.type in [2, 9, 1]:
            #     self.nameDict[i.name] = 'a_guid_' + i.id
        return self.nameDict

    def getNameClassDict(self):
        nameDict = {}
        for i in self.attrMass:
            nameDict[i.name] = i
        return nameDict


class PortalClass:
    def __init__(self, id, name,attrs):
        self.id = id
        self.name = name
        self.attrs = attrs


class ClassMass:
    def __init__(self):
        self.idDict = {}
        self.nameDict = {}
        self.count = 0
        self.classMass = []
        self.idAttrDict = {}

    def append(self, pClass,pClassAttrs):
        self.classMass.append(PortalClass(pClass['id'], pClass['name'],attrs=pClassAttrs))

    def getIdNameDict(self):
        for i in self.classMass:
            self.idDict[i.id] = i.name
        return self.idDict

    def getNameIdDict(self):
        for i in self.classMass:
            self.nameDict[i.name] = i.id
        return self.nameDict

    def getIdAttrsDict(self):
        for i in self.classMass:
            self.idAttrDict[i.id] = i.attrs
        return self.idAttrDict


def login(url):
    client = BackendApplicationClient(client_id=CLIENT_ID)
    oauth = OAuth2Session(client=client)
    # print(url + 'connect/token')
    token = oauth.fetch_token(token_url=url + 'connect/token', client_id=CLIENT_ID,
                              client_secret=CLIENT_SECRET)
    # полученный ключ
    key = token['access_token']
    # print(key)
    return key


def sendReqTreeData(url,node, key,verify):
    reqData = requests.get(url=url + 'api/v1/entities/trees/main/nodes/' + str(node) + '/children',
                           params={'Take': 1000},
                           verify = verify,
                           headers={
                               'Content-type': 'application/json',
                               'Authorization': 'Bearer ' + key
                           },
                           )

    data = json.loads(reqData.content)
    return data


def getAttrsFromSite(url, key,verify):
    reqData = requests.get(url=url + 'api/v1/metadata/attributes',
                           verify = verify,
                           headers={
                               'Content-type': 'application/json',
                               'Authorization': 'Bearer ' + key
                           },
                           )

    data = json.loads(reqData.content)

    attrs = ObjMass()
    for i in data:
        attrs.append(attr=i)
    return attrs


def getRefsFromSite(url, key,verify):
    reqData = requests.get(url=url + 'api/v1/metadata/references',
                           verify = verify,
                           headers={
                               'Content-type': 'application/json',
                               'Authorization': 'Bearer ' + key
                           },
                           )

    data = json.loads(reqData.content)
    # print(data)
    refs = ObjMass()
    for i in data:
        refs.append(attr=i)
    return refs


def getClassesFromSite(url, key,verify):
    reqData = requests.get(url=url + 'api/v1/metadata/classes',
                           verify=verify,
                           headers={
                               'Content-type': 'application/json',
                               'Authorization': 'Bearer ' + key
                           }
                           )

    data = json.loads(reqData.content)
    classes = ClassMass()

    for i in data:
        classAttrs = [j for j in i['attributes']]
        classes.append(pClass=i,pClassAttrs=classAttrs)

    return classes


def getEntityAttrs(url, entity, attrs, key,verify):
    attrsLoc = []
    for i in range(len(attrs)):
        attrsLoc.append('attrs=' + str(attrs[i]))
    reqData = requests.get(url=url + 'api/v1/entities/' + str(entity),
                           verify=verify,
                           params='&'.join(attrsLoc),
                           headers={
                               'Content-type': 'application/json',
                               'Authorization': 'Bearer ' + key
                           }
                           )
    data = json.loads(reqData.content)
    return data


def dateToTimezone(date):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return central


def moveAndRename(srcFolder, destFolder, name, rename):
    shutil.copyfile(srcFolder + '\\' + name, destFolder + '\\' + rename)


def callImporter(importerFolder):
    os.chdir(importerFolder)
    proc = subprocess.call('Importer.exe')


def Query(url,node, key, classes, attrs,references, skip, take,verify,removeGP):
    classMass = [{"class": {"eq": i}} for i in classes]
    attrMass = ["attr." + i for i in attrs]
    for i in references:
        attrMass.append('ref.' + i)
    # print(attrMass)
    if removeGP:
        query = {
            "where":
                {
                    "and":
                        [
                            {"or": classMass} if len(classMass) > 1 else classMass[0],
                            {
                                "ancestors":
                                    {"exists": {"id": {"eq": node}}}
                            },
                            {"attr.ba114a4e-a3aa-4522-be52-96f0ed52bcf4": {"ne": "0010.001.004.Р.0001.113.0001.0000.001-ГТ1"}},
                            {"attr.ba114a4e-a3aa-4522-be52-96f0ed52bcf4": {"ne": "0010.001.004.Р.0001.113.0001.0000.001-ГР1"}},
                            {"attr.ba114a4e-a3aa-4522-be52-96f0ed52bcf4": {"ne": "0010.001.004.Р.0001.113.0001.0000.001-ГТ4"}}
                        ]
                },
            "select": attrMass  # выбираемые атрибуты
        }
    else:
        query = {
            "where":
                {
                    "and":
                        [
                            {"or": classMass} if len(classMass) > 1 else classMass[0],
                            {
                                "ancestors":
                                    {"exists": {"id": {"eq": node}}}
                            }
                        ]
                },
            "select": attrMass  # выбираемые атрибуты
        }

    reqData = requests.post(url=url + 'api/v1/entities/query',
                            params={
                                'skip': skip,
                                'take': take
                            },
                            verify=verify,
                            headers={
                                'Content-type': 'application/json',
                                'Authorization': 'Bearer ' + key,
                                'X-HTTP-Method-Override': 'Get'
                            },
                            json=query
                            )

    # print(reqData.url)
    # print(reqData)
    # print(reqData.content)
    data = json.loads(reqData.content)
    # print(data)
    return data
