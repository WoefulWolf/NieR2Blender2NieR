import math

from ...utils.ioUtils import to_float, to_uint, to_string
from .lay import Lay
from ...utils.util import *


def main(layFilePath, addonName):
    with open(layFilePath, "rb") as layFile:
        print("Parsing Lay file...", layFilePath)
        lay = Lay(layFile)

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

    if boundingBox is not None:
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

def searchDirForModel(dir: str, modelName: str, depth = 0) -> str:
    if depth > 0 and dir.endswith("nier2blender_extracted") or depth > 6:
        return None

    for entry in os.scandir(dir):
        if entry.is_file() and entry.name == modelName:
            if entry.name.startswith(modelName):
                return entry.path
        elif entry.is_dir():
            modelPath = searchDirForModel(entry.path, modelName, depth + 1)
            if modelPath is not None:
                return modelPath
    
    return None

def getModelBoundingBox(modelName, addonName):
    searchDirs = bpy.context.preferences.addons[addonName].preferences.assetDirs
    searchDirs = [dir.directory for dir in searchDirs]

    filePath = ""
    for pathName in searchDirs:
        if not os.path.isdir(pathName):
            continue
        
        modelPath = searchDirForModel(pathName, modelName + ".dtt")
        if modelPath is not None:
            filePath = modelPath
            break

    if not filePath:
        return None

    with open(filePath, "rb") as modelDTTFile:
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
                return boundingBox
