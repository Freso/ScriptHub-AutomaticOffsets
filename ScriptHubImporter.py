import json
import os.path
import sys
import re

# global for storing dictionary of output strings (which reduces redundancy in code execution)
outputStringsDict = {}
exportedJson = ""
baseClassTypeList = []
baseClassTypeList.append("CrusadersGame.Defs.CrusadersGameDataSet")
baseClassTypeList.append("UnityGameEngine.Dialogs.DialogManager")
baseClassTypeList.append("UnityGameEngine.Core.EngineSettings")
baseClassTypeList.append("IdleGameManager")
baseClassTypeList.append("CrusadersGame.GameSettings")
# baseClassTypeList.append("CrusadersGame.Effects.ActiveEffectKeyHandler")
effectClassTypeList = []
effectClassTypeList.append("CrusadersGame.Effects.OminContractualObligationsHandler")
effectClassTypeList.append("TimeScaleWhenNotAttackedHandler")
effectClassTypeList.append("CrusadersGame.Effects.HavilarImpHandler")
effectClassTypeList.append("CrusadersGame.Effects.BrivUnnaturalHasteHandler")
effectClassTypeList.append("CrusadersGame.Effects.NerdWagonHandler")
effectClassTypeList.append("CrusadersGame.Effects.HewMaanTeamworkHandler")
effectClassTypeList.append("CrusadersGame.Effects.SpurtWaspirationHandlerV2")
currentEffectClass = ""


# Main
def main():
    global exportedJson
    os.chdir(os.path.realpath(__file__) + "\\..")
    memoryStructureLoc =  ".\\ScriptHubExport32.json"
    StartImport(memoryStructureLoc, False)
    if os.path.exists(memoryStructureLoc) and "value" in exportedJson["CrusadersGame.GameSettings"]["fields"]["MobileClientVersion"]:
        CreateVersionFile(32)
    memoryStructureLoc = ".\\ScriptHubExport64.json"
    StartImport(memoryStructureLoc, True)
    if os.path.exists(memoryStructureLoc) and "value" in exportedJson["CrusadersGame.GameSettings"]["fields"]["MobileClientVersion"]:
        CreateVersionFile(64)
    os.system("pause")

# Read json file exported from CE ScriptHubExporter addon and import from files based on types
def StartImport(memFileLoc, is64Bit):
    global exportedJson
    global baseClassTypeList
    global currentEffectClass
    if not os.path.exists(".\\Imports\\ActiveEffectHandlers\\"):
        os.makedirs(".\\Imports\\ActiveEffectHandlers\\")
    if os.path.exists(memFileLoc):
        jsonFile = open(memFileLoc, 'r')
        exportedJson = json.load(jsonFile)
        jsonFile.close()
        # get classes object    
        exportedJson = exportedJson['classes']
        # set the base class starting point (object the base pointer points to)
        # filename is based on the last chunk
        # e.g. CrusadersGame.Defs.CrusadersGameDataSet will check MemoryLocations_CrusadersGameDataSet.txt for offset lookup items.
        for baseClassType in baseClassTypeList:
            Import(baseClassType, is64Bit)
        for effectClassType in effectClassTypeList:
            currentEffectClass = effectClassType.rsplit('.',1)[-1:][0]
            Import(effectClassType, is64Bit, True)
        OutputHandlerIncludeFile(effectClassType, is64Bit)
    else:
        print("Could not open " + memFileLoc + ". It does not exist.")

# Reads MemoryLocations file for target variables and builds them into ScriptHub import code (AHK).
def Import(baseClass, is64Bit = False, isEffectHandler = False):
    global exportedJson
    # Make sure output is clear before doing an import
    global outputStringsDict
    outputStringsDict = {}
    # read input file with list of offsets to find
    memoryFile = ""
    baseClassParts = baseClass.split('.')
    fileNameBase = baseClassParts[len(baseClassParts) - 1]
    memoryFileLocation = ".\\MemoryLocations_" + fileNameBase + ".txt"
    if os.path.exists(memoryFileLocation):
        memoryFile = open(memoryFileLocation, 'r')
    else:
        print("Could not open " + memoryFileLocation + ". It does not exist.")
        return
    # read lines from text file without newline breaks
    memoryFileLines = memoryFile.read().splitlines() 
    memoryFile.close()
    # remove empty strings
    memoryFileLines = [i for i in memoryFileLines if i != '']
    # remove commented lines
    memoryFileLines = [i for i in memoryFileLines if i[0] != '#']

    # iterate lines and build ahk file to outputStringsDict
    for line in memoryFileLines:
        offsetsLocationStringSplit = line.split(".")
        BuildMemoryString(baseClass, offsetsLocationStringSplit, 0, isEffectHandler ) 
    version = "64" if is64Bit else "32"
    OutputImportToFile(fileNameBase, version, isEffectHandler)
    outputStringsDict = {}
    print(baseClass + " " + version + "bit output complete.")

