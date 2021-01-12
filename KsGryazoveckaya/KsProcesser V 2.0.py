from builtins import input

from traits.tests.check_timing import delegate_value

import functions
import pandas as pd
import os
import time
from tqdm import tqdm
import re
import numpy as np
from multiprocessing.dummy import Pool as ThreadPool
from openpyxl import load_workbook
import datetime
import os


# Dir = 'E:\\КС Грязовецкая\\Модель проектного института\\AllExcels\\'
# Dir = 'D:\\CNSSoft\\КС Грязовецкая\\Новая 3D модель\\Objects\\AllExcel\\'
Dir = 'D:\\CNSSoft\\КС Грязовецкая\\3D Модель 23112020_FIXED_2\\'
rawDir = Dir + 'rawExcel\\'
processedDir = Dir + 'processedExcel\\'
importerFolder = 'D:\\CNSSoft\\netcoreapp3.0\\'
ExcelFolder = 'D:\\CNSSoft\\netcoreapp3.0\\Excel\\'

idParentEntity = 29997296


tempMass = []

eCount = 1
totalExcelCount = len(list(functions.FileNames(folder=rawDir, type='xlsx')))


class Attribute:
    name = ''
    guid = ''
    type = ''

    def __init__(self,name,guid,type):
        self.name = name
        self.guid = guid
        self.type = type

    def print(self):
        print(self.name, ':',self.guid,' ',self.type)

    def __iter__(self):
        return self.name

    def __getitem__(self, item):
        return self.name

def takeAttrFromExcel(file,sheet):
    Wb = load_workbook(file)
    ws = Wb.worksheets[sheet]
    list = []
    for row in ws.rows:
        list.append(Attribute(row[0].value,row[1].value,row[2].value))
    Wb.close()
    return list


attrs = takeAttrFromExcel('AttrList.xlsx', 3)
attrSet = set()
doubleAttrSet = set()
for i in attrs:
    attrSet.add(i.name)
    if i.type == 2:
        doubleAttrSet.add(i.name)
# print(doubleAttrSet)
attrDict = functions.ParseExcel('dict', 'AttrList.xlsx', 3)


df1 = pd.DataFrame(columns=attrSet)

classes = functions.ParseExcel(type='dict', file='Классы.xlsx', sheet=1)
classGuid = functions.ParseExcel(type='dict', file='Классы.xlsx', sheet=0)


cyphers = functions.ParseExcel(type = 'dict',file='D:\\CNSSoft\\Report.xlsx',sheet=0)


