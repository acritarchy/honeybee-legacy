# This is the heart of the Honeybee
# By Mostapha Sadeghipour Roudsari
# Sadeghipour@gmail.com
# Honeybee started by Mostapha Sadeghipour Roudsari is licensed
# under a Creative Commons Attribution-ShareAlike 3.0 Unported License.

"""
This component carries all of Honeybee's main classes. Other components refer to these
classes to run the studies. Therefore, you need to let her fly before running the studies so the
classes will be copied to Rhinos shared space. So let her fly!
-
Honeybee started by Mostapha Sadeghipour Roudsari is licensed
under a Creative Commons Attribution-ShareAlike 3.0 Unported License.
Based on a work at https://github.com/mostaphaRoudsari/Honeybee.
-
Check this link for more information about the license:
http://creativecommons.org/licenses/by-sa/3.0/deed.en_US
-
Source code is available at:
https://github.com/mostaphaRoudsari/Honeybee
-
Provided by Honeybee 0.0.53
    
    Args:
        letItFly: Set Boolean to True to let the Honeybee fly!
    Returns:
        report: Current Honeybee mood!!!
"""

ghenv.Component.Name = "Honeybee_Honeybee"
ghenv.Component.NickName = 'Honeybee'
ghenv.Component.Message = 'VER 0.0.53\nJUL_24_2014'
ghenv.Component.Category = "Honeybee"
ghenv.Component.SubCategory = "00 | Honeybee"
try: ghenv.Component.AdditionalHelpFromDocStrings = "1"
except: pass



import rhinoscriptsyntax as rs
import Rhino as rc
import scriptcontext as sc
from clr import AddReference
AddReference('Grasshopper')
import Grasshopper.Kernel as gh
import math
import shutil
import sys
import os
import System.Threading.Tasks as tasks
import System
import time
from itertools import chain
import datetime
import json
import copy
import urllib
PI = math.pi

rc.Runtime.HostUtils.DisplayOleAlerts(False)

class CheckIn():
    
    def __init__(self):
        #set up default pass
        if os.path.exists("c:\\ladybug\\") and os.access(os.path.dirname("c:\\ladybug\\"), os.F_OK):
            # folder already exists so it is all fine
            sc.sticky["Honeybee_DefaultFolder"] = "c:\\ladybug\\"
        elif os.access(os.path.dirname("c:\\"), os.F_OK):
            #the folder does not exists but write privileges are given so it is fine
            sc.sticky["Honeybee_DefaultFolder"] = "c:\\ladybug\\"
        else:
            # let's use the user folder
            sc.sticky["Honeybee_DefaultFolder"] = os.path.join("C:\\Users\\", os.getenv("USERNAME"), "AppData\\Roaming\\Ladybug\\")
    
    def getComponentVersion(self):
        monthDict = {'JAN':'01', 'FEB':'02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06',
                     'JUL':'07', 'AUG':'08', 'SEP':'09', 'OCT':'10', 'NOV':'11', 'DEC':'12'}        
        # convert component version to standard versioning
        ver, verDate = ghenv.Component.Message.split("\n")
        ver = ver.split(" ")[1].strip()
        month, day, year = verDate.split("_")
        month = monthDict[month.upper()]
        version = ".".join([year, month, day, ver])
        return version
        
    def isNewerVersionAvailable(self, currentVersion, availableVersion):
        # print int(availableVersion.replace(".", "")), int(currentVersion.replace(".", ""))
        return int(availableVersion.replace(".", "")) > int(currentVersion.replace(".", ""))
    
    def checkForUpdates(self, LB= True, HB= True, OpenStudio = True, template = True):
        
        url = "https://dl.dropboxusercontent.com/u/16228160/honeybee/versions.txt"
        webFile = urllib.urlopen(url)
        versions= eval(webFile.read())
        webFile.close()
        
        if LB:
            ladybugVersion = versions['Ladybug']
            currentLadybugVersion = self.getComponentVersion() # I assume that this function will be called inside Ladybug_ladybug Component
            if self.isNewerVersionAvailable(currentLadybugVersion, ladybugVersion):
                msg = "There is a newer version of Ladybug available to download! " + \
                      "We strongly recommend you to download the newer version from Food4Rhino: " + \
                      "http://www.food4rhino.com/project/ladybug-honeybee"
                print msg
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
        if HB:
            honeybeeVersion = versions['Honeybee']
            currentHoneybeeVersion = self.getComponentVersion() # I assume that this function will be called inside Honeybee_Honeybee Component
            if self.isNewerVersionAvailable(currentHoneybeeVersion, honeybeeVersion):
                msg = "There is a newer version of Honeybee available to download! " + \
                      "We strongly recommend you to download the newer version from Food4Rhino: " + \
                      "http://www.food4rhino.com/project/ladybug-honeybee"
                print msg
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
            
        if OpenStudio:
            # This should be called inside OpenStudio component which means Honeybee is already flying
            # check if the version file exist
            openStudioLibFolder = os.path.join(sc.sticky["Honeybee_DefaultFolder"], "OpenStudio")
            versionFile = os.path.join(openStudioLibFolder, "osversion.txt")
            isNewerOSAvailable= False
            if not os.path.isfile(versionFile):
                isNewerOSAvailable= True
            else:
                # read the file
                with open(versionFile) as verFile:
                    currentOSVersion= eval(verFile.read())['version']
            
            OSVersion = versions['OpenStudio']
            
            if isNewerOSAvailable or self.isNewerVersionAvailable(currentOSVersion, OSVersion):
                sc.sticky["isNewerOSAvailable"] = True
            else:
                sc.sticky["isNewerOSAvailable"] = False
                
        if template:
            honeybeeDefaultFolder = sc.sticky["Honeybee_DefaultFolder"]
            templateFile = os.path.join(honeybeeDefaultFolder, 'OpenStudioMasterTemplate.idf')
            
            # check file doesn't exist then it should be downloaded
            if not os.path.isfile(templateFile):
                return True
            
            # find the version
            try:
                with open(templateFile) as tempFile:
                    currentTemplateVersion = eval(tempFile.readline().split("!")[-1].strip())["version"]
            except Exception, e:
                return True
            
            # finally if the file exist and already has a version, compare the versions
            templateVersion = versions['Template']
            return self.isNewerVersionAvailable(currentTemplateVersion, templateVersion)
        

checkIn = CheckIn()


class hb_findFolders():
    
    def __init__(self):
        self.RADPath, self.RADFile = self.which('rad.exe')
        self.EPPath, self.EPFile = self.which('EnergyPlus.exe')
        self.DSPath, self.DSFile = self.which('gen_dc.exe')
        
    
    def which(self, program):
        """
        Check for path. Modified from this link:
        http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
        """
        def is_exe(fpath):
            #print fpath
            #if fpath.upper().find("EnergyPlus") > 0:
            #    print fpath
            # Avoid Radiance and Daysim that comes with DIVA as it has a different
            # structure which doesn't match the standard Daysim
            if fpath.upper().find("DIVA")<0:
                # if the user has DIVA installed the component may find DIVA version
                # of RADIANCE and DAYISM which can cause issues because of the different
                # structure of folders in DIVA
                return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
            
            else:
                return False
                
        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return path, exe_file
        return None, None

class hb_GetEPConstructions():
    
    def __init__(self, downloadTemplate = False, workingDir = sc.sticky["Honeybee_DefaultFolder"]):
        
        
        def downloadFile(url, workingDir):
            import urllib
            webFile = urllib.urlopen(url)
            localFile = open(workingDir + '/' + url.split('/')[-1], 'wb')
            localFile.write(webFile.read())
            webFile.close()
            localFile.close()
        
        def cleanHBLib():
            sc.sticky ["honeybee_constructionLib"] = {}
            sc.sticky ["honeybee_materialLib"] = {}
            sc.sticky ["honeybee_windowMaterialLib"] = {}
            sc.sticky["honeybee_ScheduleLib"] = {}
            sc.sticky["honeybee_ScheduleTypeLimitsLib"] = {}
        
        # create the folder if it is not there
        if not os.path.isdir(workingDir): os.mkdir(workingDir)
        
        # create a backup from users library
        templateFile = os.path.join(workingDir, 'OpenStudioMasterTemplate.idf')
        bckupfile = os.path.join(workingDir, 'OpenStudioMasterTemplate_' + str(int(time.time())) +'.idf')
        
        # download template file
        if downloadTemplate or not os.path.isfile(templateFile):
            # create a backup from users library
            try: shutil.copyfile(templateFile, bckupfile)
            except: pass
            
            try:
                ## download File
                print 'Downloading OpenStudioMasterTemplate.idf to ', workingDir
                updatedLink = "https://dl.dropboxusercontent.com/u/16228160/honeybee/template/OpenStudioMasterTemplate.idf"
                # This is the current link for current available version of Honeybee. Once we release the new version it can be removed.
                #downloadFile(r'https://dl.dropboxusercontent.com/u/16228160/honeybee/OpenStudioMasterTemplate.idf', workingDir)
                downloadFile(updatedLink, workingDir)
                # clean current library
                cleanHBLib()
            except:
                print 'Download failed!!! You need OpenStudioMasterTemplate.idf to use honeybee.' + \
                '\nPlease check your internet connection, and try again!'
        else:
            pass
        
        if not os.path.isfile(workingDir + '\OpenStudioMasterTemplate.idf'):
            print 'Download failed!!! You need OpenStudioMasterTemplate.idf to use honeybee.' + \
                '\nPlease check your internet connection, and try again!'
            return -1
        else:
            libFilePaths = [os.path.join(workingDir, 'OpenStudioMasterTemplate.idf')]
            
        # download openstudio standards
        if not os.path.isfile(workingDir + '\OpenStudio_Standards.json'):
            try:
                ## download File
                print 'Downloading OpenStudio_Standards.json to ', workingDir
                downloadFile(r'https://dl.dropboxusercontent.com/u/16228160/honeybee/OpenStudio_Standards.json', workingDir)
            except:
                print 'Download failed!!! You need OpenStudio_Standards.json to use honeybee.' + \
                '\nPlease check your internet connection, and try again!'
        else:
            pass
        
        
        if not os.path.isfile(workingDir + '\OpenStudio_Standards.json'):
            print 'Download failed!!! You need OpenStudio_Standards.json to use honeybee.' + \
                '\nPlease check your internet connection, and try again!'
            return -1
        else:
            # load the json file
            filepath = os.path.join(workingDir, 'OpenStudio_Standards.json')
            with open(filepath) as jsondata:
                openStudioStandardLib = json.load(jsondata)
            
            sc.sticky ["honeybee_OpenStudioStandardsFile"] = openStudioStandardLib
            print "Standard template file is loaded!\n"
        
        # add cutom library
        customEPLib = os.path.join(workingDir,"userCustomEPLibrary.idf")
        
        if not os.path.isfile(customEPLib):
            # create an empty file
            with open(customEPLib, "w") as outf:
                outf.write("!Honeybee custom EnergyPlus library\n")
        
        if os.path.isfile(customEPLib):
            libFilePaths.append(customEPLib)
        
        def createObject(openFile, resultDict, key, scheduleType = None):
            # This function creates a dictionary from EPObjects
            if key not in resultDict.keys():
                # create an empty dictionary for the key
                resultDict[key] = {}
                
            # store the data into the dictionary
            for lineCount, line in enumerate(inf):
                if lineCount == 0:
                    nameKey = line.split("!")[0].strip()[:-1].upper()
                    
                    if nameKey in resultDict[key].keys():
                        # this means the material is already in the lib
                        # I can rename it but for now I rather to give a warning
                        # and break the loop
                        warning = key + ": " + nameKey + " is already existed in the libaray. " + \
                                  "Rename one of the " + nameKey + " and try again."
                        print warning
                        break
                    else:
                        # add the material to the library
                        resultDict[key][nameKey] = {}
                        if scheduleType!=None: resultDict[key][nameKey][0] = scheduleType
                        
                else:
                    objValue = line.split("!")[0].strip()
                    try: objDescription = line.split("!")[1].strip()
                    except:  objDescription = ""
                    objKey = lineCount #+ '_' + line.split("!-")[1].strip()
        
                    if objValue.endswith(","):
                        resultDict[key][nameKey][objKey] = objValue[:-1], objDescription
                    elif objValue.endswith(";"):
                        resultDict[key][nameKey][objKey] = objValue[:-1], objDescription
                        break
            return resultDict
        
        
        if True: #not sc.sticky.has_key("honeybee_constructionLib") or sc.sticky["honeybee_constructionLib"] == {}:
            print "Loading EP construction library..."
            resultDict = {}
            EPKeys = ["Material", "WindowMaterial", "Construction"]
            for libFilePath in libFilePaths:
                with open(libFilePath, 'r') as inf:
                    for line in inf:
                        for key in EPKeys:
                            if line.strip().startswith(key):
                                resultDict = createObject(inf, resultDict, key, line.strip()[:-1])
                
                outputs = { "Material" : [],
                            "WindowMaterial" : [],
                            "Construction" : []}
                
                materialList = outputs["Material"]
                windowMat =  outputs["WindowMaterial"]
                constrList = outputs["Construction"]
                
                sc.sticky ["honeybee_constructionLib"] = resultDict["Construction"]
                sc.sticky ["honeybee_materialLib"] = resultDict["Material"]
                sc.sticky ["honeybee_windowMaterialLib"] = resultDict["WindowMaterial"]
                sc.sticky ["honeybee_constructionLib"]["List"] = outputs["Construction"]
                sc.sticky ["honeybee_materialLib"]["List"] = outputs["Material"]
                sc.sticky ["honeybee_windowMaterialLib"]["List"] = outputs["WindowMaterial"]
        
            for EPKey in EPKeys:
                if EPKey in resultDict.keys():
                    try:
                        for key in resultDict[EPKey].keys(): outputs[EPKey].append(key)
                        # List shouldn't be counted
                        print  `len(resultDict[EPKey].keys())-1` + " " + EPKey.lower() + " found in " + " & ".join(libFilePaths)
                    except:
                        outputs[key] = " 0 " + EPKey.lower() + " found in " + " & ".join(libFilePaths)
                
        if True: #not sc.sticky.has_key("honeybee_ScheduleLib") or sc.sticky["honeybee_ScheduleLib"] == {}:
            print "\nLoading EP schedules..."
            EPKeys = ["ScheduleTypeLimits", "Schedule"]
            schedulesDict = {}
            for libFilePath in libFilePaths:
                with open(libFilePath, 'r') as inf:
                    for line in inf:
                        for key in EPKeys:
                            if line.strip().startswith(key):
                                schedulesDict = createObject(inf, schedulesDict, key, line.strip()[:-1])
                                break
                
                scheduleOutputs = { "Schedule" : [],
                                    "ScheduleTypeLimits" : []}
                            
                sc.sticky["honeybee_ScheduleLib"] = schedulesDict["Schedule"]
                sc.sticky["honeybee_ScheduleTypeLimitsLib"] = schedulesDict["ScheduleTypeLimits"]
                sc.sticky["honeybee_ScheduleLib"]["List"] = scheduleOutputs["Schedule"]
                sc.sticky["honeybee_ScheduleTypeLimitsLib"]["List"] = scheduleOutputs["ScheduleTypeLimits"]
            
            for EPKey in EPKeys:
                if EPKey in schedulesDict.keys():
                    try:
                        for key in schedulesDict[EPKey].keys():
                            scheduleOutputs[EPKey].append(key)
                        
                        print  `len(schedulesDict[EPKey].keys())-1` + " " + EPKey.lower() + " found in " + " & ".join(libFilePaths)
                    except:
                        scheduleOutputs[key] = " 0 " + EPKey.lower() + " found in "  + " & ".join(libFilePaths)
            print "\n"