# Writes outputStringsDict to the appropriate file.
def OutputImportToFile(fileNameBase, version, isEffectHandler):
    # Output to AHK file
    memoryFileString = "; This file was automatically generated by ScriptHubImporter.py\n"
    for k,v in outputStringsDict.items():
        memoryFileString = memoryFileString + v
    extraFolder = "\\ActiveEffectHandlers" if isEffectHandler else ""
    outputFile = open(".\\Imports" + extraFolder + "\\IC_" + fileNameBase + version + "_Import.ahk", 'w')
    outputFile.write(memoryFileString)
    outputFile.close()

# Writes a single include file that includes all other hero handlers.
def OutputHandlerIncludeFile(effectClassType, is64Bit ):
    if effectClassType:
        version = "64" if is64Bit else "32"
        handlerImportsString = "; This file was automatically generated by ScriptHubImporter.py\n"
        for effectClassType in effectClassTypeList:
            baseClassParts = effectClassType.split('.')
            fileNameBase = baseClassParts[len(baseClassParts) - 1]
            handlerImportsString = handlerImportsString + "#include %A_LineFile%\\..\\" + "IC_" + fileNameBase + version + "_Import.ahk\n"
        handlerImportsFile = open(".\\Imports\\ActiveEffectHandlers\\IC_HeroHandlerIncludes" + version + "_Import.ahk", 'w')
        handlerImportsFile.write(handlerImportsString)
        handlerImportsFile.close()

# recursive function that will search for the current indexValue of variablesStringArray and call itself for the rest of the variables in variablesStringArray
# appending strings for final output as it goes
def BuildMemoryString(classType, variablesStringArray, indexValue, isEffectHandler, checkParent = True):
    global exportedJson
    isFound = False
    if indexValue >= len(variablesStringArray):
        return isFound
    if classType == "System.Object":
        return isFound
    if classType == "CrusadersGame.Effects.IEffectSource":
        return isFound
    classTypeOriginal = classType
    #fix for timescale using GameManager (IdleGameManager extends GameManager) instead of its starting top level of IdleGameManager
    if classType == "GameManager":
        classTypeOriginal = "IdleGameManager"
    # could not find the class, test for variation with + (e.g. 'CrusadersGame.User.UserModronHandler.ModronCoreData' -> 'CrusadersGame.User.UserModronHandler+ModronCoreData') 
    if classType not in exportedJson:
        #fix for subclasses
        subClassCheckString = '+'.join(classType.rsplit('.',1))
        #fix for ActiveEffectKeyHandler classes that use the new typed BaseActiveEffectKeyHandler
        typedClassCheckString = classType.rsplit('[',1)[0] + "[T]"
        if subClassCheckString in exportedJson:
            classType = subClassCheckString
        elif typedClassCheckString in exportedJson:
            classType = typedClassCheckString
        else:
            # class still not found, lookup failed. Pass.
            NotificationForMissingClass(classType, variablesStringArray, indexValue)
            return isFound        

    # could not find the variable in the class (Check parent classes?)
    if variablesStringArray[indexValue] not in exportedJson[classType]['fields']:
        # Check special cases of collections that include derived objects
        isFound = SpecialSubClassCaseCheck(classType, variablesStringArray, indexValue, isEffectHandler)
        # otherwise, check the parent class
        if checkParent:
            if isFound or BuildMemoryString(exportedJson[classType]['Parent'], variablesStringArray, indexValue, isEffectHandler):
                return
            else:
                NotificationForMissingFields(classType, variablesStringArray, indexValue)
        return isFound

    # passed existence checks, set variables
    isFound = True
    offset = hex(int(exportedJson[classType]['fields'][variablesStringArray[indexValue]]['offset']))
    static = exportedJson[classType]['fields'][variablesStringArray[indexValue]]['static']
    classType = exportedJson[classType]['fields'][variablesStringArray[indexValue]]['type']
    
    # TODO: Handle Dictionary<List<Action<>>> types (TransitionOverride)
    # TODO: Use correct offsets for collections of collections

    currClassType = classType
    preMatch = None
    specialType = None
    # Collection test:
    match = re.search("[^<]*<", currClassType)
    if match is not None:
        preMatch = match.group(0)[:-1]
        # find inner collection type if exists
        currClassType = FindCollectionValueType(currClassType)
        currClassType = FindCollectionValueType(currClassType) 
        # add a special collection type to value string if the field has multiple collections
        if currClassType is not None:
            test = FindCollectionValueType(classType)
            match = re.search("[^<]*<", test)
            if match is not None:
                test = match.group(0)[:-1]
            specialType = GetMemoryTypeFromClassType(test)
            # output current (Increment indexValue in call)
            AppendToOutput(variablesStringArray, indexValue + 1, classTypeOriginal, static, offset, GetMemoryTypeFromClassType(preMatch), isEffectHandler, )
            indexValue += 1 
            variablesStringArray.insert(indexValue, test.rsplit('.',1)[-1:][0])
            # output subcollection
            AppendToOutput(variablesStringArray, indexValue + 1, classTypeOriginal, static, "", specialType, isEffectHandler)
            # build from current + subcollection
            BuildMemoryString(currClassType, variablesStringArray, indexValue + 1, isEffectHandler) 
            return isFound

    if preMatch is not None:
        if currClassType is None:
            currClassType = FindCollectionValueType(classType)
        varType = GetMemoryTypeFromClassType(preMatch)
    else:
        varType = GetMemoryTypeFromClassType(currClassType)

    # Fix field name if it includes invalid characters for AHK
    variablesStringArray[indexValue] = SpecialInvalidCharacterInFieldCheck(variablesStringArray, indexValue)

    # True location of int value from ProtectedInt
    if currClassType == "UnityGameEngine.Utilities.ProtectedInt":
        offset = hex(int(offset, 16) + int('0x8', 16))

    indexValue += 1
    AppendToOutput(variablesStringArray, indexValue, classTypeOriginal, static, offset, varType, isEffectHandler)
    BuildMemoryString(currClassType, variablesStringArray, indexValue, isEffectHandler) 
    return isFound

