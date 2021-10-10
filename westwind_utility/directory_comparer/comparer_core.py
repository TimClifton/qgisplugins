
import os
from qgis.core import *



class DirectoryComparerCore:


    def __init__(self, originalDirectory, comparisonDirectory):

        self.originalDirectory = originalDirectory
        self.comparisonDirectory = comparisonDirectory


    
    def compareFiles(self):

        outPutText = []


        for oRoots, oDirs, oFiles in os.walk(self.originalDirectory):

            for oFile in oFiles:

                filename, fileExtension = os.path.splitext(oFile)

                if fileExtension == '.shp':

                    oFilePath = oRoots +'\\'+ oFile
                    oComparePath = oFilePath.replace(self.originalDirectory,'')

                    matchFound = False
                    matchResult = self.findMatchingFile(oRoots,oFile)
                    if matchResult:
                        cFile = matchResult[0]
                        cRoots = matchResult[1]
                        oComparePath = matchResult[2]
                        cComparePath = matchResult[3]
                        matchFound = True

                    
                    if matchFound:

                        cFilePath = cRoots +'\\'+ cFile

                        orginalVector = QgsVectorLayer(oFilePath,oFile)
                        comparisonVector = QgsVectorLayer(cFilePath,cFile)

                        orignalFields = orginalVector.fields().names()
                        comparisonFields = comparisonVector.fields().names()

                        if orignalFields != comparisonFields:
                            outPutText.append('\n')

                            outPutText.append(f'{oComparePath} has different attributes ({cComparePath}). Checking order...')

                            if orignalFields.sort() == comparisonFields.sort():
                                outPutText.append('Fields are the same though order is different')
                                outPutText.append(f'\n{orignalFields}')
                                outPutText.append(f'\n{comparisonFields}')

                            else:
                                outPutText.append('Fields are different!!')
                                outPutText.append(f'\n{orignalFields}')
                                outPutText.append(f'\n{comparisonFields}')

                        #check the feature count is the same

                        orginalCount = orginalVector.featureCount()
                        comparisonCount = comparisonVector.featureCount()

                        if orginalCount != comparisonCount:
                            outPutText.append('\n')

                            outPutText.append(f'{oComparePath} has different feature count. {orginalCount} vs {comparisonCount}')

                    else: 

                        #print('notFound')

                        outPutText.append(f'{oComparePath} not found!!')

                        outPutText.append('\n')

                    

                        
                        
        

        return outPutText

    
    def findMatchingFile(self,oRoots,oFile):

        oFilePath = oRoots +'\\'+ oFile
        oComparePath = oFilePath.replace(self.originalDirectory,'')
        #print(oComparePath)


        for cRoots, cDirs, cFiles in os.walk(self.comparisonDirectory):

            for cFile in cFiles:

                cFilePath = cRoots +'\\'+ cFile
                cComparePath = cFilePath.replace(self.comparisonDirectory,'')

                if oComparePath == cComparePath:

                    return [cFile,cRoots,oComparePath,cComparePath]