class RADMaterialAux(object):
    
    def __init__(self, reloadRADMaterial = False):
            
        self.radMatTypes = ["plastic", "glass", "trans", "metal", "mirror", "mixedfunc", "dielectric", "transdata", "light", "glow"]
        
        if reloadRADMaterial:
            
            # initiate the library
            if not sc.sticky.has_key("honeybee_RADMaterialLib"): sc.sticky ["honeybee_RADMaterialLib"] = {}
            
            # add default materials to the library
            self.analyseRadMaterials(self.createRadMaterialFromParameters('plastic', 'Context_Material', .35, .35, .35, 0, 0.1), True, True)
            self.analyseRadMaterials(self.createRadMaterialFromParameters('plastic', 'Interior_Ceiling', .80, .80, .80, 0, 0.1), True, True)
            self.analyseRadMaterials(self.createRadMaterialFromParameters('plastic', 'Interior_Floor', .2, .2, .2, 0, 0.1), True, True)
            self.analyseRadMaterials(self.createRadMaterialFromParameters('plastic', 'Exterior_Floor', .2, .2, .2, 0, 0.1), True, True)
            self.analyseRadMaterials(self.createRadMaterialFromParameters('glass', 'Exterior_Window', .60, .60, .60), True, True)
            self.analyseRadMaterials(self.createRadMaterialFromParameters('glass', 'Interior_Window', .60, .60, .60), True, True)
            self.analyseRadMaterials(self.createRadMaterialFromParameters('plastic', 'Exterior_Roof', .35, .35, .35, 0, 0.1), True, True)
            self.analyseRadMaterials(self.createRadMaterialFromParameters('plastic', 'Exterior_Wall', .50, .50, .50, 0, 0.1), True, True)
            self.analyseRadMaterials(self.createRadMaterialFromParameters('plastic', 'Interior_Wall', .50, .50, .50, 0, 0.1), True, True)
            
            # import user defined RAD library
            RADLibraryFile = os.path.join(sc.sticky["Honeybee_DefaultFolder"], "HoneybeeRadMaterials.mat")
            if os.path.isfile(RADLibraryFile):
                self.importRADMaterialsFromFile(RADLibraryFile)
            else:
                if not os.path.isdir(sc.sticky["Honeybee_DefaultFolder"]):
                    os.mkdir(sc.sticky["Honeybee_DefaultFolder"])
                with open(RADLibraryFile, "w") as outf:
                    outf.write("#Honeybee Radiance Material Library\n")
            
            # let the user do it for now
            # update the list of the materials in the call from library components
            #for component in ghenv.Component.OnPingDocument().Objects:
            #    if  type(component)== type(ghenv.Component) and component.Name == "Honeybee_Call from Radiance Library":
            #        pass
            #        #component.ExpireSolution(True)
            
            print "Loading RAD default materials..." + \
                  `len(sc.sticky ["honeybee_RADMaterialLib"].keys())` + " RAD materials are loaded\n"
            
        
    def duplicateMaterialWarning(self, materialName, newMaterialString):
        returnYN = {'YES': True, 'NO': False}
        buttons = System.Windows.Forms.MessageBoxButtons.YesNo
        icon = System.Windows.Forms.MessageBoxIcon.Warning
        try:
            currentMaterialString = self.getRADMaterialString(materialName)
        except:
            currentMaterialString = materialName
            isAdded, materialName = self.analyseRadMaterials(materialName, False)
            
        msg = materialName + " already exists in the library:\n\n" + \
            currentMaterialString + "\n" + \
            "Do you want to overwrite the current material with this new definition?\n\n" + \
            newMaterialString + "\n\n" + \
            "Tip: If you are not sure what to do select No and change the material name."
        up = rc.UI.Dialogs.ShowMessageBox(msg, "Duplicate Material Name", buttons, icon)
        return returnYN[up.ToString().ToUpper()]
    
    def addRADMatToDocumentDict(self, HBSrf, currentMatDict, currentMixedFunctionsDict):
        """
        this function collects the materials for a single run and 
        """
        # check if the material is already added
        materialName = HBSrf.RadMaterial
        if not materialName in currentMatDict.keys():
            # find material type
            materialType = sc.sticky ["honeybee_RADMaterialLib"][materialName].keys()[0]
            
            # check if this is a mixed function
            if materialType == "mixfunc":
                # add mixedFunction
                currentMixedFunctionsDict[materialName] =  materialName
                
                # find the base materials for the mixed function
                material1 = sc.sticky ["honeybee_RADMaterialLib"][materialName][materialType][0][0]
                material2 = sc.sticky ["honeybee_RADMaterialLib"][materialName][materialType][0][1]
                
                for matName in [material1, material2]:
                    if not matName in currentMatDict.keys():
                        currentMatDict[matName] = matName
            else:
                # add to the dictionary
                currentMatDict[materialName] = materialName
        
        return currentMatDict, currentMixedFunctionsDict
    
    def createRadMaterialFromParameters(self, modifier, name, *args):
        
        def getTransmissivity(transmittance):
            return (math.sqrt(0.8402528435 + 0.0072522239 * (transmittance ** 2)) - 0.9166530661 ) / 0.0036261119 / transmittance
        
        # I should check the inputs here
        radMaterial = "void " + modifier + " " + name + "\n" + \
                      "0\n" + \
                      "0\n" + \
                      `int(len(args))`
                      
        for arg in args:
            if modifier == "glass":
                radMaterial = radMaterial + (" " + "%.3f"%getTransmissivity(arg))
            else:
                radMaterial = radMaterial + (" " + "%.3f"%arg)
        
        return radMaterial + "\n"
    
    def analyseRadMaterials(self, radMaterialString, addToDocLib = False, overwrite = True):
        """
        import a RAD material string and convert it into Honeybee rad library and return the name
        """
        cleanedRadMaterialString = self.cleanRadMaterials(radMaterialString)
        
        lineSegments = cleanedRadMaterialString.split(" ")
        
        if len(lineSegments) == 1:
            # this is just the name
            # to be used for applying material to surfaces
            return 0, lineSegments[0]
        else:
            #print lineSegments
            materialType = lineSegments[1]
            materialName = lineSegments[2]
            
            if addToDocLib:
                if not overwrite and materialName in sc.sticky ["honeybee_RADMaterialLib"]:
                    upload = self.duplicateMaterialWarning(materialName, radMaterialString)
                    if not upload:
                        return 0, materialName
                sc.sticky ["honeybee_RADMaterialLib"][materialName] = {materialType: {}}
            
                counters = []
                materialProp = lineSegments[3:]
                
                #first counter is the first member of the list
                counter = 0
                counters.append(0)
                
                while counter < len(materialProp):
                    counter += int(materialProp[counter]) + 1
                    try:
                        counters.append(counter)
                    except:
                        pass
                        # print cleanedRadMaterialString
                        # print counter
                # print counters
                
                for counter, count in enumerate(counters[1:]):
                    matStr = materialProp[counters[counter] + 1: count]
                    sc.sticky ["honeybee_RADMaterialLib"][materialName][materialType][counter] = matStr
            else:
                return 0, materialName
                
            return 1, materialName
    
    def cleanRadMaterials(self, radMaterialString):
        """
        inputs rad material string, remove comments, spaces, etc and returns
        a single line string everything separated by a single space
        """
        
        matStr = ""
        lines = radMaterialString.split("\n")
        for line in lines:
            if not line.strip().startswith("#"):
                line = line.replace("\t", " ")
                lineSeg = line.split(" ")
                for seg in lineSeg:
                    if seg.strip()!="":
                        matStr += seg + " "
        return matStr[:-1] # remove the last space
    
    def getRADMaterialString(self, materialName):
        """
        create rad material string from the HB material dictionary based
        """
        materialType = sc.sticky ["honeybee_RADMaterialLib"][materialName].keys()[0]
        matStr = "void " + materialType + " " + materialName + "\n"
        
        for lineCount in sc.sticky ["honeybee_RADMaterialLib"][materialName][materialType].keys():
            properties = sc.sticky ["honeybee_RADMaterialLib"][materialName][materialType][lineCount]
            matStr += str(len(properties)) + " " + " ".join(properties) + "\n"
        
        return matStr
    
    def getRADMaterialType(self, materialName):
        materialType = sc.sticky ["honeybee_RADMaterialLib"][materialName].keys()[0]
        return materialType
    
    def getRADMaterialParameters(self, materialName):
        materialType = self.getRADMaterialType(materialName)
        
        lastLine = len(sc.sticky ["honeybee_RADMaterialLib"][materialName][materialType].keys()) - 1
        
        properties = sc.sticky ["honeybee_RADMaterialLib"][materialName][materialType][lastLine]
        
        return properties
    
    def getSTForTransMaterials(self, materialName):
        properties = self.getRADMaterialParameters(materialName)
        properties = map(float, properties)
        # check got translucant materials
        PHAverage = 0.265 * properties[0] + 0.670 * properties[1] + 0.065 * properties[2]
        
        st = properties[5] * properties[6] * (1 - PHAverage * properties[3])
        
        return st
    
    def importRadMatStr(self, firstline, inRadf):
        matStr = firstline
        for line in inRadf:
            if not line.strip().startswith("void"):
                if not line.strip().startswith("#") and line.strip()!= "":
                    matStr += line
            else:
                isAdded, materialName = self.analyseRadMaterials(matStr, True, True)
                
                # import the rest of the file to the honeybee library
                self.importRadMatStr(line, inRadf)
        
        # import the last file
        isAdded, materialName = self.analyseRadMaterials(matStr, True, True)
        
    def importRADMaterialsFromFile(self, radFilePath):
        with open(radFilePath, "r") as inRadf:
            for line in inRadf:
                if line.strip().startswith("void"):
                    if line.split(" ")[1].strip() in self.radMatTypes:
                        matStr = self.importRadMatStr(line, inRadf)
    
    def searchRadMaterials(self, keywords, materialTypes):
        keywords = [kw.strip().upper() for kw in keywords]
        materialTypes = [mt.strip().upper() for mt in materialTypes]
        
        materials = []
        
        for radMaterial in sc.sticky["honeybee_RADMaterialLib"].keys():
            materialName = radMaterial.ToUpper()
            materialType = sc.sticky["honeybee_RADMaterialLib"][radMaterial].keys()[0].ToUpper()
            
            if len(materialTypes)==0 or materialType.ToUpper()in materialTypes:
                
                if len(keywords)!= 0 and not "*" in keywords:
                    for keyword in keywords:
                        
                        if materialName.find(keyword)!= -1 or keyword.find(materialName)!= -1:
                            materials.append(radMaterial)
                else:
                    materials.append(radMaterial)
        
        return materials
    
    def addToGlobalLibrary(self, RADMaterial, RADLibraryFile = os.path.join(sc.sticky["Honeybee_DefaultFolder"], "HoneybeeRadMaterials.mat")):
        
        added, materialName = self.analyseRadMaterials(RADMaterial, False)
        
        # read the global library file
        if not os.path.isfile(RADLibraryFile):
            # create a single line for the library
            with open(RADLibraryFile, "w") as inf:
                inf.write("#Honeybee Radiance Global Material Library\n\n")
        
        def addToExistingMaterials(firstline, inRadf, targetMaterialName):
            matStr = firstline
            thisLine = ""
            # collect material string
            for thisLine in inRadf:
                if not thisLine.strip().startswith("void"):
                    # avoid comment lines and empty lines
                    if not thisLine.strip().startswith("#") and thisLine.strip()!= "":
                        matStr += thisLine
                else:
                    break
            
            # get the material name
            isAdded, materialName = self.analyseRadMaterials(matStr, False)
            
            # print materialName
            
            if materialName == targetMaterialName:
                self.found = True
                # ask the user if he wants to overwrite it with the new one
                writeTheNewMaterial= self.duplicateMaterialWarning(matStr, RADMaterial)
                
                if writeTheNewMaterial:
                    # update the file
                    self.outFileStr += RADMaterial + "\n"
                else:
                    # keep the current material
                    self.outFileStr += matStr + "\n"
            else:
                # keep this material
                self.outFileStr += matStr + "\n"
            
            # import the rest of the file to the honeybee library
            if thisLine.strip().startswith("void"):
                addToExistingMaterials(thisLine, inRadf, targetMaterialName)
            
        # open the file and read the materials
        self.outFileStr = ""
        self.found = False
        
        with open(RADLibraryFile, "r") as inRadf:
            for line in inRadf:
                if line.strip().startswith("void"):
                    if line.split(" ")[1].strip() in self.radMatTypes:
                        # check if the name is already existed and add it to the
                        # file if the user wants to overwrite the file.
                        addToExistingMaterials(line, inRadf, materialName)
                else:
                    self.outFileStr += line
        
        if self.found == False:
                # the material is just new so let's just add it to the end of the file
                print materialName + " is added to global library"
                self.outFileStr += RADMaterial + "\n"
        # write the new file
        # this is not the most efficient way of read and write a file in Python
        # but as far as the file is not huge it is fine! Someone may want to fix this
        # print self.outFileStr
        with open(RADLibraryFile, "w") as inRadf:
            inRadf.write(self.outFileStr)
        

class hb_EnergySimulatioParameters(object):
    
    def readEPParams(self, EPParameters):
        
        if EPParameters == [] or len(EPParameters)!=11:
            timestep = 6
            
            shadowPar = ["AverageOverDaysInFrequency", 30, 3000]
            
            solarDistribution = "FullExterior"
            
            simulationControl = [True, True, True, False, True]
            
            ddyFile = None
        
        else:
            timestep = int(EPParameters[0])
            
            shadowPar = EPParameters[1:4]
            
            solarDistribution = EPParameters[4]
            
            simulationControl = EPParameters[5:10]
            
            ddyFile = EPParameters[10]
        
        return timestep, shadowPar, solarDistribution, simulationControl, ddyFile


class EPMaterialAux(object):
    
    def __init__(self):
        self.energyModelingStandards = {"0" : "ASHRAE 90.1",
                                        "1" : "ASHRAE 189.1",
                                        "2" : "CBECS 1980-2004",
                                        "3" : "CBECS Before-1980",
                                        "ASHRAE901" : "ASHRAE 90.1",
                                        "ASHRAE1891" : "ASHRAE 189.1",
                                        "CBECS19802004" : "CBECS 1980-2004",
                                        "CBECSBEFORE1980" : "CBECS Before-1980"}
    
    def calcEPMaterialUValue(self, materialObj, GHComponent = None):
        
        materialType = materialObj[0]
        
        if materialType.lower() == "windowmaterial:simpleglazingsystem":
            UValueSI = float(materialObj[1][0])
            
        elif materialType.lower() == "windowmaterial:glazing":
            thickness = float(materialObj[3][0])
            conductivity = float(materialObj[13][0])
            UValueSI = conductivity/thickness
            
        elif materialType.lower() == "material:nomass":
            # Material:NoMass is defined by R-Value and not U-Value
            UValueSI = 1 / float(materialObj[2][0])
            
        elif materialType.lower() == "material":
            thickness = float(materialObj[2][0])
            conductivity = float(materialObj[3][0])
            UValueSI = conductivity/thickness
        
        elif materialType.lower() == "material:airgap":
            UValueSI = 1 / float(materialObj[1][0])
            #print materialObj
            #print UValueSI
        
        elif materialType.lower() == "material:airgap":
            UValueSI = 1 / float(materialObj[1][0])
        
        elif materialType.lower() == "windowmaterial:gas":
            thickness = float(materialObj[2][0])
            if materialObj[1][0].lower() == "air":
                # conductivity = 0.1603675
                # considering ('0.18' for 'Thermal Resistance {m2-K/W}')
                UValueSI = 5.55555555556
            else:
                warningMsg = "Honeybee can't calculate the UValue for " + materialObj[1][0] + ".\n" + \
                    "Let us know if you think it is really neccesary and we will add it to the list. :)"
                if GHComponent!=None:
                    w = gh.GH_RuntimeMessageLevel.Warning
                    GHComponent.AddRuntimeMessage(w, warningMsg)
                    
                    print materialObj
        else:
            warningMsg = "Honeybee currently doesn't support U-Value calculation for " + materialType + ".\n" +\
                "Let us know if you think it is really neccesary and we will add it to the list. :)"
            if GHComponent!=None:
                w = gh.GH_RuntimeMessageLevel.Warning
                GHComponent.AddRuntimeMessage(w, warningMsg)
        
            # http://bigladdersoftware.com/epx/docs/8-0/input-output-reference/page-010.html
            UValueSI = -1
        
        return UValueSI
    
    def calcEPConstructionUValue(self, constructionObj, GHComponent=None):
        # find material layers
        uValues = []
        for layer in constructionObj.keys()[1:]:
            materialName, comment = constructionObj[layer]
            try: values, comments, UValueSI, UValueIP = self.decomposeMaterial(materialName, GHComponent)
            except: UValueSI = -1
            uValues.append(UValueSI)
        
        # calculate cumulative UValue
        totalRValue = 0
        for uValue in uValues:
            totalRValue += 1/uValue
        
        return 1/totalRValue
    
    def convertUValueToIP(self, UValueSI):
        return  0.176110 * UValueSI
    
    def convertUValueToSI(self, UValueIP):
        return  5.678263 * UValueIP
    
    def decomposeMaterial(self, matName, GHComponent = None):
        try:
            try:
                materialObj = sc.sticky["honeybee_materialLib"][matName.upper()]
            except:
                materialObj = sc.sticky["honeybee_windowMaterialLib"][matName.upper()]
                
            comments = []
            values = []
            
            #print matName
            for layer in materialObj.keys():
                try:
                    value, comment = materialObj[layer]
                    # print value + ',\t!-' + comment + "\n"
                    values.append(value)
                    comments.append(comment)
                except:
                    value = materialObj[layer]
                    values.append(value)
                    comments.append('Material Type')
            
            UValueSI = self.calcEPMaterialUValue(materialObj, GHComponent)
            UValueIP = self.convertUValueToIP(UValueSI)
            
            return values, comments, UValueSI, UValueIP
            
        except Exception, e:
            print `e`
            print "Failed to find " + matName + " in the Honeybee material library."
            return -1
    
    
    def decomposeEPCnstr(self, cnstrName, GHComponent = None):
        try:
            constructionObj = sc.sticky ["honeybee_constructionLib"][cnstrName.upper()]
            comments = []
            materials = []
            
            # print cnstrName
            for layer in constructionObj.keys():
                try:
                    material, comment = constructionObj[layer]
                    materials.append(material)
                    comments.append(comment)
                except:
                    material = constructionObj[layer]
                    materials.append(material)
                    comments.append("!- Material Type")
            
            # place holder
            UValue_SI = self.calcEPConstructionUValue(constructionObj, GHComponent)
            UValue_IP = self.convertUValueToIP(UValue_SI)
            
            return materials[1:], comments[1:], UValue_SI, UValue_IP
    
        except Exception, e:
            print `e`
            print "Failed to find " + cnstrName + " in the Honeybee construction library."
            return -1
       
    def searchListByKeyword(self, inputList, keywords):
        """ search inside a list of strings for keywords """
        
        def checkMultipleKeywords(name, keywordlist):
            for kw in keywordlist:
                if name.find(kw)== -1:
                    return False
            return True
            
        kWords = []
        for kw in keywords:
            kWords.append(kw.strip().upper().split(" "))
            
        selectedItems = []
        alternateOptions = []
        
        for item in inputList:
            if len(kWords)!= 0 and not "*" in keywords:
                for keyword in kWords:
                    if len(keyword) > 1 and checkMultipleKeywords(item.ToUpper(), keyword):
                        selectedItems.append(item)
                    elif len(keyword) == 1 and item.ToUpper().find(keyword[0])!= -1:
                        selectedItems.append(item)
            else:
                selectedItems.append(item)
    
        return selectedItems
    
    def filterMaterials(self, constrList, standard, climateZone, surfaceType, bldgProgram, constructionType, sourceComponent):
        hb_EPTypes = EPTypes()
        
        w = gh.GH_RuntimeMessageLevel.Warning
        
        try:
            standard = str(standard).upper().Replace(" ", "").Replace("-", "").Replace(".", "")
            standard = self.energyModelingStandards[standard]
            
        except:
            msg = "The input for standard is not valid. Standard is set to ASHRAE 90.1"
            sourceComponent.AddRuntimeMessage(w, msg)
            standard = "ASHRAE 90.1"
        
        if surfaceType:
            try: surfaceType = hb_EPTypes.srfType[surfaceType.upper()]
            except: sourceComponent.AddRuntimeMessage(w, str(surfaceType) + " is not a valid surface type.")
                
        
        selConstr =[]
        for cnstrName in constrList:
           if cnstrName.upper().find(standard.upper())!=-1 and cnstrName.upper().find(surfaceType.upper())!=-1:
                # check for climate zone
                if climateZone!="":
                    clmZones = []
                    # split by space " "
                    possibleAlt, zoneCode = cnstrName.split(" ")[-2:]
                    clmZoneList = zoneCode.split("-")
                    if len(clmZoneList) != 1:
                        try:
                            clmZoneRange = range(int(clmZoneList[0]), int(clmZoneList[1]) + 1)
                            for clmZone in clmZoneRange: clmZones.append(str(clmZone))
                        except:
                            clmZones = [clmZoneList[0], clmZoneList[1]]
                    else:
                        clmZones = clmZoneList
                        
                    if climateZone in clmZones:
                        selConstr.append(cnstrName)
                    elif climateZone[0] in clmZones:
                        # cases like 3a that is included in 3
                        selConstr.append(cnstrName)
                else:
                    selConstr.append(cnstrName)
                    
        # check if any alternate 
        alternateFit = []
        if bldgProgram!=None and bldgProgram!="":
            bldgProgram = hb_EPTypes.bldgTypes[bldgProgram]
            # print bldgProgram
            for cnstrName in selConstr:
                possibleAlt = cnstrName.split(" ")[-2].split("-")
                if possibleAlt[0].upper().find("ALT")!= -1:
                    if bldgProgram.upper().find(possibleAlt[1].upper())!= -1:
                        # if there is an alternate fit the rest should be removed
                        gistName = " ".join(cnstrName.split(" ")[:-2])
                        gistName.replace
                        alternateFit.append(gistName)
                    else:
                        selConstr.remove(cnstrName)
        
        # check if there is a best fit and if not just return the list
        if alternateFit!=[]:
            for cnstrName in selConstr:
                for gistName in alternateFit:
                    if cnstrName.upper().find(gistName.upper())!= -1 and cnstrName.split(" ")[-2].split("-")[0].upper() != "ALT":
                        try: selConstr.remove(cnstrName)
                        except: pass
        
        # if there are multiple options they should be for different construction types
        # so let check that
        if len(selConstr) > 1 and constructionType != "":
            tempSelConstr = []
            for cnstrName in selConstr:
                if cnstrName.upper().find(constructionType.upper())!= -1:
                    tempSelConstr.append(cnstrName)
            
            if len(tempSelConstr)!=0:
                selConstr = tempSelConstr
        
        return selConstr

    def isEPMaterialObjectAlreadyExists(self, name):
        """
        Check if material or construction exist
        """
        if name in sc.sticky ["honeybee_constructionLib"].keys(): return True
        if name in sc.sticky ["honeybee_materialLib"].keys(): return True
        if name in sc.sticky ["honeybee_windowMaterialLib"].keys(): return True
        
        return False
    
    def getEPObjectsStr(self, objectName):
        """
        This function should work for materials, and counstructions
        """
        objectData = None
        if objectName in sc.sticky ["honeybee_windowMaterialLib"].keys():
            objectData = sc.sticky ["honeybee_windowMaterialLib"][objectName]
        elif objectName in sc.sticky ["honeybee_materialLib"].keys():
            objectData = sc.sticky ["honeybee_materialLib"][objectName]
        elif objectName in sc.sticky ["honeybee_constructionLib"].keys():
            objectData = sc.sticky ["honeybee_constructionLib"][objectName]
        
        if objectData!=None:
            numberOfLayers = len(objectData.keys())
            # add material/construction type
            # print objectData
            objectStr = objectData[0] + ",\n"
            
            # add the name
            objectStr =  objectStr + "  " + objectName + ",   !- name\n"
            
            for layer in range(1, numberOfLayers):
                if layer < numberOfLayers-1:
                    objectStr =  objectStr + "  " + str(objectData[layer][0]) + ",   !- " +  objectData[layer][1] + "\n"
                else:
                    objectStr =  objectStr + "  " + str(objectData[layer][0]) + ";   !- " +  objectData[layer][1] + "\n\n"
            return objectStr
            
    
    def getObjectKey(self, EPObject):
        
        EPKeys = ["Material", "WindowMaterial", "Construction"]
    
        # check if it is a full string
        for key in EPKeys:
            if EPObject.strip().startswith(key):
                return key
    
    def addEPConstructionToLib(self, EPMaterial, overwrite = False):
        
        key = self.getObjectKey(EPMaterial)
        
        if key == None:
            return None, None
        
        HBLibrarieNames = {
                       "Construction" : "honeybee_constructionLib",
                       "Material" : "honeybee_materialLib",
                       "WindowMaterial" : "honeybee_windowMaterialLib"
                       }
        
        # find construction/material name
        name = EPMaterial.split("\n")[1].split("!")[0].strip()[:-1].upper()
        
        if name in sc.sticky[HBLibrarieNames[key]].keys():
            #overwrite = True
            if not overwrite:
                # ask user if they want to overwrite it
                add = self.duplicateEPMaterialWarning(name, EPMaterial)
                if not add: return False, name
        
        # add material/construction to the lib
        # create an empty dictoinary for the material
        sc.sticky[HBLibrarieNames[key]][name] = {}
        
        lines = EPMaterial.split("\n")

        # store the data into the dictionary
        for lineCount, line in enumerate(lines):
            
            objValue = line.split("!")[0].strip()
            try: objDescription = line.split("!")[1].strip()
            except:  objDescription = ""
            if lineCount == 0:
                sc.sticky[HBLibrarieNames[key]][name][lineCount] = objValue[:-1]
            elif lineCount == 1:
                pass # name is already there as the key
            elif objValue.endswith(","):
                sc.sticky[HBLibrarieNames[key]][name][lineCount-1] = objValue[:-1], objDescription
            elif objValue.endswith(";"):
                sc.sticky[HBLibrarieNames[key]][name][lineCount-1] = objValue[:-1], objDescription
                break
        
        # add name to list
        sc.sticky [HBLibrarieNames[key]]["List"].append(name)
        
        return True, name
    
    def duplicateEPMaterialWarning(self, objectName, newMaterialString):
        # this function is duplicate with duplicateEPObject warning and should be removed at some point
        returnYN = {'YES': True, 'NO': False}
        buttons = System.Windows.Forms.MessageBoxButtons.YesNo
        icon = System.Windows.Forms.MessageBoxIcon.Warning
        
        currentMaterialString = self.getEPObjectsStr(objectName)
            
        msg = objectName + " already exists in the library:\n\n" + \
            currentMaterialString + "\n" + \
            "Do you want to overwrite the current with this new definition?\n\n" + \
            newMaterialString + "\n\n" + \
            "Tip: If you are not sure what to do select No and change the name."
        
        up = rc.UI.Dialogs.ShowMessageBox(msg, "Duplicate Material Name", buttons, icon)
        return returnYN[up.ToString().ToUpper()]