# For cases where there is a collection of a base class that can contain objects that may be sub classes of the base class.
# If the object is not found in the base class, check the derived class, but not its parents.
def SpecialSubClassCaseCheck(classType, variablesStringArray, indexValue, isEffectHandler):
    isFound = False
    if classType == "UnityGameEngine.Dialogs.Dialog":
        isFound = BuildMemoryString( "CrusadersGame.Dialogs.BlessingsStore.BlessingsStoreDialog", variablesStringArray, indexValue, isEffectHandler, False) or BuildMemoryString(exportedJson[classType]['Parent'], variablesStringArray, indexValue, isEffectHandler)
    return isFound

# For cases where a field name uses reserved characters in AHK code
def SpecialInvalidCharacterInFieldCheck(variablesStringArray, indexValue):
    # AHK Can't handle <> in names, such as k__BackingField
    if variablesStringArray[indexValue].find("k__BackingField") >= 0:
        match = re.search("<.*>", variablesStringArray[indexValue])
        # fix for activeeffectkeyhandlers using k_backingfields
        if variablesStringArray[indexValue] == "<effectKey>k__BackingField":
            return match.group(0)[1:-1]
        return match.group(0)[1:-1] + "_k__BackingField"
    else:
        return variablesStringArray[indexValue]

# Get the type from inside the collection params (inside <>)
def FindCollectionValueType(classType):
    if classType is None:
        return None
    match = re.search("<.*>", classType)
    if match is not None:
        currClassType = match.group(0)
        currClassType = currClassType[1:-1] # trim <> from match edges 
        return currClassType.rsplit(",",1)[-1:][0]      
    else:
        return None

# When a class is not found, print a messsage displaying the offending class type and variable.
def NotificationForMissingClass(classType, variablesStringArray, indexValue):
    appended = ""
    if indexValue+1 < (len(variablesStringArray)):
        appended = "." + '.'.join(variablesStringArray[indexValue+1:])
    variableInQuestion = '.'.join(variablesStringArray[:indexValue]) + ".[" + variablesStringArray[indexValue] + "]" + appended
    print("Class \"" + classType + "\" not found when looking up " + variableInQuestion + ". Continuing...")

