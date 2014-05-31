# By Mostapha Sadeghipour Roudsari
# Sadeghipour@gmail.com
# Honeybee started by Mostapha Sadeghipour Roudsari is licensed
# under a Creative Commons Attribution-ShareAlike 3.0 Unported License.

"""
EnergyPlus Construction

-
Provided by Honeybee 0.0.53
    
    Args:
        _name: ...
        _layer_1
    Returns:
        EPConstruction: ...

"""

ghenv.Component.Name = "Honeybee_EnergyPlus Construction"
ghenv.Component.NickName = 'EPConstruction'
ghenv.Component.Message = 'VER 0.0.53\nMAY_13_2014'
ghenv.Component.Category = "Honeybee"
ghenv.Component.SubCategory = "06 | Energy | Material | Construction"
try: ghenv.Component.AdditionalHelpFromDocStrings = "1"
except: pass

# set the right names
numInputs = ghenv.Component.Params.Input.Count
for input in range(numInputs):
    if input == 0: inputName = '_name'
    else: inputName = '_layer_' + str(input)
    
    ghenv.Component.Params.Input[input].NickName = inputName
    ghenv.Component.Params.Input[input].Name = inputName
ghenv.Component.Attributes.Owner.OnPingDocument()


# read the layers
import scriptcontext as sc
import Grasshopper.Kernel as gh
import os

def main():
    
    # import the classes
    w = gh.GH_RuntimeMessageLevel.Warning
    
    if not sc.sticky.has_key('ladybug_release')and sc.sticky.has_key('honeybee_release'):
        print "You should first let both Ladybug and Honeybee to fly..."
        ghenv.Component.AddRuntimeMessage(w, "You should first let both Ladybug and Honeybee to fly...")
        return -1
    
    hb_EPMaterialAUX = sc.sticky["honeybee_EPMaterialAUX"]()
    
    # check if all the layers are there
    # check if the material is already created in the library
    # if not then stop the process
    materialNames = []
    
    constructionStr = "Construction,\n" + _name + ",    !- Name\n"
    
    for inputCount in range(ghenv.Component.Params.Input.Count):
        if inputCount!=0 and inputCount < ghenv.Component.Params.Input.Count:
            layerName = ghenv.Component.Params.Input[inputCount].NickName
            exec('materialName = ' + layerName) #that's why I love Python. Yo!
            # check if it is a full string definition
            if materialName != None:
                added, materialName = hb_EPMaterialAUX.addEPConstructionToLib(materialName, overwrite = True)
            
                # double check and make sure material already exists
                if materialName in sc.sticky ["honeybee_materialLib"].keys():
                    pass
                elif materialName in sc.sticky ["honeybee_windowMaterialLib"].keys():
                    pass
                else:
                    msg = "layer_" + str(inputCount) + " is not a valid material name/definition.\n" + \
                        "Create the material first and try again."
                    ghenv.Component.AddRuntimeMessage(w, msg)
                    return
                
                if inputCount!= ghenv.Component.Params.Input.Count - 1:
                    constructionStr += materialName + ",    !- Layer " + str(inputCount) + "\n"
                else:
                    constructionStr += materialName + ";    !- Layer " + str(inputCount) + "\n"
                    
    return constructionStr

#if addToLibrary:
#    customLibPath = "C:/Ladybug/userCustomLibrary.idf"
#    if not os.path.isfile(customLibPath): modifier = 'w'
#    else: modifier = 'a'
#    with open(customLibPath, modifier) as libFile:
#        constructionStr = EPConstructionStr(name)
#        # Later I should add a check and avoid duplicates
#        libFile.write(constructionStr)

if _name and _layer_1:
    EPConstruction = main()