class EPScheduleAux(object):
    
    def getScheduleDataByName(self, schName, component = None):

        if schName.lower().endswith(".csv"):
            # Check for the file
            if not os.path.isfile(schName):
                msg = "Failed to find the schedule file: " + schName
                print msg
                if component is not None:
                    component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
                return None, None
                
            return schName, "csv"
            
        try:
            scheduleObj = sc.sticky["honeybee_ScheduleLib"][schName.upper()]
        except Exception, e:
            #print e
            msg = "Failed to find " + schName + " in the Honeybee schedule library."
            print msg
            if component is not None:
                component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
            
            return None, None
            
        comments = []
        values = []
        
        for layer in scheduleObj.keys():
            try:
                material, comment = scheduleObj[layer]
                values.append(material)
                comments.append(comment)
            except:
                scheduleType = scheduleObj[layer]
                values.append(scheduleType)
                comments.append("Schedule Type")
        
        return values, comments
    
    def getScheduleTypeLimitsDataByName(self, schName, component = None):
        try:
            scheduleObj = sc.sticky["honeybee_ScheduleTypeLimitsLib"][schName.upper()]
        except Exception, e:
            #print e
            msg = "Failed to find " + schName + " in the Honeybee schedule type limits library."
            print msg
            if component is not None:
                component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
            
            return None, None
            
        comments = []
        values = []
        
        for layer in scheduleObj.keys():
            try:
                material, comment = scheduleObj[layer]
                values.append(material)
                comments.append(comment)
            except:
                scheduleType = scheduleObj[layer]
                values.append(scheduleType)
                comments.append("Schedule Type")
        
        return values, comments


class EPObjectsAux(object):
    
    def isEPMaterial(self, matName):
        return matName.upper() in sc.sticky["honeybee_materialLib"].keys() or \
               matName.upper() in sc.sticky["honeybee_windowMaterialLib"].keys()
    
    def isEPConstruction(self, matName):
        return matName.upper() in sc.sticky["honeybee_constructionLib"].keys()
    
    def isSchedule(self, scheduleName):
        return scheduleName.upper() in sc.sticky["honeybee_ScheduleLib"].keys()
    
    def isScheduleTypeLimits(self, scheduleName):
        return scheduleName.upper() in sc.sticky["honeybee_ScheduleTypeLimitsLib"].keys()
    
    def customizeEPObject(self, EPObjectName, indexes, inValues):
        hb_EPScheduleAUX = EPScheduleAux()
        hb_EPMaterialAUX = EPMaterialAux()
        
        if self.isSchedule(EPObjectName):
            values, comments = hb_EPScheduleAUX.getScheduleDataByName(EPObjectName.upper())
        
        elif self.isScheduleTypeLimits(EPObjectName):
            values, comments = hb_EPScheduleAUX.getScheduleTypeLimitsDataByName(EPObjectName.upper())
        elif self.isEPConstruction(EPObjectName):
            values, comments, uSI, uIP = hb_EPMaterialAUX.decomposeEPCnstr(EPObjectName.upper())
        
        elif self.isEPMaterial(EPObjectName):
            values, comments, uSI, uIP = hb_EPMaterialAUX.decomposeMaterial(EPObjectName.upper())
        else:
            return
        
        # create a dictionary of index and values
        if len(indexes)==0 or (len(indexes) != len(inValues)):
            return
        
        valuesDict = {}
        
        for i, v in zip(indexes, inValues):
            valuesDict[i] = v
        
        count = 0
        originalObj = ""
        modifiedObj = ""
        
        for value, comment in zip(values, comments):
            if count == len(values) -1:
                separator = ";"
            else:
                separator = ","
                
            if count == 1:
                # add name
                originalObj += "[" + `count` + "]\t" + EPObjectName.upper() + " ! Name\n" 
                
                if count in valuesDict.keys():
                    # update the value
                    modifiedObj += valuesDict[count].upper() + separator + "   ! Name\n"
                
                else:
                    # keep original
                    modifiedObj += EPObjectName.upper() + separator + "    ! Name\n"
                
                count = 2
                
            originalObj += "[" + `count` + "]\t " + value + "   !" + comment + "\n" 
            
            if count in valuesDict.keys():
                modifiedObj += valuesDict[count] + separator + "   !" + comment + "\n"
            else:
                modifiedObj += value + separator + "   !" + comment + "\n" 
                
            count += 1
        
        return originalObj, modifiedObj
    
    def getObjectKey(self, EPObject):
        
        EPKeys = ["Material", "WindowMaterial", "Construction", "ScheduleTypeLimits", "Schedule"]
        
        # check if it is a full string
        for key in EPKeys:
            if EPObject.strip().startswith(key):
                return key
    
    def addEPObjectToLib(self, EPObject, overwrite = False):
        
        key = self.getObjectKey(EPObject)
        
        if key == None:
            return None, None
        
        HBLibrarieNames = {
                       "Construction" : "honeybee_constructionLib",
                       "Material" : "honeybee_materialLib",
                       "WindowMaterial" : "honeybee_windowMaterialLib",
                       "Schedule": "honeybee_ScheduleLib",
                       "ScheduleTypeLimits" : "honeybee_ScheduleTypeLimitsLib"
                       }
        
        # find construction/material name
        name = EPObject.split("\n")[1].split("!")[0].strip()[:-1].upper()
        
        if name in sc.sticky[HBLibrarieNames[key]].keys():
            #overwrite = True
            if not overwrite:
                # ask user if they want to overwrite it
                add = self.duplicateEPObjectWarning(name, EPObject)
                if not add: return False, name
        
        # add material/construction to the lib
        # create an empty dictoinary for the material
        sc.sticky[HBLibrarieNames[key]][name] = {}
        
        lines = EPObject.split("\n")

        # store the data into the dictionary
        for lineCount, line in enumerate(lines):
            
            objValue = line.split("!")[0].strip()
            try: objDescription = line.split("!")[1].strip()
            except:  objDescription = ""
            if lineCount == 0:
                sc.sticky[HBLibrarieNames[key]][name][lineCount] = objValue[:-1]
            elif lineCount == 1:
                pass # name is already there as the key
            elif objValue.endswith(","):
                sc.sticky[HBLibrarieNames[key]][name][lineCount-1] = objValue[:-1], objDescription
            elif objValue.endswith(";"):
                sc.sticky[HBLibrarieNames[key]][name][lineCount-1] = objValue[:-1], objDescription
                break
        
        # add name to list
        sc.sticky [HBLibrarieNames[key]]["List"].append(name)
        
        return True, name
    
    def getEPObjectDataByName(self, objectName):
        objectData = None
        
        objectName = objectName.upper()
        
        if objectName in sc.sticky ["honeybee_windowMaterialLib"].keys():
            objectData = sc.sticky ["honeybee_windowMaterialLib"][objectName]
        elif objectName in sc.sticky ["honeybee_materialLib"].keys():
            objectData = sc.sticky ["honeybee_materialLib"][objectName]
        elif objectName in sc.sticky ["honeybee_constructionLib"].keys():
            objectData = sc.sticky ["honeybee_constructionLib"][objectName]
        elif objectName in sc.sticky["honeybee_ScheduleLib"].keys():
            objectData = sc.sticky ["honeybee_ScheduleLib"][objectName]
        elif objectName in sc.sticky["honeybee_ScheduleTypeLimitsLib"].keys():
            objectData = sc.sticky ["honeybee_ScheduleTypeLimitsLib"][objectName]

        return objectData
    
    def getEPObjectsStr(self, objectName):
        """
        This function should work for materials, and counstructions
        """
        
        objectData = self.getEPObjectDataByName(objectName)
        
        if objectData!=None:
            numberOfLayers = len(objectData.keys())
            # add material/construction type
            # print objectData
            objectStr = objectData[0] + ",\n"
            
            # add the name
            objectStr =  objectStr + "  " + objectName + ",   !- name\n"
            
            for layer in range(1, numberOfLayers):
                if layer < numberOfLayers-1:
                    objectStr =  objectStr + "  " + str(objectData[layer][0]) + ",   !- " +  objectData[layer][1] + "\n"
                else:
                    objectStr =  objectStr + "  " + str(objectData[layer][0]) + ";   !- " +  objectData[layer][1] + "\n\n"
            return objectStr
            
    def duplicateEPObjectWarning(self, objectName, newMaterialString):
        returnYN = {'YES': True, 'NO': False}
        buttons = System.Windows.Forms.MessageBoxButtons.YesNo
        icon = System.Windows.Forms.MessageBoxIcon.Warning
        
        currentMaterialString = self.getEPObjectsStr(objectName)
            
        msg = objectName + " already exists in the library:\n\n" + \
            currentMaterialString + "\n" + \
            "Do you want to overwrite the current with this new definition?\n\n" + \
            newMaterialString + "\n\n" + \
            "Tip: If you are not sure what to do select No and change the name."
        
        up = rc.UI.Dialogs.ShowMessageBox(msg, "Duplicate Material Name", buttons, icon)
        
        return returnYN[up.ToString().ToUpper()]
        
        

class EPTypes(object):
    def __init__(self):
        self.srfType = {0:'WALL',
                   0.5: 'UndergroundWall',
                   1:'ROOF',
                   1.5: 'UndergroundCeiling',
                   2:'FLOOR',
                   2.25: 'UndergroundSlab',
                   2.5: 'SlabOnGrade',
                   2.75: 'ExposedFloor',
                   3:'CEILING',
                   4:'WALL',
                   5:'WINDOW',
                   6:'SHADING',
                   'WALL': 'WALL',
                   'ROOF':'ROOF',
                   'FLOOR': 'FLOOR',
                   'CEILING': 'CEILING',
                   'WINDOW':'WINDOW',
                   'SHADING': 'SHADING'}
            
        self.bldgTypes = {0:'RES',
                   'RESIDENTIAL':'RES',
                   1:'OFFICE',
                   'OFFICE':'OFFC',
                   2:'HOSP',
                   'HOSPITAL':'HOSP'
                   }
                #Restaurant(Full Service)  = "FullServiceRestaurant"
                #Restaurant(Quick Service) = "QuickServiceRestaurant"
                #Mid-rise Apartment        = "Mid-riseApartment"
                #Hospital                  = "Hospital"
                #Small Office              = "Small Office"
                #Medium Office             = "Medium Office"
                #Large Office              = "Large Office"
                #Small Hotel               = "SmallHotel"
                #Large Hotel               = "LargeHotel"
                #Primary School            = "PrimarySchool"
                #Secondary School          = "SecondarySchool"
                #Strip Mall                = "StripMall"
                #Retail                    = "Retail"
                #Warehouse                 = "Warehouse"
        
class materialLibrary(object):
    
    def __init__(self):
        self.zoneProgram = {0: 'RETAIL',
                1: 'OFFICE',
                2: 'RESIDENTIAL',
                3: 'HOTEL'}
                
        self.zoneConstructionSet =  {0: 'RETAIL_CON',
                        1: 'OFFICE_CON',
                        2: 'RESIDENTIAL_CON',
                        3: 'HOTEL_CON'}
                   
        self.zoneInternalLoad = {0: 'RETAIL_INT_LOAD',
                    1: 'OFFICE_INT_LOAD',
                    2: 'RESIDENTIAL_INT_LOAD',
                    3: 'HOTEL_INT_LOAD'}

        self.zoneSchedule =  {0: 'RETAIL_SCH',
                 1: 'OFFICE_SCH',
                 2: 'RESIDENTIAL_SCH',
                 3: 'HOTEL_SCH'}
             
        self.zoneThermostat =  {0: 'RETAIL_SCH',
                   1: 'OFFICE_SCH',
                   2: 'RESIDENTIAL_SCH',
                   3: 'HOTEL_SCH'}
                   