# When a field is not found, print a messsage displaying suggested alternative (if available), as well as the offending offset.
def NotificationForMissingFields(classType, variablesStringArray, indexValue):
    # When the class is still not found, test for case mis-match and print alert if found
    for fieldName in exportedJson[classType]['fields']:
        if variablesStringArray[indexValue].lower() == fieldName.lower():
            print("Did you mean \'" + fieldName + "'?")
            break
    # show diagnostic info for failure to find variable
    print("Variable " + variablesStringArray[indexValue] + " not found in class " + classType + ". Checking Parent (" + exportedJson[classType]['Parent'] + ")...")
    appended = ""
    if indexValue+1 < (len(variablesStringArray)):
        appended = "." + '.'.join(variablesStringArray[indexValue+1:])
    print('.'.join(variablesStringArray[:indexValue]) + ".[" + variablesStringArray[indexValue] + "]" + appended)

# Given a class type, return the memory read type to be used.
def GetMemoryTypeFromClassType(classType):
    # read class type and pick appropriate type for memory reading
    # Standard cases:
    varType = None
    if classType == "System.Int32":
        varType = "Int"
    elif classType == "System.Boolean":
        varType = "Char"
    elif classType == "System.String":
        varType = "UTF-16"
    elif classType == "System.Double":
        varType = "Double"
    elif classType == "System.Single":
        varType = "Float"

            # _classMemory - aTypeSize := {    
            #         "UChar":    1, 
            #         "UShort":   2,
            #         "Short":    2
            #         "UInt":     4
            #         "UFloat":   4,
            #         "Int64":    8,
            #         "Double":   8}  
    # Special Cases:        
    elif classType == "Engine.Numeric.Quad":
        varType = "Quad"                        # actually 2 sequential Int64
    elif classType == "UnityGameEngine.Utilities.ProtectedInt":
        varType = "Int"
    elif classType == "System.Collections.Generic.List":
        varType = "List"
    elif classType == "System.Collections.Generic.Dictionary":
        varType = "Dict"
    elif classType == "System.Collections.Generic.HashSet":
        varType = "HashSet"
    else:
        varType = "Int"
    return varType

# Adds an item to the output strings dictionary if it does not already exist
def AppendToOutput(variablesStringArray, indexValue, classTypeOriginal, static, offset, varType, isEffectHandler):
    global currentEffectClass
    # add new value to dictionary if it is not already there, then build next value

    fullNameOfCurrentVariable = '.'.join(variablesStringArray[:indexValue])
    if isEffectHandler:
        fullNameOfCurrentVariable =  currentEffectClass + "." + fullNameOfCurrentVariable
    if fullNameOfCurrentVariable not in outputStringsDict:
        parentValue = '.'.join(variablesStringArray[:indexValue-1]) if indexValue > 1 else classTypeOriginal 
        if isEffectHandler:
            if indexValue > 1:
                parentValue = '.'.join(variablesStringArray[:indexValue-1])
                parentValue = currentEffectClass + "." + parentValue
            else:
                parentValue = currentEffectClass
        if static == "false":
            outputStringsDict[fullNameOfCurrentVariable] = "this." + fullNameOfCurrentVariable + " := New GameObjectStructure(this." + parentValue + ",\"" + varType + "\", [" + str(offset) + "])\n"
        else:
            outputStringsDict[fullNameOfCurrentVariable] = "this." + fullNameOfCurrentVariable + " := New GameObjectStructure(this." + parentValue + ",\"" + varType + "\", [this.StaticOffset + " + str(offset) + "])\n"

# Creates a game version file.
def CreateVersionFile(architecture):
    # Output to AHK file
    version = exportedJson["CrusadersGame.GameSettings"]["fields"]["MobileClientVersion"]["value"]
    versionPostFix = ''
    if "value" in exportedJson["CrusadersGame.GameSettings"]["fields"]["VersionPostFix"]:
        versionPostFix = exportedJson["CrusadersGame.GameSettings"]["fields"]["VersionPostFix"]["value"] if exportedJson["CrusadersGame.GameSettings"]["fields"]["VersionPostFix"]["value"] != "" else "\"\""
    versionFileString = "; This file was automatically generated by ScriptHubImporter.py\n"
    versionFileString = versionFileString + "global g_ImportsGameVersion" + str(architecture) + " := " + str(version) + "\n"
    versionFileString = versionFileString + "global g_ImportsGameVersionPostFix" + str(architecture) + " := " + str(versionPostFix)
    outputFile = open(".\\Imports" + "\\IC_GameVersion" + str(architecture) + "_Import.ahk", 'w')
    outputFile.write(versionFileString)
    outputFile.close()

if __name__ == "__main__":
    main()