import bpy, math, os
from .lay import Lay
from .util import *

def main(layFilePath, addonName):
    layFile = open(layFilePath, "rb")
    print("Parsing Lay file...", layFilePath)
    lay = Lay(layFile)
    layFile.close()

    # Create LAY Collection
    layCollection = bpy.data.collections.get("LAY")
    if not layCollection:
        layCollection = bpy.data.collections.new("LAY")
        bpy.context.scene.collection.children.link(layCollection)

    # Create layAssets Sub-Collection
    layAssetsCollection = bpy.data.collections.get("lay_layAssets")
    if not layAssetsCollection:
        layAssetsCollection = bpy.data.collections.new("lay_layAssets")
        layCollection.children.link(layAssetsCollection)

    # Create layInstances Sub-Collection
    layInstancesCollection = bpy.data.collections.get("lay_layInstances")
    if not layInstancesCollection:
        layInstancesCollection = bpy.data.collections.new("lay_layInstances")
        layCollection.children.link(layInstancesCollection)

    # Create layAssets and layInstances
    assetRootNode = bpy.data.objects.new("Root_layAsset", None)
    assetRootNode.hide_viewport = True
    layAssetsCollection.objects.link(assetRootNode)
    assetRootNode.rotation_euler = (math.radians(90),0,0)

    instanceRootNode = bpy.data.objects.new("Root_layInstance", None)
    instanceRootNode.hide_viewport = True
    layInstancesCollection.objects.link(instanceRootNode)
    instanceRootNode.rotation_euler = (math.radians(90),0,0)
    
    for asset in lay.assets:
        assetName = asset.name
        print("Placing asset", assetName)
        boundingBox = getModelBoundingBox(assetName.split("_")[0], addonName)
        assetObj = createLayObject(assetName, layAssetsCollection, assetRootNode, asset.position, asset.rotation, asset.scale, boundingBox)
        assetObj["unknownIndex"] = asset.unknownIndex
        assetObj["null1"] = asset.null1
        for instance in asset.instances:
            instanceName = assetName + "-Instance"
            createLayObject(instanceName, layInstancesCollection, instanceRootNode, instance.position, instance.rotation, instance.scale, boundingBox)

    print('Importing finished. ;)')
    return {'FINISHED'}

def createLayObject(name, collection, parent, pos, rot, scale, boundingBox):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.parent = parent
    obj.empty_display_type = 'SPHERE'
    obj.empty_display_size = 0.5

    obj.location = pos
    obj.rotation_euler = rot
    obj.scale = scale

    obj.show_axis = True

    if boundingBox != None:
        createBoundingBoxObject(obj, name + "-BoundingBox", collection, boundingBox)

    return obj



def createBoundingBoxObject(obj: bpy.types.Object, name, collection, boundingBox):
    boundingBoxObj = bpy.data.objects.new(name, None)
    collection.objects.link(boundingBoxObj)
    for child in obj.children:
        bpy.data.objects.remove(child, do_unlink=True)
    boundingBoxObj.parent = obj
    boundingBoxObj.empty_display_type = 'CUBE'

    boundingBoxObj.location = boundingBox[:3]
    boundingBoxObj.scale = boundingBox[-3:]

    boundingBoxObj.hide_select = True

def getModelBoundingBox(modelName, addonName):
    data005_dir = bpy.context.preferences.addons[addonName].preferences.data005_dir
    data015_dir = bpy.context.preferences.addons[addonName].preferences.data015_dir

    if not os.path.isdir(data005_dir) or not os.path.isdir(data015_dir):
        return None

    #print("Model To Find", modelName)

    fileFound = False
    filePath = ""
    # Search data005.cpk
    for pathName in os.listdir(data005_dir):
        if fileFound:
            break
        fullPathName = os.path.join(data005_dir, pathName)
        if os.path.isdir(fullPathName):
            for file in os.listdir(fullPathName):
                if file == (modelName + ".dtt"):
                    filePath = fullPathName + "\\" + file
                    fileFound = True
                    break
        else:
            if pathName == (modelName + ".dtt"):
                filePath = fullPathName + "\\" + pathName
                fileFound = True
                break

    # Search data015.cpk
    for pathName in os.listdir(data015_dir):
        if fileFound:
            break
        fullPathName = os.path.join(data015_dir, pathName)
        if os.path.isdir(fullPathName):
            for file in os.listdir(fullPathName):
                if file == (modelName + ".dtt"):
                    filePath = fullPathName + "\\"  + file
                    fileFound = True
                    break
        else:
            if pathName == (modelName + ".dtt"):
                filePath = fullPathName + "\\" + pathName
                fileFound = True
                break

    if not fileFound:
        return None

    modelDTTFile = open(filePath, "rb")
    id = modelDTTFile.read(4)
    numFiles = to_uint(modelDTTFile.read(4))
    fileOffsetsOffset = to_uint(modelDTTFile.read(4))
    fileExtensionsOffset = to_uint(modelDTTFile.read(4))

    fileOffsets = []
    modelDTTFile.seek(fileOffsetsOffset)
    for i in range(numFiles):
        fileOffsets.append(to_uint(modelDTTFile.read(4)))
    
    fileExtensions = []
    modelDTTFile.seek(fileExtensionsOffset)
    for i in range(numFiles):
        fileExtensions.append(to_string(modelDTTFile.read(4)))

    for i, ext in enumerate(fileExtensions):
        if ext == "wmb":
            modelDTTFile.seek(fileOffsets[i] + 16)
            boundingBox = [to_float(modelDTTFile.read(4)) for val in range(6)]
            modelDTTFile.close()
            return boundingBox