class scheduleLibrary(object):
    
    # schedule library should be updated to functions
    # so it can be used to generate schedueles
    def __init__(self):
        
        self.ScheduleTypeLimits = '\n' + \
        'ScheduleTypeLimits,\n' + \
        '\tFraction,                !- Name\n' + \
        '\t0,                       !- Lower Limit Value\n' + \
        '\t1,                       !- Upper Limit Value\n' + \
        '\tCONTINUOUS;              !- Numeric Type\n' + \
        '\n' + \
        'ScheduleTypeLimits,\n' + \
        '\tOn/Off,                  !- Name\n' + \
        '\t0,                       !- Lower Limit Value\n' + \
        '\t1,                       !- Upper Limit Value\n' + \
        '\tDISCRETE;                !- Numeric Type\n' + \
        '\n' + \
        'ScheduleTypeLimits,\n' + \
        '\tTemperature,             !- Name\n' + \
        '\t-60,                     !- Lower Limit Value\n' + \
        '\t200,                     !- Upper Limit Value\n' + \
        '\tCONTINUOUS;              !- Numeric Type\n' + \
        '\n' + \
        'ScheduleTypeLimits,\n' + \
        '\tControl Type,            !- Name\n' + \
        '\t0,                       !- Lower Limit Value\n' + \
        '\t4,                       !- Upper Limit Value\n' + \
        '\tDISCRETE;                !- Numeric Type\n' + \
        '\n' + \
        'ScheduleTypeLimits,\n' + \
        '\tAny Number;              !- Name\n'
        
        self.largeOfficeEquipmentSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_BLDG_EQUIP_SCH,  !- Name\n' + \
            '\tFraction,                !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: Weekdays,           !- Field 2\n' + \
            '\tUntil: 08:00,            !- Field 3\n' + \
            '\t0.40,                    !- Field 4\n' + \
            '\tUntil: 12:00,            !- Field 5\n' + \
            '\t0.90,                    !- Field 6\n' + \
            '\tUntil: 13:00,            !- Field 7\n' + \
            '\t0.80,                    !- Field 8\n' + \
            '\tUntil: 17:00,            !- Field 9\n' + \
            '\t0.90,                    !- Field 10\n' + \
            '\tUntil: 18:00,            !- Field 11\n' + \
            '\t0.80,                    !- Field 12\n' + \
            '\tUntil: 20:00,            !- Field 13\n' + \
            '\t0.60,                    !- Field 14\n' + \
            '\tUntil: 22:00,            !- Field 15\n' + \
            '\t0.50,                    !- Field 16\n' + \
            '\tUntil: 24:00,            !- Field 17\n' + \
            '\t0.40,                    !- Field 18\n' + \
            '\tFor: Saturday,           !- Field 19\n' + \
            '\tUntil: 06:00,            !- Field 20\n' + \
            '\t0.30,                    !- Field 21\n' + \
            '\tUntil: 08:00,            !- Field 22\n' + \
            '\t0.4,                     !- Field 23\n' + \
            '\tUntil: 14:00,            !- Field 24\n' + \
            '\t0.5,                     !- Field 25\n' + \
            '\tUntil: 17:00,            !- Field 26\n' + \
            '\t0.35,                    !- Field 27\n' + \
            '\tUntil: 24:00,            !- Field 28\n' + \
            '\t0.30,                    !- Field 29\n' + \
            '\tFor: SummerDesignDay,    !- Field 30\n' + \
            '\tUntil: 24:00,            !- Field 31\n' + \
            '\t1.0,                     !- Field 32\n' + \
            '\tFor: WinterDesignDay,    !- Field 33\n' + \
            '\tUntil: 24:00,            !- Field 34\n' + \
            '\t0.0,                     !- Field 35\n' + \
            '\tFor: AllOtherDays,       !- Field 36\n' + \
            '\tUntil: 24:00,            !- Field 37\n' + \
            '\t0.30;                    !- Field 38\n'
        
        self.largeOfficeElevatorsSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_BLDG_ELEVATORS,  !- Name\n' + \
            '\tFraction,                !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: AllDays,            !- Field 2\n' + \
            '\tUntil: 04:00,            !- Field 3\n' + \
            '\t0.05,                    !- Field 4\n' + \
            '\tUntil: 05:00,            !- Field 5\n' + \
            '\t0.10,                    !- Field 6\n' + \
            '\tUntil: 06:00,            !- Field 7\n' + \
            '\t0.20,                    !- Field 8\n' + \
            '\tUntil: 07:00,            !- Field 9\n' + \
            '\t0.40,                    !- Field 10\n' + \
            '\tUntil: 09:00,            !- Field 11\n' + \
            '\t0.50,                    !- Field 12\n' + \
            '\tUntil: 10:00,            !- Field 13\n' + \
            '\t0.35,                    !- Field 14\n' + \
            '\tUntil: 16:00,            !- Field 15\n' + \
            '\t0.15,                    !- Field 16\n' + \
            '\tUntil: 17:00,            !- Field 17\n' + \
            '\t0.35,                    !- Field 18\n' + \
            '\tUntil: 19:00,            !- Field 19\n' + \
            '\t0.50,                    !- Field 20\n' + \
            '\tUntil: 21:00,            !- Field 21\n' + \
            '\t0.40,                    !- Field 22\n' + \
            '\tUntil: 22:00,            !- Field 23\n' + \
            '\t0.30,                    !- Field 24\n' + \
            '\tUntil: 23:00,            !- Field 25\n' + \
            '\t0.20,                    !- Field 26\n' + \
            '\tUntil: 24:00,            !- Field 27\n' + \
            '\t0.10;                    !- Field 28\n'
            
        self.largeOfficeOccupancySchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_BLDG_OCC_SCH,  !- Name\n' + \
            '\tFraction,                !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: SummerDesignDay,    !- Field 2\n' + \
            '\tUntil: 06:00,            !- Field 3\n' + \
            '\t0.0,                     !- Field 4\n' + \
            '\tUntil: 22:00,            !- Field 5\n' + \
            '\t1.0,                     !- Field 6\n' + \
            '\tUntil: 24:00,            !- Field 7\n' + \
            '\t0.05,                    !- Field 8\n' + \
            '\tFor: Weekdays,           !- Field 9\n' + \
            '\tUntil: 06:00,            !- Field 10\n' + \
            '\t0.0,                     !- Field 11\n' + \
            '\tUntil: 07:00,            !- Field 12\n' + \
            '\t0.1,                     !- Field 13\n' + \
            '\tUntil: 08:00,            !- Field 14\n' + \
            '\t0.2,                     !- Field 15\n' + \
            '\tUntil: 12:00,            !- Field 16\n' + \
            '\t0.95,                    !- Field 17\n' + \
            '\tUntil: 13:00,            !- Field 18\n' + \
            '\t0.5,                     !- Field 19\n' + \
            '\tUntil: 17:00,            !- Field 20\n' + \
            '\t0.95,                    !- Field 21\n' + \
            '\tUntil: 18:00,            !- Field 22\n' + \
            '\t0.7,                     !- Field 23\n' + \
            '\tUntil: 20:00,            !- Field 24\n' + \
            '\t0.4,                     !- Field 25\n' + \
            '\tUntil: 22:00,            !- Field 26\n' + \
            '\t0.1,                     !- Field 27\n' + \
            '\tUntil: 24:00,            !- Field 28\n' + \
            '\t0.05,                    !- Field 29\n' + \
            '\tFor: Saturday,           !- Field 30\n' + \
            '\tUntil: 06:00,            !- Field 31\n' + \
            '\t0.0,                     !- Field 32\n' + \
            '\tUntil: 08:00,            !- Field 33\n' + \
            '\t0.1,                     !- Field 34\n' + \
            '\tUntil: 14:00,            !- Field 35\n' + \
            '\t0.5,                     !- Field 36\n' + \
            '\tUntil: 17:00,            !- Field 37\n' + \
            '\t0.1,                     !- Field 38\n' + \
            '\tUntil: 24:00,            !- Field 39\n' + \
            '\t0.0,                     !- Field 40\n' + \
            '\tFor: AllOtherDays,       !- Field 41\n' + \
            '\tUntil: 24:00,            !- Field 42\n' + \
            '\t0.0;                     !- Field 43\n'
            
        self.largeOfficeWorkEffSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_WORK_EFF_SCH,  !- Name\n' + \
            '\tOn/Off,                  !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: AllDays,            !- Field 2\n' + \
            '\tUntil: 24:00,            !- Field 3\n' + \
            '\t0.0;                     !- Field 4\n'
            
        self.largeOfficeInfiltrationSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_INFIL_QUARTER_ON_SCH,  !- Name\n' + \
            '\tFraction,                !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: Weekdays SummerDesignDay,  !- Field 2\n' + \
            '\tUntil: 06:00,            !- Field 3\n' + \
            '\t1.0,                     !- Field 4\n' + \
            '\tUntil: 22:00,            !- Field 5\n' + \
            '\t0.25,                    !- Field 6\n' + \
            '\tUntil: 24:00,            !- Field 7\n' + \
            '\t1.0,                     !- Field 8\n' + \
            '\tFor: Saturday WinterDesignDay,  !- Field 9\n' + \
            '\tUntil: 06:00,            !- Field 10\n' + \
            '\t1.0,                     !- Field 11\n' + \
            '\tUntil: 18:00,            !- Field 12\n' + \
            '\t0.25,                    !- Field 13\n' + \
            '\tUntil: 24:00,            !- Field 14\n' + \
            '\t1.0,                     !- Field 15\n' + \
            '\tFor: Sunday Holidays AllOtherDays,  !- Field 16\n' + \
            '\tUntil: 24:00,            !- Field 17\n' + \
            '\t1.0;                     !- Field 18\n'
            
        self.largeOfficeClothingSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_CLOTHING_SCH,  !- Name\n' + \
            '\tFraction,                !- Schedule Type Limits Name\n' + \
            '\tThrough: 04/30,          !- Field 1\n' + \
            '\tFor: AllDays,            !- Field 2\n' + \
            '\tUntil: 24:00,            !- Field 3\n' + \
            '\t1.0,                     !- Field 4\n' + \
            '\tThrough: 09/30,          !- Field 5\n' + \
            '\tFor: AllDays,            !- Field 6\n' + \
            '\tUntil: 24:00,            !- Field 7\n' + \
            '\t0.5,                     !- Field 8\n' + \
            '\tThrough: 12/31,          !- Field 9\n' + \
            '\tFor: AllDays,            !- Field 10\n' + \
            '\tUntil: 24:00,            !- Field 11\n' + \
            '\t1.0;                     !- Field 12\n'
            
        self.alwaysOffSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tAlways_Off,              !- Name\n' + \
            '\tOn/Off,                  !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: AllDays,            !- Field 2\n' + \
            '\tUntil: 24:00,            !- Field 3\n' + \
            '\t0;                       !- Field 4\n'
            
        self.largeOfficeHeatingSetPtSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_HTGSETP_SCH,!- Name\n' + \
            '\tTemperature,             !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: Weekdays,           !- Field 2\n' + \
            '\tUntil: 06:00,            !- Field 3\n' + \
            '\t15.6,                    !- Field 4\n' + \
            '\tUntil: 22:00,            !- Field 5\n' + \
            '\t21.0,                    !- Field 6\n' + \
            '\tUntil: 24:00,            !- Field 7\n' + \
            '\t15.6,                    !- Field 8\n' + \
            '\tFor SummerDesignDay,     !- Field 9\n' + \
            '\tUntil: 24:00,            !- Field 10\n' + \
            '\t15.6,                    !- Field 11\n' + \
            '\tFor: Saturday,           !- Field 12\n' + \
            '\tUntil: 06:00,            !- Field 13\n' + \
            '\t15.6,                    !- Field 14\n' + \
            '\tUntil: 18:00,            !- Field 15\n' + \
            '\t21.0,                    !- Field 16\n' + \
            '\tUntil: 24:00,            !- Field 17\n' + \
            '\t15.6,                    !- Field 18\n' + \
            '\tFor: WinterDesignDay,    !- Field 19\n' + \
            '\tUntil: 24:00,            !- Field 20\n' + \
            '\t21.0,                    !- Field 21\n' + \
            '\tFor: AllOtherDays,       !- Field 22\n' + \
            '\tUntil: 24:00,            !- Field 23\n' + \
            '\t15.6;                    !- Field 24\n'
            
        self.largeOfficeCoolingSetPtSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_CLGSETP_SCH,!- Name\n' + \
            '\tTemperature,             !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: Weekdays SummerDesignDay,  !- Field 2\n' + \
            '\tUntil: 06:00,            !- Field 3\n' + \
            '\t26.7,                    !- Field 4\n' + \
            '\tUntil: 22:00,            !- Field 5\n' + \
            '\t24.0,                    !- Field 6\n' + \
            '\tUntil: 24:00,            !- Field 7\n' + \
            '\t26.7,                    !- Field 8\n' + \
            '\tFor: Saturday,           !- Field 9\n' + \
            '\tUntil: 06:00,            !- Field 10\n' + \
            '\t26.7,                    !- Field 11\n' + \
            '\tUntil: 18:00,            !- Field 12\n' + \
            '\t24.0,                    !- Field 13\n' + \
            '\tUntil: 24:00,            !- Field 14\n' + \
            '\t26.7,                    !- Field 15\n' + \
            '\tFor WinterDesignDay,     !- Field 16\n' + \
            '\tUntil: 24:00,            !- Field 17\n' + \
            '\t26.7,                    !- Field 18\n' + \
            '\tFor: AllOtherDays,       !- Field 19\n' + \
            '\tUntil: 24:00,            !- Field 20\n' + \
            '\t26.7;                    !- Field 21\n'
        
        self.largeOfficeActivitySchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_ACTIVITY_SCH,  !- Name\n' + \
            '\tAny Number,              !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: AllDays,            !- Field 2\n' + \
            '\tUntil: 24:00,            !- Field 3\n' + \
            '\t120;                     !- Field 4\n'
        
        self.alwaysOnSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tAlways_On,               !- Name\n' + \
            '\tOn/Off,                  !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: AllDays,            !- Field 2\n' + \
            '\tUntil: 24:00,            !- Field 3\n' + \
            '\t1;                       !- Field 4\n'
        
        self.largeOfficeLightingSchedule = '\n' + \
            'Schedule:Compact,\n' + \
            '\tLarge Office_BLDG_LIGHT_SCH,  !- Name\n' + \
            '\tFraction,                !- Schedule Type Limits Name\n' + \
            '\tThrough: 12/31,          !- Field 1\n' + \
            '\tFor: Weekdays,           !- Field 2\n' + \
            '\tUntil: 05:00,            !- Field 3\n' + \
            '\t0.05,                    !- Field 4\n' + \
            '\tUntil: 07:00,            !- Field 5\n' + \
            '\t0.1,                     !- Field 6\n' + \
            '\tUntil: 08:00,            !- Field 7\n' + \
            '\t0.3,                     !- Field 8\n' + \
            '\tUntil: 17:00,            !- Field 9\n' + \
            '\t0.9,                     !- Field 10\n' + \
            '\tUntil: 18:00,            !- Field 11\n' + \
            '\t0.7,                     !- Field 12\n' + \
            '\tUntil: 20:00,            !- Field 13\n' + \
            '\t0.5,                     !- Field 14\n' + \
            '\tUntil: 22:00,            !- Field 15\n' + \
            '\t0.3,                     !- Field 16\n' + \
            '\tUntil: 23:00,            !- Field 17\n' + \
            '\t0.1,                     !- Field 18\n' + \
            '\tUntil: 24:00,            !- Field 19\n' + \
            '\t0.05,                    !- Field 20\n' + \
            '\tFor: Saturday,           !- Field 21\n' + \
            '\tUntil: 06:00,            !- Field 22\n' + \
            '\t0.05,                    !- Field 23\n' + \
            '\tUntil: 08:00,            !- Field 24\n' + \
            '\t0.1,                     !- Field 25\n' + \
            '\tUntil: 14:00,            !- Field 26\n' + \
            '\t0.5,                     !- Field 27\n' + \
            '\tUntil: 17:00,            !- Field 28\n' + \
            '\t0.15,                    !- Field 29\n' + \
            '\tUntil: 24:00,            !- Field 30\n' + \
            '\t0.05,                    !- Field 31\n' + \
            '\tFor: SummerDesignDay,    !- Field 32\n' + \
            '\tUntil: 24:00,            !- Field 33\n' + \
            '\t1.0,                     !- Field 34\n' + \
            '\tFor: WinterDesignDay,    !- Field 35\n' + \
            '\tUntil: 24:00,            !- Field 36\n' + \
            '\t0.0,                     !- Field 37\n' + \
            '\tFor: AllOtherDays,       !- Field 38\n' + \
            '\tUntil: 24:00,            !- Field 39\n' + \
            '\t0.05;                    !- Field 40\n'
    

class BuildingProgramsLib(object):
    def __init__(self):
        
        self.bldgPrograms = {
                0 : 'Office',
                1 : 'Retail',
                2 : 'MidriseApartment',
                3 : 'PrimarySchool',
                4 : 'SecondarySchool',
                5 : 'SmallHotel',
                6 : 'LargeHotel',
                7 : 'Hospital',
                8 : 'Outpatient',
                9 : 'Warehouse',
                10 : 'SuperMarket',
                11 : 'FullServiceRestaurant',
                12 : 'QuickServiceRestaurant',
                'Office' : 'Office',
                'Retail' : 'Retail',
                'MidriseApartment' : 'MidriseApartment',
                'PrimarySchool' : 'PrimarySchool',
                'SecondarySchool' : 'SecondarySchool',
                'SmallHotel' : 'SmallHotel',
                'LargeHotel' : 'LargeHotel',
                'Hospital' : 'Hospital',
                'Outpatient' : 'Outpatient',
                'Warehouse' : 'Warehouse',
                'SuperMarket' : 'SuperMarket',
                'FullServiceRestaurant' : 'FullServiceRestaurant',
                'QuickServiceRestaurant' : 'QuickServiceRestaurant'}
        
        self.zonePrograms = { "MidriseApartment" : {
                                            0: "Apartment",
                                            1: "Office",
                                            2: "Corridor",
                                            },
                    'Outpatient' : {
                                    0: "IT_Room",
                                    1: "ProcedureRoom",
                                    2: "Conference",
                                    3: "MedGas",
                                    4: "Janitor",
                                    5: "Cafe",
                                    6: "OR",
                                    7: "PhysicalTherapy",
                                    8: "Lobby",
                                    9: "Xray",
                                    10: "MRI_Control",
                                    11: "Toilet",
                                    12: "Elec/MechRoom",
                                    13: "Stair",
                                    14: "PACU",
                                    15: "Anesthesia",
                                    16: "MRI",
                                    17: "CleanWork",
                                    18: "NurseStation",
                                    19: "PreOp",
                                    20: "Lounge",
                                    21: "BioHazard",
                                    22: "Office",
                                    23: "Hall",
                                    24: "Soil Work",
                                    25: "DressingRoom",
                                    26: "Exam",
                                    27: "LockerRoom",
                                    },
                    'LargeHotel'  : {
                                    0: "Storage",
                                    1: "Mechanical",
                                    2: "Banquet",
                                    3: "GuestRoom",
                                    4: "Laundry",
                                    5: "Retail",
                                    6: "Kitchen",
                                    7: "Cafe",
                                    8: "Corridor",
                                    9: "Lobby"
                                    },
                    'FullServiceRestaurant' : {
                                    0: "Kitchen",
                                    1: "Dining"
                                    },
                    'PrimarySchool' : {
                                    0: "Mechanical",
                                    1: "Library",
                                    2: "Cafeteria",
                                    3: "Gym",
                                    4: "Restroom",
                                    5: "Office",
                                    6: "Classroom",
                                    7: "Kitchen",
                                    8: "Corridor",
                                    9: "Lobby"
                                    },
                    'SmallHotel' : {
                                    0: "Storage",
                                    1: "GuestLounge",
                                    2: "Mechanical",
                                    3: "StaffLounge",
                                    4: "PublicRestroom",
                                    5: "GuestRoom",
                                    6: "Exercise",
                                    7: "Laundry",
                                    8: "Meeting",
                                    9: "Office",
                                    10: "Stair",
                                    11: "Corridor"
                                    },
                    'SuperMarket' : {
                                    0: "Sales/Produce",
                                    1: "DryStorage",
                                    2: "Office",
                                    3: "Deli/Bakery"
                                    },
                    'SecondarySchool' : {
                                    0: "Mechanical",
                                    1: "Library",
                                    2: "Auditorium",
                                    3: "Cafeteria",
                                    4: "Gym",
                                    5: "Restroom",
                                    6: "Office",
                                    7: "Classroom",
                                    8: "Kitchen",
                                    9: "Corridor",
                                    10: "Lobby"
                                    },
                    'Retail' : {
                                    0: "Back_Space",
                                    1: "Point_of_Sale",
                                    2: "Entry",
                                    3: "Retail"
                                    },
                    'Hospital' : {
                                    0: "ER_Trauma",
                                    1: "PatCorridor",
                                    2: "ICU_PatRm",
                                    3: "ER_NurseStn",
                                    4: "ICU_Open",
                                    5: "NurseStn",
                                    6: "PhysTherapy",
                                    7: "ICU_NurseStn",
                                    8: "Radiology",
                                    9: "Dining",
                                    10: "PatRoom",
                                    11: "OR",
                                    12: "Office",
                                    13: "Kitchen",
                                    14: "Lab",
                                    15: "ER_Exam",
                                    16: "ER_Triage",
                                    17: "Corridor",
                                    18: "Lobby"
                                    },
                    'Office' : {
                                    0: "BreakRoom",
                                    1: "Storage",
                                    2: "Vending",
                                    3: "OpenOffice",
                                    4: "ClosedOffice",
                                    5: "Conference",
                                    6: "PrintRoom",
                                    7: "Restroom",
                                    8: "Elec/MechRoom",
                                    9: "IT_Room",
                                    10: "Stair",
                                    11: "Corridor",
                                    12: "Lobby"
                                    },
                    'Warehouse' : {
                                    0: "Office",
                                    1: "Fine",
                                    2: "Bulk"
                                    },
                    'QuickServiceRestaurant' : {
                                    0: "Kitchen",
                                    1: "Dining"
                                    }
                    }