def process(file):
    # print(file)
    xl = pd.ExcelFile(rawDir + file)
    df = xl.parse('MySheet')
    # df = pd.read_csv(rawDir + file,delimiter=';')
    # print(df)
    # дроп ненужных колонок с атрибутами
    for i in df.columns:
        if i not in attrSet:
            df = df.drop(i, axis=1)

    # удаление типов и значений в скобках
    # df = df.replace(to_replace=r'.+:', value='', regex=True)
    df = df.replace(to_replace=r'\(.+\)', value='', regex=True)



    for ind in df.index:
        # замена значений group и mesh
        try:
            name = df['ElementName'][ind]
            if (name == 'Group' or name == 'Mesh') and not pd.isnull(df.at[ind, 'Имя_0']):
                df.at[ind, 'ElementName'] = df.at[ind, 'Имя_0']
        except:
            pass
        # regexp на double атрибуты
        for col in df.columns[5:]:
            if col in doubleAttrSet:
                try:
                    df.at[ind, col] = re.search('([0-9]*\,[0-9]+)|(\d+)', str(df.at[ind, col])).group(0)
                except AttributeError:
                    continue

    # for ind in df.index:


    # удаление ненужных строк
    indexNames = df[df['ElementName'] == 'Group'].index
    indexNames1 = df[df['ElementName'] == 'Mesh'].index
    df.drop(indexNames, inplace=True)
    df.drop(indexNames1, inplace=True)

    # удаление Имени типа
    try:
        df = df.drop('Имя_0', axis=1)
    except:
        print('Имя_0 отсутствует:',file)

    # поиск классов всеми доступными способами
    df['Class guid'] = df.astype({'Class guid': 'object'})

    extDMass = ["Диаметр",
                "Диаметр заглушки",
                "Диаметр задвижки",
                "Диаметр переходного тройника",
                "Диаметр стыка",
                "Диаметр тройника",
                "Диаметр трубопровода",
                "Диаметр трубы"]

    for ind in df.index:
        ModelFlag = False
        if df['IdTree'][ind] in list(df['IdTreeParent']):
            ModelFlag = True

        if ModelFlag == True:
            df.at[ind, 'Class guid'] = '3D Модель'
        else:
            name = df['ElementName'][ind]
            for cl in classes.keys():
                if str(name).find(cl) != -1:
                    df.at[ind, 'Class guid'] = classes[cl]
                    break
        # переименовывание классов
        if pd.isnull(df['Class guid'][ind]) == True:
            df.at[ind, 'Class guid'] = '3D Модель'
        # замена классов на шифры
        df.at[ind, 'Class guid'] = classGuid[df['Class guid'][ind]]

        if 'Внешний диаметр' in df.columns.values:
            if pd.isnull(df['Внешний диаметр'][ind]):
                for dim in extDMass:
                    try:
                        if not pd.isnull(df[dim][ind]):
                            df.at[ind,'Внешний диаметр'] = df[dim][ind]
                            break
                    except:
                        continue
        if 'Внутренний диаметр' in df.columns.values:
            if pd.isnull(df['Внутренний диаметр'][ind]):
                try:
                    if not pd.isnull(df['Внутренний диаметр'][ind]):
                        df.at[ind,'Внутренний диаметр'] = df['Номинальный диаметр'][ind]
                except:
                    pass


    # try:
    # # прокидка шифра
    #     cypher = df['ElementName'][0]
    #     cypherCol = [cyphers[cypher] for i in range(len(df.index))]
    #     df.insert(len(df.columns), 'Шифр элемента', cypherCol)
    # except KeyError:
    #     print(df['ElementName'][0])


    # еботня с диаметрами
    # постановка внешнего диаметра

    # print(df.columns.values)
    # for ind in df.index:



    #удаление атрибутов внешнего диаметра
    for dim in extDMass:
        try:
            df = df.drop(dim, axis=1)
        except:
            continue

    if 'Номинальный диаметр' in df.columns.values:
        df.drop('Номинальный диаметр',axis=1)


    # перетаскивание колонки ElementId в конец
    cols = list(df.columns.values)
    cols.pop(cols.index('ElementId'))
    df = df[cols + ['ElementId']]

    # переименовывание атрибутов
    df.rename(columns=lambda x: attrDict[x], inplace=True)

    # установка idParentEntity
    df.at[0, 'IdParentEntity'] = idParentEntity
    # сохранение
    df.to_excel(processedDir + 'processed' + file, index=False)
    # df.to_excel(processedDir + 'processed' + '000_Decode_entitites_1.xlsx', index=False)

    today = datetime.datetime.today()
    global eCount
    print(str(eCount) + '/' + str(totalExcelCount) + today.strftime(" %H:%M:%S"),' Processed - ', file)
    eCount +=1

Process = False
Import = True

if Process == True:
    start = time.time()
    files = functions.FileNames(rawDir, 'xlsx')
    tempFiles = []
    pool = ThreadPool(4)
    results = pool.map(process, files)
    pool.close()
    pool.join()
    print(time.time() - start)


# process('Part5_Decode_entitites_1.csv')

if Import == True:
    for i in functions.FileNames(folder=processedDir, type='xlsx'):
        functions.moveAndRename(processedDir, ExcelFolder, i, 'InsertEntities.xlsx')
        functions.callImporter()
        functions.moveAndRename(importerFolder,importerFolder + '\\logs\\','importer.log',i[:i.find('.xlsx')] + '.log')

        file = open(importerFolder + 'importer.log', encoding='utf-8').readlines()
        for j in enumerate(iter(file)):
            if 'ERROR' in j[1]:
                with open(importerFolder + 'importerLogs.txt', 'a') as logs:
                        logs.write(i + ';' + j[1])
        os.remove(importerFolder + 'importer.log')