class EPSurfaceLib(object):
    # I think I can remove this now
    def __init__(self):
        # 4 represents an Air Wall
        self.srfType = {0:'WALL',
               1:'ROOF',
               2:'FLOOR',
               3:'CEILING',
               4:'WALL',
               5:'WINDOW'}
        
        # surface construction should change later
        # to be based on the zone program
        self.srfCnstr = {0:'Exterior_Wall',
                1:'Exterior_Roof',
                2:'Exterior_Floor',
                3:'Interior_Floor',
                4:'Air_Wall',
                5:'Exterior_Window'}
         
        self.srfBC = {0:'Outdoors',
                 1:'Outdoors',
                 2: 'Outdoors',
                 3: 'Adiabatic',
                 4: 'surface',
                 5: 'Outdoors'}
        
        self.srfSunExposure = {0:'SunExposed',
                 1:'SunExposed',
                 2:'SunExposed',
                 3:'NoSun',
                 4:'NoSun',
                 5:'SunExposed',}
    
        self.srfWindExposure = {0:'WindExposed',
                  1:'WindExposed',
                  2:'WindExposed',
                  3:'NoWind',
                  4:'NoWind',
                  5:'WindExposed'}


class EPZone(object):
    """This calss represents a honeybee zone that will be used for energy and daylighting
    simulatios"""
    
    def __init__(self, zoneBrep, zoneID, zoneName, program = [None, None], isConditioned = True):
        self.north = 0
        self.objectType = "HBZone"
        self.origin = rc.Geometry.Point3d.Origin
        self.geometry = zoneBrep
        
        self.num = zoneID
        self.name = zoneName
        self.hasNonPlanarSrf = False
        self.hasInternalEdge = False
        
        self.surfaces = []
        
        self.daylightThreshold = ""
        self.coolingSetPt= ""
        self.heatingSetPt= ""
        self.coolSupplyAirTemp= ""
        self.heatSupplyAirTemp= ""
        
        if zoneBrep != None:
            self.isClosed = self.geometry.IsSolid
        else:
            self.isClosed = False
        if self.isClosed:
            try:
                self.checkZoneNormalsDir()
            except Exception, e:
                print 'Checking normal directions failed:\n' + `e`
        
        self.bldgProgram = program[0]
        self.zoneProgram = program[1]
        
        # assign schedules
        self.assignScheduleBasedOnProgram()
        # assign loads
        self.assignLoadsBasedOnProgram()
        
        if isConditioned: self.HVACSystem = ["GroupI", 0] # assign ideal loads as default
        else: self.HVACSystem = ["NoHVAC", -1] # no system        
        
        self.isConditioned = isConditioned
        self.isThisTheTopZone = False
        self.isThisTheFirstZone = False
    
    def assignScheduleBasedOnProgram(self, component = None):
        # create an open office is the program is not assigned
        if self.bldgProgram == None: self.bldgProgram = "Office"
        if self.zoneProgram == None: self.zoneProgram = "OpenOffice"
        
        openStudioStandardLib = sc.sticky ["honeybee_OpenStudioStandardsFile"]
        
        try:
            schedulesAndLoads = openStudioStandardLib['space_types']['90.1-2007']['ClimateZone 1-8'][self.bldgProgram][self.zoneProgram]
        except:
            msg = "Either your input for bldgProgram > [" + self.bldgProgram + "] or " + \
                  "the input for zoneProgram > [" + self.zoneProgram + "] is not valid.\n" + \
                  "Use ListSpacePrograms component to find the available programs."
            print msg
            if component != None:
                component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
            return
        
        self.occupancySchedule = schedulesAndLoads['occupancy_sch']
        self.occupancyActivitySch = schedulesAndLoads['occupancy_activity_sch']
        self.heatingSetPtSchedule = schedulesAndLoads['heating_setpoint_sch']
        self.coolingSetPtSchedule = schedulesAndLoads['cooling_setpoint_sch']
        self.lightingSchedule = schedulesAndLoads['lighting_sch']
        self.equipmentSchedule = schedulesAndLoads['elec_equip_sch']
        self.infiltrationSchedule = schedulesAndLoads['infiltration_sch']
        
        # find all the patameters and assign them to 
        self.isSchedulesAssigned = True
    
    def assignLoadsBasedOnProgram(self, component=None):
        # create an open office is the program is not assigned
        if self.bldgProgram == None: self.bldgProgram = "Office"
        if self.zoneProgram == None: self.zoneProgram = "OpenOffice"
        
        openStudioStandardLib = sc.sticky ["honeybee_OpenStudioStandardsFile"]
        
        try:
            schedulesAndLoads = openStudioStandardLib['space_types']['90.1-2007']['ClimateZone 1-8'][self.bldgProgram][self.zoneProgram]
            
        except:
            msg = "Either your input for bldgProgram > [" + self.bldgProgram + "] or " + \
                  "the input for zoneProgram > [" + self.zoneProgram + "] is not valid.\n" + \
                  "Use ListSpacePrograms component to find the available programs."
            print msg
            if component != None:
                component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
            return
        
        # numbers in OpenStudio standard library are in IP and I have to convert them to SI!
        self.equipmentLoadPerArea = schedulesAndLoads['elec_equip_per_area'] * 10.763961 #Per ft^2 to Per m^2
        self.infiltrationRatePerArea = schedulesAndLoads['infiltration_per_area_ext'] * 0.00508001 #1 ft3/min.m2 = 5.08001016E-03 m3/s.m2
        self.lightingDensityPerArea = schedulesAndLoads['lighting_w_per_area'] * 10.763961 #Per ft^2 to Per m^2
        self.numOfPeoplePerArea = schedulesAndLoads[ 'occupancy_per_area'] * 10.763961 /1000 #Per 1000 ft^2 to Per m^2
        self.ventilationPerArea = schedulesAndLoads['ventilation_per_area'] * 0.00508001 #1 ft3/min.m2 = 5.08001016E-03 m3/s.m2
        self.ventilationPerPerson = schedulesAndLoads['ventilation_per_person'] * 0.0004719  #1 ft3/min.perosn = 4.71944743E-04 m3/s.person
        
        self.isLoadsAssigned = True
    
    def getCurrentSchedules(self, returnDictionary = False, component = None):
        # assign the default is there is no schedule assigned 
        if not self.isSchedulesAssigned:
            self.assignScheduleBasedOnProgram(component)
        
        if not returnDictionary:
            report = " Schedule list:\n" + \
            "occupancySchedule: " + str(self.occupancySchedule) + "\n" + \
            "occupancyActivitySch: " + str(self.occupancyActivitySch) + "\n" + \
            "heatingSetPtSchedule: " + str(self.heatingSetPtSchedule) + "\n" + \
            "coolingSetPtSchedule: " + str(self.coolingSetPtSchedule) + "\n" + \
            "lightingSchedule: " + str(self.lightingSchedule) + "\n" + \
            "equipmentSchedule: " + str(self.equipmentSchedule) + "\n" + \
            "infiltrationSchedule: " + str(self.infiltrationSchedule) + "."
            
            return report
        
        else:
            scheduleDict = {"occupancySchedule" : str(self.occupancySchedule),
                            "occupancyActivitySch" : str(self.occupancyActivitySch),
                            "heatingSetPtSchedule" :str(self.heatingSetPtSchedule),
                            "coolingSetPtSchedule" : str(self.coolingSetPtSchedule),
                            "lightingSchedule" : str(self.lightingSchedule),
                            "equipmentSchedule" : str(self.equipmentSchedule),
                            "infiltrationSchedule" : str(self.infiltrationSchedule)}
            
            return scheduleDict

    def getCurrentLoads(self,  returnDictionary = False, component = None):
        
        # assign the default is there is no schedule assigned
        if not self.isLoadsAssigned:
            self.assignLoadsBasedOnProgram(component)
        
        if not returnDictionary:
            report = " Internal Loads [SI]:\n" + \
            "EquipmentsLoadPerArea: " + "%.4f"%self.equipmentLoadPerArea + "\n" + \
            "infiltrationRatePerArea: " + "%.4f"%self.infiltrationRatePerArea + "\n" + \
            "lightingDensityPerArea: " + "%.4f"%self.lightingDensityPerArea + "\n" + \
            "numOfPeoplePerArea: " + "%.4f"%self.numOfPeoplePerArea + "\n" + \
            "ventilationPerPerson: " + "%.4f"%self.ventilationPerPerson + "\n" + \
            "ventilationPerArea: " + "%.4f"%self.ventilationPerArea + "."
            
            return report        
            
        else:
            
            loadsDict = {"EquipmentsLoadPerArea" : "%.4f"%self.equipmentLoadPerArea,
                         "infiltrationRatePerArea" : "%.4f"%self.infiltrationRatePerArea,
                         "lightingDensityPerArea" : "%.4f"%self.lightingDensityPerArea,
                         "numOfPeoplePerArea" : "%.4f"%self.numOfPeoplePerArea,
                         "ventilationPerArea" : "%.4f"%self.ventilationPerArea,
                         "ventilationPerPerson" : "%.4f"%self.ventilationPerPerson}
            
            return loadsDict
            
    def joinMesh(self, meshList):
        joinedMesh = rc.Geometry.Mesh()
        for m in meshList: joinedMesh.Append(m)
        return joinedMesh
    
    def checkZoneNormalsDir(self):
        # isPointInside for Breps is buggy, that's why I mesh the geometry here
        mesh = rc.Geometry.Mesh.CreateFromBrep(self.geometry)
        joinedMesh = self.joinMesh(mesh)
        
        """check normal direction of the surfaces"""
        MP3D = rc.Geometry.AreaMassProperties.Compute(self.geometry)
        self.cenPt = MP3D.Centroid
        MP3D.Dispose()
        
        #Check if the centroid is inside the volume.
        if joinedMesh.IsPointInside(self.cenPt, sc.doc.ModelAbsoluteTolerance, True) != True:
            # point is not inside so this method can't be used
            return
        
        # first surface of the geometry
        testSurface = self.geometry.Faces[0].DuplicateFace(False)
        srfCenPt, normal = self.getSrfCenPtandNormal(testSurface)
        
        #create a plane from the surface
        srfPlane = rc.Geometry.Plane(srfCenPt, normal)
        
        # project center point of the geometry to surface plane
        projectedPt = srfPlane.ClosestPoint(self.cenPt)
        
        try:
            # make a vector from the center point of the zone to center point of the surface
            testVector = rc.Geometry.Vector3d(projectedPt - self.cenPt)
            # check the direction of the vectors and flip zone surfaces if needed
            vecAngleDiff = math.degrees(rc.Geometry.Vector3d.VectorAngle(testVector, normal))
            
            # vecAngleDiff should be 0 otherwise the normal is reversed
            if vecAngleDiff > 10:
                self.geometry.Flip()
        except Exception, e:
            print 'Zone normal check failed!\n' + `e`
            return 
        
    def decomposeZone(self, maximumRoofAngle = 30):
        # this method is useufl when the zone is going to be constructed from a closed brep
        # materials will be applied based on the zones construction set

        # explode zone
        for i in range(self.geometry.Faces.Count):
            
            surface = self.geometry.Faces[i].DuplicateFace(False)
            # find the normal
            findNormal = self.getSrfCenPtandNormal(surface)
            if findNormal:
                normal = findNormal[1]
                angle2Z = math.degrees(rc.Geometry.Vector3d.VectorAngle(normal, rc.Geometry.Vector3d.ZAxis))
            else:
                #print findNormal
                #print self.geometry
                angle2Z = 0
            
            if  angle2Z < maximumRoofAngle or angle2Z > 360- maximumRoofAngle:
                # roof is the right assumption
                # it will change to ceiling after solveAdj if it is a ceiling
                surafceType = 1 #roof
                #if self.isThisTheTopZone: surafceType = 1 #roof
                #else:  surafceType = 3 # ceiling
            
            elif  160 < angle2Z <200:
                surafceType = 2 # floor
            
            else: surafceType = 0 #wall
            
            
            HBSurface = hb_EPZoneSurface(surface, i, self.name + '_Srf_' + `i`, self, surafceType)

            self.addSrf(HBSurface)
    
    def createZoneFromSurfaces(self, maximumRoofAngle = 30):
        # this method recreate the geometry from the surfaces
        srfs = []
        # check if surface has a type
        for srf in self.surfaces:
            srf.parent = self
            
            # check planarity and set it for parent zone
            if not srf.isPlanar:
                self.hasNonPlanarSrf = True
            if srf.hasInternalEdge:
                self.hasInternalEdge = True
            
            # also chek for interal Edges
            
            surface = srf.geometry.Faces[0].DuplicateFace(False)
            #print surface
            srfs.append(surface)
            try:
                surfaceType = srf.type
            except:
                srf.type = srf.getTypeByNormalAngle()
            
            srf.reEvaluateType(True)
            
            # check for child surfaces
            if srf.hasChild: srf.calculatePunchedSurface()
            
            # assign construction
            srf.construction = srf.cnstrSet[srf.type]
            if srf.EPConstruction == "":
                srf.EPConstruction = srf.construction
            
        try:
            self.geometry = rc.Geometry.Brep.JoinBreps(srfs, sc.doc.ModelAbsoluteTolerance)[0]
            self.isClosed = self.geometry.IsSolid
            if self.isClosed:
                try:
                    self.checkZoneNormalsDir()
                except Exception, e:
                    print '0_Check Zone Normals Direction Failed:\n' + `e`
            else:
                MP3D = rc.Geometry.AreaMassProperties.Compute(self.geometry)
                self.cenPt = MP3D.Centroid
                MP3D.Dispose()
        except Exception, e:
            print " Failed to create the geometry from the surface:\n" + `e`
        
    def getSrfCenPtandNormal(self, surface):
        
        surface = surface.Faces[0]
        u_domain = surface.Domain(0)
        v_domain = surface.Domain(1)
        centerU = (u_domain.Min + u_domain.Max)/2
        centerV = (v_domain.Min + v_domain.Max)/2
        
        centerPt = surface.PointAt(centerU, centerV)
        normalVector = surface.NormalAt(centerU, centerV)
        
        normalVector.Unitize()
        return centerPt, normalVector

    def addSrf(self, srf):
        self.surfaces.append(srf)
    
    def updateConstructionSet(newProgramCode, level = 1):
        """level defines the level of the construction set
        0: low performance; 1: normal; 2: high performance"""
        self.constructionSet = constructionSet[newProgramCode]
    
    def cleanMeshedFaces(self):
        for srf in self.surfaces: srf.disposeCurrentMeshes()
    
    def prepareNonPlanarZone(self, meshingParameters = None, isEnergyPlus = False):
        # clean current meshedFaces
        self.cleanMeshedFaces()
        # collect walls and windows, and roofs
        srfsToBeMeshed = []
        for srf in self.surfaces:
            #clean the meshedFaces if any
            
            # if surface is planar just collect the surface
            if srf.isPlanar or not srf.hasChild: srfsToBeMeshed.append(srf.geometry)
            # else collect the punched wall and child surfaces
            else:
                for fenSrf in srf.childSrfs:
                   srfsToBeMeshed.append(fenSrf.geometry)
                   srfsToBeMeshed.append(fenSrf.parent.punchedGeometry)
                   
        # join surfaces
        joinedBrep = rc.Geometry.Brep.JoinBreps(srfsToBeMeshed, sc.doc.ModelAbsoluteTolerance)[0]
        
        # mesh the geometry
        if meshingParameters == None:
            mp = rc.Geometry.MeshingParameters.Default; disFactor = 3
        else:
            disFactor = 1
            mp = meshingParameters
            
        meshedGeo = rc.Geometry.Mesh.CreateFromBrep(joinedBrep, mp)
        
        for mesh in meshedGeo:
            # generate quad surfaces for EnergyPlus model
            # if isEnergyPlus:
            #     angleTol = sc.doc.ModelAngleToleranceRadians
            #     minDiagonalRatio = .875
            #     #print mesh.Faces.ConvertTrianglesToQuads(angleTol, minDiagonalRatio)
            #     mesh.Faces.ConvertTrianglesToQuads(angleTol, minDiagonalRatio)
            
            mesh.FaceNormals.ComputeFaceNormals()
            #mesh.FaceNormals.UnitizeFaceNormals()
        
            for faceIndex in  range(mesh.Faces.Count):
                normal = mesh.FaceNormals[faceIndex]
                cenPt = mesh.Faces.GetFaceCenter(faceIndex)
                ##check mesh normal direction
                reverseList = False
                ## make a vector from the center point of the zone to center point of the surface
                testVector = rc.Geometry.Vector3d(cenPt - self.cenPt)
                ## check the direction of the vectors and flip zone surfaces if needed
                if rc.Geometry.Vector3d.VectorAngle(testVector, normal)> 1:
                    normal.Reverse()
                    reverseList = True
                ## create a ray
                #ray = rc.Geometry.Ray3d(cenPt, normal)
                for srf in self.surfaces:
                    if srf.isPlanar or not srf.hasChild:
                        ## shoot a ray from the center of the mesh to each surface
                        #intPt = rc.Geometry.Intersect.Intersection.RayShoot(ray, [srf.geometry], 1) 
                        #if intPt:
                        if cenPt.DistanceTo(srf.geometry.ClosestPoint(cenPt))<0.05 * disFactor:
                            srf.collectMeshFaces(mesh.Faces.GetFaceVertices(faceIndex), reverseList) ## if hit then add this face to that surface
                            break
                    else:
                        for fenSrf in srf.childSrfs:
                            #intPt = rc.Geometry.Intersect.Intersection.RayShoot(ray, [fenSrf.geometry], 1) 
                            #if intPt:
                            if cenPt.DistanceTo(fenSrf.geometry.ClosestPoint(cenPt))<0.05 * disFactor:
                                fenSrf.collectMeshFaces(mesh.Faces.GetFaceVertices(faceIndex), reverseList); break
                            #intPt = rc.Geometry.Intersect.Intersection.RayShoot(ray, [fenSrf.parent.punchedGeometry], 1)
                            #if intPt:
                            if cenPt.DistanceTo(fenSrf.parent.punchedGeometry.ClosestPoint(cenPt))<0.05 * disFactor:
                                srf.collectMeshFaces(mesh.Faces.GetFaceVertices(faceIndex), reverseList); break
    
    def getFloorArea(self):
        totalFloorArea = 0
        for HBSrf in self.surfaces:
            if int(HBSrf.type) == 2:
                totalFloorArea += HBSrf.getTotalArea()
        return totalFloorArea
    
    def getZoneVolume(self):
        return self.geometry.GetVolume()
    
    def getFloorZLevel(self):
        # useful for gbXML export
        minZ = float("inf")
        for HBSrf in self.surfaces:
            if int(HBSrf.type) == 2:
                #get the center point
                centerPt, normalVector = HBSrf.getSrfCenPtandNormalAlternate()
                
                if centerPt.Z < minZ: minZ = centerPt.Z
        return minZ
    
    def setName(self, newName):
        self.name = newName
    
    def __str__(self):
        try:
            return 'Zone name: ' + self.name + \
               '\nZone program: ' + self.bldgProgram + "::" + self.zoneProgram + \
               '\n# of surfaces: ' + `len(self.surfaces)` + \
               '\n-------------------------------------'
        except:
            return 'Zone name: ' + self.name + \
               '\nZone program: Unknown' + \
               '\n# of surfaces: ' + `len(self.surfaces)` + \
               '\n-------------------------------------'

class hb_reEvaluateHBZones(object):
    """
    This class check Honeybee zones once more and zones with nonplanar surfaces
    or non-rectangualr glazings recreates the surfaces so the output zones will
    be all zones with planar surfaces, and they can be exported with two functions
    for planar EPSurfaces and planar fenestration.
    
    It also assigns the right boundary condition object to each sub surface
    and checks duplicate names for zones and surfaces and give a warning
    to user to get them fixed.
    """
    
    def __init__(self, inHBZones, meshingParameters):
        # import the classes
        self.hb_EPZone = sc.sticky["honeybee_EPZone"]
        self.hb_EPSrf = sc.sticky["honeybee_EPSurface"]
        self.hb_EPZoneSurface = sc.sticky["honeybee_EPZoneSurface"]
        self.hb_EPFenSurface = sc.sticky["honeybee_EPFenSurface"]
        
        self.fakeSurface = rc.Geometry.Brep.CreateFromCornerPoints(
                                            rc.Geometry.Point3d(0,0.5,0),
                                            rc.Geometry.Point3d(-0.5,-0.5,0),
                                            rc.Geometry.Point3d(0.5,-0.5,0),
                                            sc.doc.ModelAbsoluteTolerance)
        self.originalHBZones = inHBZones
        self.meshingParameters = meshingParameters
        #self.triangulate = triangulate
        self.zoneNames = []
        self.srfNames = []
        self.modifiedSrfsNames= []
        self.modifiedGlzSrfsNames = []
        self.adjcGlzSrfCollection = []
        self.adjcSrfCollection = {} #collect adjacent surfaces for nonplanar surfaces
    
    def checkSrfNameDuplication(self, surface):
        if surface.name in self.srfNames:
                warning = "Duplicate surface name!"
                print warning
                # return -1
        else:
            self.srfNames.append(surface.name)            
        
        if not surface.isChild and surface.hasChild:
            for child in surface.childSrfs:
                self.checkSrfNameDuplication(child)
                    
    def checkNameDuplication(self, HBZone):
        
        if HBZone.name in self.zoneNames:
            warning = "Duplicate zone name!"
            print warning
            # return -1
        else:
            self.zoneNames.append(HBZone.name)            
        
        for surface in HBZone.surfaces:
            self.checkSrfNameDuplication(surface)
    
    def prepareNonPlanarZones(self, HBZone):
        # prepare nonplanar zones
        if  HBZone.hasNonPlanarSrf or  HBZone.hasInternalEdge:
             HBZone.prepareNonPlanarZone(self.meshingParameters)
    
    
    def createSurface(self, pts):
        """
        # it takes so long if I generate the geometry
        
        if len(pts) == 3:
            return rc.Geometry.Brep.CreateFromCornerPoints(pts[0], pts[1], pts[2], sc.doc.ModelAbsoluteTolerance)
        elif len(pts) == 4:
            return rc.Geometry.Brep.CreateFromCornerPoints(pts[0], pts[1], pts[2], pts[3], sc.doc.ModelAbsoluteTolerance)
        else:
            # create a planar surface
            pts.append(pts[0])
            pl = rc.Geometry.Polyline(pts).ToNurbsCurve()
            return rc.Geometry.Brep.CreatePlanarBreps([pl])[0]
        """
        return self.fakeSurface
        
    def evaluateZones(self):
        for HBZone in self.originalHBZones:
            self.checkNameDuplication(HBZone)
            self.prepareNonPlanarZones(HBZone)
            
            modifiedSurfaces = []
            for surface in HBZone.surfaces:
                srfs = self.checkZoneSurface(surface)
                try: modifiedSurfaces.extend(srfs)
                except: modifiedSurfaces.append(srfs)
            
            # replace surfaces with new ones
            HBZone.surfaces = []
            for HBSrf in modifiedSurfaces:
                HBZone.surfaces.append(HBSrf)
    
    def createSubSurfaceFromBaseSrf(self, surface, newSurfaceName, count, coordinates, glazingBase = False, nameAddition = None):
        
        # pass the wrong geometry for now. I assume creating planar surface from
        # coordinates will be computationally heavy and at this point geometry doesn't
        # matter, since I have the coordinates.
        newSurface = self.hb_EPZoneSurface(self.createSurface(coordinates),
                                           count, newSurfaceName, surface.parent, surface.type)
        newSurface.coordinates = coordinates
        newSurface.type = surface.type # protect the surface from reEvaluate
        newSurface.construction = surface.construction
        newSurface.BC = surface.BC
        newSurface.sunExposure = surface.sunExposure
        newSurface.windExposure = surface.windExposure
        newSurface.groundViewFactor = surface.groundViewFactor
        
        if surface.BC.upper() == 'SURFACE':
            adjcSurface = surface.BCObject
            
            if not glazingBase:
                newAdjcSurfaceName = adjcSurface.name + "_" + `count`
            else:
                newAdjcSurfaceName = adjcSurface.name + nameAddition
            
            newAdjcSurface = self.hb_EPZoneSurface(self.createSurface(coordinates),
                                           count, newAdjcSurfaceName, adjcSurface.parent, adjcSurface.type)
            # reverse the order of points
            restOfcoordinates = coordinates[1:]
            restOfcoordinates.reverse()
            newAdjcSurface.coordinates = [coordinates[0]] + restOfcoordinates
            newAdjcSurface.type = adjcSurface.type
            newAdjcSurface.construction = adjcSurface.construction
            newAdjcSurface.BC = adjcSurface.BC
            newAdjcSurface.sunExposure = adjcSurface.sunExposure
            newAdjcSurface.windExposure = adjcSurface.windExposure
            newAdjcSurface.groundViewFactor = adjcSurface.groundViewFactor
        
            # assign boundary objects
            newSurface.BCObject = newAdjcSurface
            newAdjcSurface.BCObject = newSurface
            
            self.adjcSrfCollection[adjcSurface.name].append(newAdjcSurface)
            
        return newSurface
    
    def createSubGlzSurfaceFromBaseSrf(self, baseChildSurface, parentSurface, glzSurfaceName, count, coordinates):
        
        newFenSrf = self.hb_EPFenSurface(self.createSurface(coordinates),
                                    count, glzSurfaceName, parentSurface, 5, punchedWall = None)
        
        newFenSrf.coordinates = coordinates
        newFenSrf.type = baseChildSurface.type
        newFenSrf.construction = baseChildSurface.construction
        newFenSrf.parent = parentSurface
        newFenSrf.groundViewFactor = baseChildSurface.groundViewFactor
        newFenSrf.shadingControlName = baseChildSurface.shadingControlName
        newFenSrf.frameName = baseChildSurface.frameName
        newFenSrf.Multiplier = baseChildSurface.Multiplier
        
        # Will be overwritten later if needed
        newFenSrf.BCObject = baseChildSurface.BCObject
        newFenSrf.BCObject = baseChildSurface.BCObject
        
        return newFenSrf
        
    def getInsetGlazingCoordinates(self, glzCoordinates):
        # find the coordinates
        def averagePts(ptList):
            pt = rc.Geometry.Point3d(0,0,0)
            for p in ptList: pt = pt + p
            return rc.Geometry.Point3d(pt.X/len(ptList), pt.Y/len(ptList), pt.Z/len(ptList))
            
        distance = 2 * sc.doc.ModelAbsoluteTolerance
        # offset was so slow so I changed the method to this
        pts = []
        for pt in glzCoordinates:
            pts.append(rc.Geometry.Point3d(pt.X, pt.Y, pt.Z))
        cenPt = averagePts(pts)
        insetPts = []
        for pt in pts:
            movingVector = rc.Geometry.Vector3d(cenPt-pt)
            movingVector.Unitize()
            newPt = rc.Geometry.Point3d.Add(pt, movingVector * 2 * sc.doc.ModelAbsoluteTolerance)
            insetPts.append(newPt)
        
        return insetPts
            
    def checkChildSurfaces(self, surface):
        
        def isRectangle(ptList):
            if ptList[0].DistanceTo(ptList[2]) == ptList[1].DistanceTo(ptList[3]):
                return True
            else:
                return False
        
        # get glaing coordinates- coordinates will be returned as lists of lists
        glzCoordinates = surface.extractGlzPoints()
        glzSrfs = []
        if surface.isPlanar:
            
            for count, coordinates in enumerate(glzCoordinates):
                try: child = surface.childSrfs[count]
                except: child = surface.childSrfs[0]
                
                if len(glzCoordinates) == 1: #not hasattr(glzCoordinates, '__iter__'):
                    # single rectangular glazing - All should be fine
                    # also the adjacent surface will be fine by itself
                    child.coordinates = coordinates
                    self.modifiedGlzSrfsNames.append(child.name)                        
                else:
                    # surface is planar but glazing is not rectangular
                    # and so it is meshed now and is multiple glazing
                    glzSurfaceName = "glzSrf_" + `count` + "_" + surface.name
                    
                    # create glazing surface
                    HBGlzSrf = self.createSubGlzSurfaceFromBaseSrf(child, surface, glzSurfaceName, count, coordinates)
                    
                    # create adjacent glazingin case needed
                    if surface.BC.upper() == 'SURFACE':
                        # add glazing to adjacent surface
                        if count == 0:
                            adjcSrf = surface.BCObject
                            adjcSrf.childSrfs = []
                        
                        # add glazing to adjacent surface
                        adjcSrf = surface.BCObject
                        glzAdjcSrfName = "glzSrf_" + `count` + "_" + adjcSrf.name
                            
                        adjcGlzPt = glzCoordinates[1:]
                        adjcGlzPt.reverse()
                        adjcGlzPt = [glzCoordinates[0]] + adjcGlzPt

                        adjHBGlzSrf = self.createSubGlzSurfaceFromBaseSrf(child, adjcSrf, glzAdjcSrfName, count, adjcGlzPt)
                        
                        # overwrite BC Object
                        adjHBGlzSrf.BCObject = HBGlzSrf
                        HBGlzSrf.BCObject = adjHBGlzSrf
                        
                        adjcSrf.addChildSrf(adjHBGlzSrf)
                    
                    # collect surfaces
                    glzSrfs.append(HBGlzSrf)
            
            # add to parent surface
            if len(glzCoordinates) != 1:
                surface.removeAllChildSrfs()
                surface.addChildSrf(glzSrfs)
          
        else:
            
            # convert nonplanar surface to planar wall surfaces with offset glazing
            # and treat them similar to other surfaces except the fact that if it has
            # another surface next to it the surface should be generated regardless of
            # being single geometry or not
            newSurfaces =[]
            count = 0
            baseChildSrf = surface.childSrfs[0]
            
                
            for count, glzCoordinate in enumerate(glzCoordinates):
                # check if the points are recetangle
                if len(glzCoordinate) == 3 or isRectangle(glzCoordinate):
                    insetGlzCoordinates = [glzCoordinate]
                else:
                    # triangulate
                    insetGlzCoordinates = [glzCoordinate[:3], [glzCoordinate[0],glzCoordinate[2],glzCoordinate[3]]]
                
                for glzCount, insetGlzCoordinate in enumerate(insetGlzCoordinates):
                    
                    # self.modifiedGlzSrfsNames.append(child.name)
                    # create new Honeybee surfaces as parent surface for glass face
                    if len(insetGlzCoordinates) == 1:
                        newSurfaceName = surface.name + '_glzP_' + `count`
                    else:
                        newSurfaceName = surface.name + '_glzP_' + `count` + '_' + `glzCount`
                        
                    newSurface = self.createSubSurfaceFromBaseSrf(surface, newSurfaceName, count, insetGlzCoordinate, glazingBase = True, nameAddition = '_glzP_' + `count` + '_' + `glzCount`)
                    
                    # collect them here so it will have potential new BC
                    newSurfaces.append(newSurface)
                    
                    # create glazing coordinate and add it to the parent surface
                    insetPts = self.getInsetGlazingCoordinates(insetGlzCoordinate)

                    # create new window and go for it
                    glzSurfaceName = "glzSrf_" + `count` + "_" + newSurface.name
                    
                    HBGlzSrf = self.createSubGlzSurfaceFromBaseSrf(baseChildSrf, newSurface, glzSurfaceName, count, insetPts)
                    
                    if surface.BC.upper() == 'SURFACE':
                        # add glazing to adjacent surface
                        if count == 0:
                            adjcSrf = newSurface.BCObject
                            adjcSrf.childSrfs = []
                        
                        # add glazing to adjacent surface
                        adjcSrf = newSurface.BCObject
                        glzAdjcSrfName = "glzSrf_" + `count` + "_" + adjcSrf.name
                            
                        adjcGlzPt = insetPts[1:]
                        adjcGlzPt.reverse()
                        adjcGlzPt = [insetPts[0]] + adjcGlzPt

                        adjHBGlzSrf = self.createSubGlzSurfaceFromBaseSrf(baseChildSrf, adjcSrf, glzAdjcSrfName, count, adjcGlzPt)
                        
                        # overwrite BC Object
                        adjHBGlzSrf.BCObject = HBGlzSrf
                        HBGlzSrf.BCObject = adjHBGlzSrf
                        
                        adjcSrf.addChildSrf(adjHBGlzSrf)
                        
                    # add to parent surface
                    newSurface.addChildSrf(HBGlzSrf)                        
            
            return newSurfaces
        
    def checkZoneSurface(self, surface):
        if not hasattr(surface, 'coordinates'):
            coordinatesL = surface.extractPoints()
        else:
            coordinatesL = surface.coordinates
        
        # case 0 : it is a planar surface so it is all fine
        if not hasattr(coordinatesL[0], '__iter__'):
            # it is a single surface so just let it go to the modified list
            surface.coordinates = coordinatesL
            self.modifiedSrfsNames.append(surface.name)
            if  not surface.isChild and surface.hasChild:
                self.checkChildSurfaces(surface)
            return surface
            
        # case 1 : it is not planar
        else:
            
            # case 1-1 : surface is a nonplanar surface and adjacent to another surface
            # sub surfaces has been already generated based on the adjacent surface
            if surface.BC.upper() == 'SURFACE' and surface.name in self.adjcSrfCollection.keys():
                    # print "collecting sub surfaces for surface " + surface.name
                    # surface has been already generated by the other adjacent surface
                    self.modifiedSrfsNames.append(surface.name)
                    return self.adjcSrfCollection[surface.name]
                    
            # case 1-2 : surface is a nonplanar surface and adjacent to another surface
            # and hasn't been generated so let's generate this surface and the adjacent one
            elif surface.BC.upper() == 'SURFACE':
                adjcSurface= surface.BCObject
                # find adjacent zone and create the surfaces
                # create a place holder for the surface
                # the surfaces will be collected inside the function
                self.adjcSrfCollection[adjcSurface.name] = []
                
            self.modifiedSrfsNames.append(surface.name)
            newSurfaces = []
            for count, coordinates in enumerate(coordinatesL):
                # create new Honeybee surfaces
                # makes sense to copy the original surface here but since
                # copy.deepcopy fails on a number of systems I just create
                # a new surface and assign necessary data to write the surface
                
                newSurfaceName = surface.name + "_" + `count`
                
                newSurface = self.createSubSurfaceFromBaseSrf(surface, newSurfaceName, count, coordinates)
                
                newSurfaces.append(newSurface)
                
            # nonplanar surface
            if  not surface.isChild and surface.hasChild:
                
                glzPSurfaces = self.checkChildSurfaces(surface)
                
                if glzPSurfaces != None:
                    newSurfaces += glzPSurfaces
                
            return newSurfaces


class hb_EPSurface(object):
    def __init__(self, surface, srfNumber, srfID, *arg):
        """EP surface Class
            surface: surface geometry as a Brep
            srfNumber: a unique number that is only for this surface
            srfID: the unique name for this surface
            *arg is parentZone for EPZoneClasses
            *arg is parentSurface for child surfaces"""
        
        self.objectType = "HBSurface"
        self.geometry = surface
        self.num = srfNumber
        
        self.name = srfID
        
        self.isPlanar = self.checkPlanarity()
        self.hasInternalEdge = self.checkForInternalEdge()
        self.meshedFace = rc.Geometry.Mesh()
        self.RadMaterial = None
        self.EPConstruction = None # this gets overwritten below
        
        self.cenPt, self.normalVector = self.getSrfCenPtandNormalAlternate()
        
        # define if type and BC is defined by user and should be kept
        self.srfTypeByUser = False
        self.srfBCByUser = False
        
                # 4 represents an Air Wall
        self.srfType = {0:'WALL',
           0.5: 'UndergroundWall',
           1:'ROOF',
           1.5: 'UndergroundCeiling',
           2:'FLOOR',
           2.25: 'UndergroundSlab',
           2.5: 'SlabOnGrade',
           2.75: 'ExposedFloor',
           3:'CEILING',
           4:'WALL',
           5:'WINDOW',
           6:'SHADING',
           'WALL': 'WALL',
           'ROOF':'ROOF',
           'FLOOR': 'FLOOR',
           'CEILING': 'CEILING',
           'WINDOW':'WINDOW',
           'SHADING': 'SHADING'}
           
        self.cnstrSet = {0:'Exterior Wall',
                0.5: 'Exterior Wall',
                1: 'Exterior Roof',
                1.5: 'Exterior Roof',
                2:'Interior Floor',
                2.25: 'Exterior Floor',
                2.5: 'Exterior Floor',
                2.75: 'Exterior Floor',
                3:'Interior Ceiling',
                4:'Air Wall',
                5:'Exterior Window',
                6:'Interior Wall'}
        
        self.intCnstrSet = {
                0:'Interior Wall',
                0.5: 'Exterior Wall',
                1:'Exterior Roof',
                1.5:'Exterior Roof',
                2:'Interior Floor',
                2.25: 'Exterior Floor',
                2.5: 'Exterior Floor',
                2.75: 'Exterior Floor',
                3:'Interior Ceiling',
                4:'Air Wall',
                5:'Interior Window',
                6:'Interior Wall'}
        
        self.srfBC = {0:'Outdoors',
                     0.5: 'ground',
                     1:'Outdoors',
                     1.5: 'ground',
                     2: 'outdoors', # this will be changed to surface once solveAdjacency is used 
                     2.25: 'ground',
                     2.5: 'ground',
                     2.75: 'outdoors',
                     3: 'outdoors', # this will be changed to surface once solveAdjacency is used 
                     4: 'surface',
                     5: 'Outdoors',
                     6: 'surface'}
         
        self.srfSunExposure = {0:'SunExposed',
                     0.5:'NoSun',
                     1:'SunExposed',
                     1.5:'NoSun', 
                     2:'NoSun',
                     2.25: 'NoSun',
                     2.5: 'NoSun',
                     2.75: 'SunExposed',
                     3:'NoSun',
                     4:'NoSun',
                     6: 'NoSun'}
             
        self.srfWindExposure = {0:'WindExposed',
                     0.5:'NoWind',
                     1:'WindExposed',
                     1.5:'NoWind',
                     2:'NoWind',
                     2.25:'NoWind',
                     2.5:'NoWind',
                     2.75:'WindExposed',
                     3:'NoWind',
                     4:'NoWind',
                     6:'NoWind'}
        
        self.numOfVertices = 'autocalculate'
        
        if len(arg) == 0:
            # minimum surface
            # A minimum surface is a surface that will be added to a zone later
            # or is a surface that will only be used for daylighting simulation
            # so the concept of parent zone/surface is irrelevant
            self.parent = None
            self.reEvaluateType(True)
        elif len(arg) == 1:
            # represents an opening. The parent is the parent surafce
            # honeybee only supports windows (and not doors) at this point so
            # the type is always the same (window)
            self.parent = arg[0]
        elif len(arg) == 2:
            # represents a normal EP surface
            # parent is a parent zone and the type differs case by case
            self.parent = arg[0] # parent zone
            self.type = arg[1] # surface type (e.g. wall, roof,...)
            self.BC = self.srfBC[self.type] # initial BC based on type
            # check for special conditions(eg. slab underground, slab on ground
            
            self.reEvaluateType(True) # I should give this another thought
            
            # this should be fixed to be based on zone type
            # I can remove default constructions at some point
            self.construction = self.cnstrSet[int(self.type)]
            self.EPConstruction = self.construction
        
    def checkPlanarity(self):
        # planarity tolerance should change for different 
        return self.geometry.Faces[0].IsPlanar(1e-3)
    
    def checkForInternalEdge(self):
        edges = self.geometry.DuplicateEdgeCurves(True)
        edgesJoined = rc.Geometry.Curve.JoinCurves(edges)
        if len(edgesJoined)>1:
            return True
        else:
            return False
    
    class outdoorBCObject(object):
        """
        BCObject for surfaces with outdoor BC
        """
        def __init__(self, name = ""):
            self.name = name
    
    def getAngle2North(self):
        types = [0, 4, 5] # vertical surfaces
        northVector = rc.Geometry.Vector3d.YAxis
        
        # rotate north based on the zone north vector
        try: northVector.Rotate(math.radians(self.parent.north), rc.Geometry.Vector3d.ZAxis)
        except: pass
        
        normalVector = self.getSrfCenPtandNormalAlternate()[1]
        if self.type in types:
            angle =  rc.Geometry.Vector3d.VectorAngle(northVector, normalVector, rc.Geometry.Plane.WorldXY)
        #if normalVector.X < 0: angle = (2* math.pi) - angle
        else: angle = 0
        self.angle2North = math.degrees(angle)
    
    def findDiscontinuity(self, curve, style):
        # copied and modified from rhinoScript (@Steve Baer @GitHub)
        """Search for a derivatitive, tangent, or curvature discontinuity in
        a curve object.
        Parameters:
          curve_id = identifier of curve object
          style = The type of continuity to test for. The types of
              continuity are as follows:
              Value    Description
              1        C0 - Continuous function
              2        C1 - Continuous first derivative
              3        C2 - Continuous first and second derivative
              4        G1 - Continuous unit tangent
              5        G2 - Continuous unit tangent and curvature
        Returns:
          List 3D points where the curve is discontinuous
        """
        dom = curve.Domain
        t0 = dom.Min
        t1 = dom.Max
        points = []
        get_next = True
        while get_next:
            get_next, t = curve.GetNextDiscontinuity(System.Enum.ToObject(rc.Geometry.Continuity, style), t0, t1)
            if get_next:
                points.append(curve.PointAt(t))
                t0 = t # Advance to the next parameter
        return points
    
    def extractMeshPts(self, mesh, triangulate = False):
        coordinatesList = []
        for face in  range(mesh.Faces.Count):
            # get each mesh surface vertices
            if mesh.Faces.GetFaceVertices(face)[3] != mesh.Faces.GetFaceVertices(face)[4]:
                meshVertices = mesh.Faces.GetFaceVertices(face)[1:5]
                # triangulation
                if triangulate:
                    coordinatesList.append(meshVertices[:3])
                    coordinatesList.append([meshVertices[0], meshVertices[2], meshVertices[3]])
                else:
                    coordinatesList.append(list(meshVertices))
            else:
                meshVertices = mesh.Faces.GetFaceVertices(face)[1:4]
                coordinatesList.append(list(meshVertices))
        #print len(coordinatesList)
        #coordinatesList.reverse()
        return coordinatesList
    
    def extractPoints(self, method = 1, triangulate = False):
        if not self.meshedFace.IsValid:
            if self.isPlanar:
                meshPar = rc.Geometry.MeshingParameters.Coarse
                meshPar.SimplePlanes = True
            else:
                meshPar = rc.Geometry.MeshingParameters.Smooth
            
            self.meshedFace = rc.Geometry.Mesh.CreateFromBrep(self.geometry, meshPar)[0]
            
        if self.meshedFace.IsValid or self.hasInternalEdge:
            if self.isPlanar and not self.hasInternalEdge:
                plSegments = self.meshedFace.GetNakedEdges()
                segments = []
                [segments.append(seg.ToNurbsCurve()) for seg in plSegments]
            else:
                return self.extractMeshPts(self.meshedFace,triangulate)
        else:
            segments = self.geometry.DuplicateEdgeCurves(True)
        
        joinedBorder = rc.Geometry.Curve.JoinCurves(segments)
            
        if method == 0:
            pts = []
            [pts.append(seg.PointAtStart) for seg in segments]
        else:
            pts = []
            pts.append(joinedBorder[0].PointAtStart)
            restOfpts = self.findDiscontinuity(joinedBorder[0], style = 4)
            # for some reason restOfPts returns no pt!
            try: pts.extend(restOfpts)
            except: pass
            try: centPt, normalVector = self.getSrfCenPtandNormalAlternate()
            except:  centPt, normalVector = self.parent.getSrfCenPtandNormal(self.geometry)
        
        basePlane = rc.Geometry.Plane(centPt, normalVector)
        
        # inclusion test
        if str(joinedBorder[0].Contains(centPt, basePlane)).lower() != "inside":
            # average points
            cumPt = rc.Geometry.Point3d(0,0,0)
            for pt in pts: cumPt += pt
            centPt = cumPt/len(pts)
            # move basePlane to the new place
            basePlane = rc.Geometry.Plane(centPt, normalVector)
        
        # sort based on parameter on curve
        pointsSorted = sorted(pts, key =lambda pt: joinedBorder[0].ClosestPoint(pt)[1])
        
        def isClockWise(pts, basePlane):
            vector0 = rc.Geometry.Vector3d(pts[0]- basePlane.Origin)
            vector1 = rc.Geometry.Vector3d(pts[1]- basePlane.Origin)
            vector2 =  rc.Geometry.Vector3d(pts[-1]- basePlane.Origin)
            if rc.Geometry.Vector3d.VectorAngle(vector0, vector1, basePlane) < rc.Geometry.Vector3d.VectorAngle(vector0, vector2, basePlane):
                return True
            return False
            
        # check if clockWise and reverse the list in case it is
        if not isClockWise(pointsSorted, basePlane): pointsSorted.reverse()
        

        # in case the surface still doesn't have a type
        # it happens for radiance surfaces. For EP it won't happen
        # as it has been already assigned based on the zone
        if not hasattr(self, 'type'):
            self.Type = self.getTypeByNormalAngle()
        
        ## find UpperRightCorner point
        ## I'm changin this to find the LowerLeftCorner point
        ## instead as it is how gbXML needs it
        
        # check the plane
        srfType = self.getTypeByNormalAngle()
        rotationCount = 0
        if srfType == 0:
            # vertical surface
            while basePlane.YAxis.Z <= sc.doc.ModelAbsoluteTolerance and rotationCount < 3:
                # keep rotating for 90 degrees
                basePlane.Rotate(math.radians(90), basePlane.ZAxis)
                rotationCount += 1
                
        elif srfType == 1 or  srfType == 3:            
            # roof + ceiling
            while basePlane.YAxis.Y <=  sc.doc.ModelAbsoluteTolerance and rotationCount < 3:
                # keep rotating for 90 degrees
                basePlane.Rotate(math.radians(90), basePlane.ZAxis)
                rotationCount += 1
                
        elif srfType == 2:
            # floor
            while basePlane.YAxis.Y >= sc.doc.ModelAbsoluteTolerance and rotationCount < 3:
                # keep rotating for 90 degrees
                basePlane.Rotate(math.radians(90), basePlane.ZAxis)
                rotationCount += 1
                
        # remap point on the new plane
        remPts = []
        for pt in pointsSorted: remPts.append(basePlane.RemapToPlaneSpace(pt)[1])
        
        # find UpperRightCorner point (x>0 and max y)
        firstPtIndex = None
        #for ptIndex, pt in enumerate(remPts):
        #    if pt.X > 0 and pt.Y > 0 and firstPtIndex == None:
        #        firstPtIndex = ptIndex #this could be the point
        #    elif pt.X > 0 and pt.Y > 0:
        #        if pt.Y > remPts[firstPtIndex].Y: firstPtIndex = ptIndex
        
        for ptIndex, pt in enumerate(remPts):
            if pt.X < 0 and pt.Y < 0 and firstPtIndex == None:
                firstPtIndex = ptIndex #this could be the point
            elif pt.X < 0 and pt.Y < 0:
                if pt.Y < remPts[firstPtIndex].Y: firstPtIndex = ptIndex
        
        
        if firstPtIndex!=None and firstPtIndex!=0:
            pointsSorted = pointsSorted[firstPtIndex:] + pointsSorted[:firstPtIndex]
        
        return list(pointsSorted)

    def extractGlzPoints(self, RAD = False, method = 2):
        glzCoordinatesList = []
        for glzSrf in self.childSrfs:
            sortedPoints = glzSrf.extractPoints()
            # check numOfPoints
            if len(sortedPoints) < 4 or (self.isPlanar and RAD==True):
                glzCoordinatesList.append(sortedPoints) #triangle
            elif len(sortedPoints) == 4 and self.isPlanar and abs(sortedPoints[0].DistanceTo(sortedPoints[2]) - sortedPoints[1].DistanceTo(sortedPoints[3]))< sc.doc.ModelAbsoluteTolerance:
                glzCoordinatesList.append(sortedPoints) #rectangle
            else:
                if method == 1:
                    sortedPoints.append(sortedPoints[0])
                    border = rc.Geometry.Polyline(sortedPoints)
                    mesh = rc.Geometry.Mesh.CreateFromClosedPolyline(border)
                elif method == 2:
                    mp = rc.Geometry.MeshingParameters.Smooth
                    mesh = rc.Geometry.Mesh.CreateFromBrep(glzSrf.geometry, mp)[0]
                if mesh:
                    # Make sure non-rectangular shapes with 4 edges will be triangulated
                    if len(sortedPoints) == 4 and self.isPlanar: triangulate= True
                    else: triangulate= False
                    
                    glzCoordinatesList = self.extractMeshPts(mesh, triangulate)
                    
        return glzCoordinatesList
    
    def collectMeshFaces(self, meshVertices, reverseList = False):
        mesh = rc.Geometry.Mesh()
        if meshVertices[3]!= meshVertices[4:]:
            mesh.Vertices.Add(meshVertices[1]) #0
            mesh.Vertices.Add(meshVertices[2]) #1
            mesh.Vertices.Add(meshVertices[3]) #2
            mesh.Vertices.Add(meshVertices[4]) #3
            if not reverseList: mesh.Faces.AddFace(0, 1, 2, 3)
            else: mesh.Faces.AddFace(0, 1, 2, 3)
        else:
            mesh.Vertices.Add(meshVertices[1]) #0
            mesh.Vertices.Add(meshVertices[2]) #1
            mesh.Vertices.Add(meshVertices[3]) #2
            if not reverseList: mesh.Faces.AddFace(0, 1, 2)
            else: mesh.Faces.AddFace(0, 1, 2)
        
        self.meshedFace.Append(mesh)
        #print self.meshedFace.Faces.Count
    
    def disposeCurrentMeshes(self):
        if self.meshedFace.Faces.Count>0:
            self.meshedFace.Dispose()
            self.meshedFace = rc.Geometry.Mesh()
        if self.hasChild:
            for fenSrf in self.childSrfs:
                if fenSrf.meshedFace.Faces.Count>0:
                    fenSrf.meshedFace.Dispose()
                    fenSrf.meshedFace = rc.Geometry.Mesh()
    
    def getSrfCenPtandNormalAlternate(self):
        surface = self.geometry.Faces[0]
        u_domain = surface.Domain(0)
        v_domain = surface.Domain(1)
        centerU = (u_domain.Min + u_domain.Max)/2
        centerV = (v_domain.Min + v_domain.Max)/2
        
        centerPt = surface.PointAt(centerU, centerV)
        normalVector = surface.NormalAt(centerU, centerV)
        
        normalVector.Unitize()
        
        return centerPt, normalVector
    
    def isUnderground(self, wall = False):
        """
        check if this surface is underground
        """
        # extract points
        coordinatesList = self.extractPoints()
        # create a list of list
        if type(coordinatesList[0])is not list and type(coordinatesList[0]) is not tuple:
            coordinatesList = [coordinatesList]
        
        for ptList in coordinatesList:
            for pt in ptList:
                if not wall and pt.Z - rc.Geometry.Point3d.Origin.Z >= sc.doc.ModelAbsoluteTolerance: return False
                elif pt.Z >= sc.doc.ModelAbsoluteTolerance: return False
        return True
        
    def isOnGrade(self):
        """
        check if this surface is underground
        """
        # extract points
        coordinatesList = self.extractPoints()
        # create a list of list
        if type(coordinatesList[0])is not list and type(coordinatesList[0]) is not tuple:
            coordinatesList = [coordinatesList]
        
        for ptList in coordinatesList:
            for pt in ptList:
                if abs(pt.Z - rc.Geometry.Point3d.Origin.Z) >= sc.doc.ModelAbsoluteTolerance: return False
        return True
        
    def reEvaluateType(self, overwrite= True):
        """
        Find special surface types
        """
        if not overwrite and hasattr(self, "type"): return self.type
        
        if self.srfTypeByUser: return self.type
        
        if self.srfBCByUser: return self.type
        
        # find initial type it has no type yet
        if not hasattr(self, "type"):
            self.type = self.getTypeByNormalAngle()
            self.BC = "OUTDOORS"
            
        if self.type == 0:
            if self.isUnderground(True):
                self.type += 0.5 #UndergroundWall
                self.BC = "GROUND"
                
        elif self.type == 1:
            # A roof underground will be assigned as UndergroundCeiling!
            if self.isUnderground():
                self.type += 0.5 #UndergroundCeiling
                self.BC = "GROUND"
            elif self.BC.upper() == "SURFACE":
                self.type == 3 # ceiling
            
        elif self.type == 2:
            # floor
            if self.isOnGrade():
                self.type += 0.5 #SlabOnGrade
                self.BC = "GROUND"
            elif self.isUnderground():
                self.type += 0.25 #UndergroundSlab
                self.BC = "GROUND"
            elif self.BC.upper() != "SURFACE":
                self.type += 0.75 #Exposed floor
        
        # update boundary condition based on new type
        self.BC = self.srfBC[self.type]
        
    def getTypeByNormalAngle(self, maximumRoofAngle = 30):
        # find the normal
        try: findNormal = self.getSrfCenPtandNormalAlternate()
        except: findNormal = self.parent.getSrfCenPtandNormal(self.geometry) #I should fix this at some point - Here just for shading surfaces for now
        
        if findNormal:
            try:
                normal = findNormal[1]
                angle2Z = math.degrees(rc.Geometry.Vector3d.VectorAngle(normal, rc.Geometry.Vector3d.ZAxis))
            except:
                print self
                print rc.Geometry.AreaMassProperties.Compute(self.geometry).Centroid
                angle2Z = 0
        else:
            #print findNormal
            angle2Z = 0
        
        if  angle2Z < maximumRoofAngle or angle2Z > 360- maximumRoofAngle:
            try:
                if self.isThisTheTopZone:
                    return 1 #roof
                else:
                    return 3 # ceiling
            except:
                return 1 #roof
                
        elif  160 < angle2Z <200:
            return 2 # floor
        
        else:
            return 0 #wall
    
    def getTotalArea(self):
        return self.geometry.GetArea()
    
    def setType(self, type, isUserInput = False):
        self.type = type
        self.srfTypeByUser = isUserInput
    
    def setBC(self, BC, isUserInput = False):
        self.BC = BC
        self.srfBCByUser = isUserInput
    
    def setBCObject(self, BCObject):
        self.BCObject = BCObject
    
    def setBCObjectToOutdoors(self):
        self.BCObject = self.outdoorBCObject()
    
    def setEPConstruction(self, EPConstruction):
        self.EPConstruction = EPConstruction
    
    def setRADMaterial(self, RADMaterial):
        self.RadMaterial = RADMaterial
    
    def setName(self, newName):
        self.name = newName
        
    def setSunExposure(self, exposure = 'NoSun'):
        self.sunExposure = exposure
    
    def setWindExposure(self, exposure = 'NoWind'):
        self.windExposure = exposure
    
    def __str__(self):
        try:
            return 'Surface name: ' + self.name + '\nSurface number: ' + str(self.num) + \
                   '\nThis surface is a ' + str(self.srfType[self.type]) + "."
        except:
            return 'Surface name: ' + self.name + '\n' + 'Surface number: ' + str(self.num) + \
                   '\nSurface type is not assigned. Honeybee thinks this is a ' + str(self.srfType[self.getTypeByNormalAngle()]) + "."
                   

class hb_EPZoneSurface(hb_EPSurface):
    """..."""
    def __init__(self, surface, srfNumber, srfName, *args):
        """This function initiates the class for an EP surface.
            surface: surface geometry as a Brep
            srfNumber: a unique number that is only for this surface
            srfName: the unique name for this surface
            parentZone: class of the zone that this surface belongs to"""
        if len(args)==2:
            parentZone, surafceType = args
            hb_EPSurface.__init__(self, surface, srfNumber, srfName, parentZone, surafceType)
            self.getAngle2North()
            
            self.BCObject = self.outdoorBCObject()

        else:
            hb_EPSurface.__init__(self, surface, srfNumber, srfName)
            
            # Check for possible surface type and assign the BC based on that
            # This will be re-evaluated in write idf file
            srfType = self.getTypeByNormalAngle()
            self.BC = self.srfBC[srfType]
            self.BCObject = self.outdoorBCObject()
            self.sunExposure = self.srfSunExposure[srfType]
            self.windExposure = self.srfWindExposure[srfType]
        
        if hasattr(self, 'parent') and self.parent!=None:
            # in both of this cases the zone should be meshed
            if not self.isPlanar:
                self.parent.hasNonPlanarSrf = True
            if self.hasInternalEdge:
                self.parent.hasInternalEdge = True
        
        if hasattr(self, 'type'):
            self.sunExposure = self.srfSunExposure[self.type]
            self.windExposure = self.srfWindExposure[self.type]
        
        self.groundViewFactor = 'autocalculate'
        self.hasChild = False
        self.isChild = False
        self.childSrfs = []
    
    def isPossibleChild(self, chidSrfCandidate, tolerance = sc.doc.ModelAbsoluteTolerance):
        # check if all the vertices has 0 distance with the base surface
        segments = chidSrfCandidate.DuplicateEdgeCurves(True)
        pts = []
        [pts.append(seg.PointAtStart) for seg in segments]
        
        for pt in pts:
            ptOnSrf = self.geometry.ClosestPoint(pt)
            if pt.DistanceTo(ptOnSrf) > tolerance: return False
        
        # check the area of the child surface and make sure is smaller than base surface
        #if self.geometry.GetArea() <= chidSrfCandidate.GetArea():
        #    print "The area of the child surface cannot be larger than the area of the parent surface!"
        #    return False
        
        # all points are located on the surface and the area is less so it is all good!
        return True
    
    def addChildSrf(self, childSurface, percentage = 40):
        # I should copy/paste the function here so I can run it as
        # a method! For now I just collect them here together....
        # use the window function
        try: self.childSrfs.extend(childSurface)
        except: self.childSrfs.append(childSurface)
        self.hasChild = True
        pass
    
    def calculatePunchedSurface(self):
        
        def checkCrvArea(crv):
            try:
                area = rc.Geometry.AreaMassProperties.Compute(crv).Area
            except:
                area = 0
            
            return area > sc.doc.ModelAbsoluteTolerance
        
        def checkCrvsPts(crv):
            # in some cases crv generates a line with similar points
            pts = []
            pts.append(crv.PointAtStart)
            restOfpts = self.findDiscontinuity(crv, style = 4)
            # for some reason restOfPts returns no pt!
            try: pts.extend(restOfpts)
            except: pass
            
            def isDuplicate(pt, newPts):
                for p in newPts:
                    # print pt.DistanceTo(p)
                    if pt.DistanceTo(p) < 2 * sc.doc.ModelAbsoluteTolerance:
                        return True
                return False
                
            newPts = [pts[0]]
            for pt in pts[1:]:
                if not isDuplicate(pt, newPts):
                    newPts.append(pt)
                    if len(newPts) > 2:
                        return True
            return False
            
        glzCrvs = []
        childSrfs = []
        for glzSrf in self.childSrfs:
            glzEdges = glzSrf.geometry.DuplicateEdgeCurves(True)
            jGlzCrv = rc.Geometry.Curve.JoinCurves(glzEdges)[0]
            # in some cases glazing based on percentage generates very small glazings
            # here I check and remove them
            
            # check area of curve
            try:
                if self.isPlanar:
                    area = rc.Geometry.AreaMassProperties.Compute(jGlzCrv).Area
                else:
                    area = rc.Geometry.AreaMassProperties.Compute(glzSrf).Area
            except:
                #in case area calulation fails 
                area = 0.0
            
            if  area > sc.doc.ModelAbsoluteTolerance and checkCrvsPts(jGlzCrv):
                
                # check normal direction of child surface and base surface
                # print math.degrees(rc.Geometry.Vector3d.VectorAngle(glzSrf.normalVector, self.normalVector))
                
                childSrfs.append(glzSrf)
                glzCrvs.append(jGlzCrv)
            else:
                print "A very tiny glazing is removed from " + self.name+ "."
                
        self.childSrfs = childSrfs
        
        baseEdges = self.geometry.DuplicateEdgeCurves(True)
        
        jBaseCrv = rc.Geometry.Curve.JoinCurves(baseEdges)
        
        # convert array to list
        jBaseCrvList = list(jBaseCrv)
        
        try:
            if self.isPlanar:
                # works for planar surfaces
                punchedGeometries = rc.Geometry.Brep.CreatePlanarBreps(glzCrvs + jBaseCrvList)
                
                if len(punchedGeometries) == 1:
                    self.punchedGeometry = punchedGeometries[0]
                else:
                    # curves are not in the same plane so let's
                    # project the curves on surface plane
                    srfPlane = rc.Geometry.Plane(self.cenPt, self.normalVector)
                    PGlzCrvs = []
                    for curve in glzCrvs + jBaseCrvList:
                        pCrv = rc.Geometry.Curve.ProjectToPlane(curve, srfPlane)
                        if checkCrvArea:
                            PGlzCrvs.append(pCrv)
                    
                    punchedGeometries = rc.Geometry.Brep.CreatePlanarBreps(PGlzCrvs)
                    # in some cases glazing with very minor areas are generated
                    # which causes multiple surfaces
                    self.punchedGeometry = punchedGeometries[-1]
            else:
                # split the base geometry - Good luck!
                splitBrep = self.geometry.Faces[0].Split(glzCrvs, sc.doc.ModelAbsoluteTolerance)
                
                #splitBrep.Faces.ShrinkFaces()
                
                for srfCount in range(splitBrep.Faces.Count):
                    surface = splitBrep.Faces.ExtractFace(srfCount)
                    edges = surface.DuplicateEdgeCurves(True)
                    joinedEdges = rc.Geometry.Curve.JoinCurves(edges)
                    
                    if len(joinedEdges)>1:
                        self.punchedGeometry = surface
                                        
        except Exception, e:
            self.punchedGeometry = None
            self.hasChild = False
            self.childSrfs = []
            print "Failed to calculate opaque part of the surface. " + \
                  "Glazing is removed from " + self.name

    def getOpaqueArea(self):
        if self.hasChild:
            try:
                return self.punchedGeometry.GetArea()
            except:
                self.calculatePunchedSurface()
                return self.punchedGeometry.GetArea()
        else:
            return self.getTotalArea()
    
    def getGlazingArea(self):
        if self.hasChild:
            glzArea = 0
            for childSrf in self.childSrfs:
                glzArea += childSrf.getTotalArea()
            return glzArea
        else:
            return 0
    
    def getWWR(self):
        return self.getGlazingArea()/self.getTotalArea()
        
    def removeAllChildSrfs(self):
        self.childSrfs = []
        self.hasChild = False
        self.calculatePunchedSurface()

class hb_EPShdSurface(hb_EPSurface):
    def __init__(self, surface, srfNumber, srfName):
        hb_EPSurface.__init__(self, surface, srfNumber, srfName, self)
        self.TransmittanceSCH = ''
        self.isChild = False
        self.hasChild = False
        self.construction = 'Exterior Wall' # just added here to get the minimum surface to work
        self.EPConstruction = 'Exterior Wall' # just added here to get the minimum surface to work
        self.childSrfs = [self] # so I can use the same function as glazing to extract the points
        self.type = 6
        pass
    
    def getSrfCenPtandNormal(self, surface):
        # I'm not sure if we need this method
        # I will remove this later
        surface = surface.Faces[0]
        u_domain = surface.Domain(0)
        v_domain = surface.Domain(1)
        centerU = (u_domain.Min + u_domain.Max)/2
        centerV = (v_domain.Min + v_domain.Max)/2
        
        centerPt = surface.PointAt(centerU, centerV)
        normalVector = surface.NormalAt(centerU, centerV)
        
        normalVector.Unitize()
        return centerPt, normalVector


class hb_EPFenSurface(hb_EPSurface):
    """..."""
    def __init__(self, surface, srfNumber, srfName, parentSurface, surafceType, punchedWall = None):
        """This function initiates the class for an EP surface.
            surface: surface geometry as a Brep
            srfNumber: a unique number that is only for this surface
            srfName: the unique name for this surface
            parentZone: class of the zone that this surface belongs to"""
        hb_EPSurface.__init__(self, surface, srfNumber, srfName, parentSurface, surafceType)
        
        if not self.isPlanar:
            try:
                self.parent.parent.hasNonplanarSrf = True
            except:
                # surface is not part of a zone yet.
                pass

        # calculate punchedWall
        self.parent.punchedGeometry = punchedWall
        self.shadingControlName = ''
        self.frameName = ''
        self.Multiplier = 1
        self.BCObject = self.outdoorBCObject()
        self.groundViewFactor = 'autocalculate'
        self.isChild = True # is it really useful?
        
        
class hb_Hive(object):
    
    class CopyClass(object):
        pass
    
    def addToHoneybeeHive(self, HBObjects, GHComponentID):
        # check if the honeybeedictionary already existed
        # if not create the dictionary
        # eventually this should be generated as soon as they user let the bee fly
        if not sc.sticky.has_key('HBHive'): sc.sticky['HBHive'] = {}
        geometries = []
        childGeometries = []
        for HBObject in HBObjects:
            key = GHComponentID + HBObject.name
            
            sc.sticky['HBHive'][key] = HBObject
            
            # assuming that all the HBOBjects has a geometry! I assume they do
            
            try:
                if HBObject.objectType != "HBZone" and HBObject.hasChild:
                    if HBObject.punchedGeometry == None:
                        HBObject.calculatePunchedSurface()
                    geo = HBObject.punchedGeometry.Duplicate()
                    geometry = geo.Duplicate()
                    for childObject in HBObject.childSrfs:
                        # for now I only return the childs as geometries and not objects
                        # it could cause some confusion for the users that I will try to
                        # address later
                        childGeometries.append(childObject.geometry.Duplicate())
                    # join geometries into a single surface
                    geometry = rc.Geometry.Brep.JoinBreps([geometry] + childGeometries, sc.doc.ModelAbsoluteTolerance)[0]
                
                elif HBObject.objectType == "HBZone":
                    geo = HBObject.geometry
                    geometry = geo.Duplicate()
                    srfs = []
                    zoneHasChildSrf = False
                    for HBSrf in HBObject.surfaces:
                        if HBSrf.hasChild:
                            zoneHasChildSrf = True
                            srfs.append(HBSrf.punchedGeometry.Duplicate())
                            for childObject in HBSrf.childSrfs:
                                # for now I only return the childs as geometries and not objects
                                # it could cause some confusion for the users that I will try to
                                # address later
                                srfs.append(childObject.geometry.Duplicate())
                        else:
                            srfs.append(HBSrf.geometry.Duplicate())
                            
                    if zoneHasChildSrf:
                        geometry = rc.Geometry.Brep.JoinBreps(srfs, sc.doc.ModelAbsoluteTolerance)[0]
                        
                else:
                    geo = HBObject.geometry
                    geometry = geo.Duplicate()
                geometry.UserDictionary.Set('HBID', key)
                geometries.append(geometry)
            except Exception, e:
                print "Reached the maximum array size for UserDictionary: " + `e`
                    
        # return geometry with the ID
        return geometries
        
    def callFromHoneybeeHive(self, geometryList):
        HBObjects = []
        for geometry in geometryList:
            try:
                key = geometry.UserDictionary['HBID']
                if sc.sticky['HBHive'].has_key(key):
                    try:
                        HBObject = sc.sticky['HBHive'][key]
                        # after the first round meshedFace makes copy.deepcopy crash
                        # so I need to regenerate meshFaces
                        if HBObject.objectType == "HBZone":
                            for surface in HBObject.surfaces:
                                newMesh = rc.Geometry.Mesh()
                                newMesh.Append(surface.meshedFace)
                                surface.meshedFace = newMesh
                        elif HBObject.objectType == "HBSurface": 
                            newMesh = rc.Geometry.Mesh()
                            newMesh.Append(HBObject.meshedFace)
                            HBObject.meshedFace = newMesh
                        
                        HBObjects.append(copy.deepcopy(HBObject))
                        
                    except Exception, e:
                        print `e`
                        print "Failed to copy the object. Returning the original objects...\n" +\
                              "This can cause strange behaviour!"
                        HBObjects.append(sc.sticky['HBHive'][key])
            except:
                pass
                
        return HBObjects


class hb_RADParameters(object):
    def __init__(self):
        self.radParDict = {
        "_ab_": [2, 3, 6],
        "_ad_": [512, 2048, 4096],
        "_as_": [128, 2048, 4096],
        "_ar_": [16, 64, 128],
        "_aa_": [.25, .2, .1],
        "_ps_": [8, 4, 2],
        "_pt_": [.15, .10, .05],
        "_pj_": [.6, .9, .9],
        "_dj_": [0, .5, .7],
        "_ds_": [.5, .25, .05],
        "_dt_": [.5, .25, .15],
        "_dc_": [.25, .5, .75],
        "_dr_": [0, 1, 3],
        "_dp_": [64, 256, 512],
        "_st_": [.85, .5, .15],
        "_lr_": [4, 6, 8],
        "_lw_": [.05, .01, .005],
        "_av_": [0, 0, 0],
        "xScale": [1, 2, 6],
        "yScale": [1, 2, 6]
        }


class hb_DSParameters(object):
    
    def __init__(self, outputUnits = [2], dynamicSHDGroup_1 = None,  dynamicSHDGroup_2 = None, RhinoViewsName = [] , adaptiveZone = False, dgp_imageSize = 250):
        
        if len(outputUnits)!=0 and outputUnits[0]!=None: self.outputUnits = outputUnits
        else: self.outputUnits = [2]
        
        if adaptiveZone == None: adaptiveZone = False
        self.adaptiveZone = adaptiveZone
        
        if not dgp_imageSize: dgp_imageSize = 250
        self.dgp_imageSize = dgp_imageSize
        
        if dynamicSHDGroup_1 == None and dynamicSHDGroup_2==None:
            
            class dynamicSHDRecipe(object):
                def __init__(self, type = 1, name = "no_blind"):
                    self.type = type
                    self.name = name
            
            self.DShdR = [dynamicSHDRecipe(type = 1, name = "no_blind")]
            
        else:
            self.DShdR = []
            if dynamicSHDGroup_1 != None: self.DShdR.append(dynamicSHDGroup_1)
            if dynamicSHDGroup_2 != None: self.DShdR.append(dynamicSHDGroup_2)
        
        # Number of ill files
        self.numOfIll = 1
        for shadingRecipe in self.DShdR:
            if shadingRecipe.name == "no_blind":
                pass
            elif shadingRecipe.name == "conceptual_dynamic_shading":
                self.numOfIll += 1
            else:
                # advanced dynamic shading
                self.numOfIll += len(shadingRecipe.shadingStates) - 1
        
        # print "number of ill files = " + str(self.numOfIll)

letItFly = True

def checkGHPythonVersion(target = "0.6.0.3"):
    currentVersion = int(ghenv.Version.ToString().replace(".", ""))
    targetVersion = int(target.replace(".", ""))
    
    if targetVersion > currentVersion: return False
    else: return True

try:
    downloadTemplate = checkIn.checkForUpdates(LB= False, HB= True, OpenStudio = True, template = True)
except:
    # no internet connection
    downloadTemplate = False

GHPythonTargetVersion = "0.6.0.3"

if not checkGHPythonVersion(GHPythonTargetVersion):
    msg =  "Honeybee failed to fly! :(\n" + \
           "You are using an old version of GHPython. " +\
           "Please update to version: " + GHPythonTargetVersion
    print msg
    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
    letItFly = False
    sc.sticky["honeybee_release"] = False

if letItFly:
    if not sc.sticky.has_key("honeybee_release") or True:
        w = gh.GH_RuntimeMessageLevel.Warning
        sc.sticky["honeybee_release"] = True
        folders = hb_findFolders()
        
        sc.sticky["honeybee_folders"] = {}
        
        if folders.RADPath == None:
            if os.path.isdir("c:\\radiance\\bin\\"):
                folders.RADPath = "c:\\radiance\\bin\\"
            else:
                msg= "Honeybee cannot find RADIANCE folder on your system.\n" + \
                     "Make sure you have RADIANCE installed on your system.\n" + \
                     "You won't be able to run daylighting studies without RADIANCE.\n" + \
                     "A good place to install RADIANCE is c:\\radiance"
                ghenv.Component.AddRuntimeMessage(w, msg)
                folders.RADPath = ""
        
        if  folders.RADPath.find(" ") > -1:
            msg =  "There is a white space in RADIANCE filepath: " + folders.RADPath + "\n" + \
                   "Please install RADIANCE in a valid address (e.g. c:\\radiance)"
            ghenv.Component.AddRuntimeMessage(w, msg)
            
        # I should replace this with python methods in os library
        # looks stupid!
        if folders.RADPath.endswith("\\"): segmentNumber = -2
        else: segmentNumber = -1
        hb_RADLibPath = "\\".join(folders.RADPath.split("\\")[:segmentNumber]) + "\\lib"
        
        sc.sticky["honeybee_folders"]["RADPath"] = folders.RADPath
        sc.sticky["honeybee_folders"]["RADLibPath"] = hb_RADLibPath
            
        if folders.DSPath == None:
            if os.path.isdir("c:\\daysim\\bin\\"):
                folders.DSPath = "c:\\daysim\\bin\\"
            else:
                msg= "Honeybee cannot find DAYSIM folder on your system.\n" + \
                     "Make sure you have DAYISM installed on your system.\n" + \
                     "You won't be able to run annual climate-based daylighting studies without DAYSIM.\n" + \
                     "A good place to install DAYSIM is c:\\DAYSIM"
                ghenv.Component.AddRuntimeMessage(w, msg)
                folders.DSPath = ""
        
        if folders.DSPath.find(" ") > -1:
            msg =  "There is a white space in DAYSIM filepath: " + folders.DSPath + "\n" + \
                   "Please install Daysism in a valid address (e.g. c:\\daysim)"
            ghenv.Component.AddRuntimeMessage(w, msg)
        
        if folders.DSPath.endswith("\\"): segmentNumber = -2
        else: segmentNumber = -1
        hb_DSCore = "\\".join(folders.DSPath.split("\\")[:segmentNumber])
        hb_DSLibPath = "\\".join(folders.DSPath.split("\\")[:segmentNumber]) + "\\lib"
        
        sc.sticky["honeybee_folders"]["DSPath"] = folders.DSPath
        sc.sticky["honeybee_folders"]["DSCorePath"] = hb_DSCore
        sc.sticky["honeybee_folders"]["DSLibPath"] = hb_DSLibPath
    
        if folders.EPPath == None:
            EPVersion = "V8-1-0"
            if os.path.isdir("C:\EnergyPlus" + EPVersion + "\\"):
                folders.EPPath = "C:\EnergyPlus" + EPVersion + "\\"
            else:
                msg= "Honeybee cannot find EnergyPlus" + EPVersion + " folder on your system.\n" + \
                     "Make sure you have EnergyPlus" + EPVersion + " installed on your system.\n" + \
                     "You won't be able to run energy simulations without EnergyPlus.\n" + \
                     "A good place to install EnergyPlus is c:\\EnergyPlus" + EPVersion
                # I remove the warning for now until EP plugins are available
                # It confuses the users
                ghenv.Component.AddRuntimeMessage(w, msg)
                folders.EPPath = "C:\EnergyPlus" + EPVersion + "\\"
        
        sc.sticky["honeybee_folders"]["EPPath"] = folders.EPPath
        
        sc.sticky["honeybee_RADMaterialAUX"] = RADMaterialAux
        
        # set up radiance materials
        sc.sticky["honeybee_RADMaterialAUX"](True)
        
        try:
            hb_GetEPConstructions(downloadTemplate)
            
            sc.sticky["honeybee_EPMaterialAUX"] = EPMaterialAux
            sc.sticky["honeybee_EPScheduleAUX"] = EPScheduleAux
            sc.sticky["honeybee_EPObjectsAUX"] = EPObjectsAux
            
        except Exception, e:
            print e
            print "Failed to load EP constructions!"
        
        sc.sticky["honeybee_Hive"] = hb_Hive
        sc.sticky["honeybee_DefaultMaterialLib"] = materialLibrary
        sc.sticky["honeybee_DefaultScheduleLib"] = scheduleLibrary
        sc.sticky["honeybee_DefaultSurfaceLib"] = EPSurfaceLib
        sc.sticky["honeybee_BuildingProgramsLib"] = BuildingProgramsLib
        sc.sticky["honeybee_EPTypes"] = EPTypes()
        sc.sticky["honeybee_EPZone"] = EPZone
        sc.sticky["honeybee_reEvaluateHBZones"] = hb_reEvaluateHBZones
        sc.sticky["honeybee_EPSurface"] = hb_EPSurface
        sc.sticky["honeybee_EPShdSurface"] = hb_EPShdSurface
        sc.sticky["honeybee_EPZoneSurface"] = hb_EPZoneSurface
        sc.sticky["honeybee_EPFenSurface"] = hb_EPFenSurface
        sc.sticky["honeybee_RADParameters"] = hb_RADParameters
        sc.sticky["honeybee_DSParameters"] = hb_DSParameters
        sc.sticky["honeybee_EPParameters"] = hb_EnergySimulatioParameters
        
        # done! sharing the happiness.
        print "Hooohooho...Flying!!\nVviiiiiiizzz..."
