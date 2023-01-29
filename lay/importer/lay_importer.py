from __future__ import annotations
import math
from time import time

from ...utils.ioUtils import to_string, read_float, read_uint32
from .lay import Lay
from ...utils.util import *


def main(layFilePath):
    t1 = time()

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
        assetObj = createLayObject(assetName, layAssetsCollection, assetRootNode, asset.position, asset.rotation, asset.scale)
        assetObj["unknownIndex"] = asset.unknownIndex
        assetObj["null1"] = asset.null1
        for instance in asset.instances:
            instanceName = assetName + "-Instance"
            createLayObject(instanceName, layInstancesCollection, instanceRootNode, instance.position, instance.rotation, instance.scale)

    tD = time() - t1
    print(f"Importing finished in {tD:.1}s ;)")
    return {'FINISHED'}

def createLayObject(name, collection, parent, pos, rot, scale):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.parent = parent
    obj.empty_display_type = 'SPHERE'
    obj.empty_display_size = 0.5

    obj.location = pos
    obj.rotation_euler = rot
    obj.scale = scale

    obj.show_axis = True

    updateVisualizationObject(obj, name[:6], True)

    return obj

def updateVisualizationObject(emptyObj: bpy.types.Object, modelName: str, isParentRotated: bool) -> None:
    if emptyObj is not None:
        # clear objects from old addon versions
        for child in emptyObj.children:
            bpy.data.objects.remove(child, do_unlink=True)
    
    visColl = linkAssetModel(modelName, isParentRotated) or createBoundingBoxCollection(modelName)
    if visColl is not None:
        emptyObj.instance_type = "COLLECTION"
        emptyObj.instance_collection = visColl
        emptyObj.empty_display_type = "ARROWS"
        emptyObj.empty_display_size = 0.15
        emptyObj.show_axis = False
    else:
        emptyObj.instance_type = "NONE"
        emptyObj.instance_collection = None
        emptyObj.empty_display_type = "SPHERE"
        emptyObj.empty_display_size = 0.5
        emptyObj.show_axis = True

def createBoundingBoxCollection(modelName: str) -> bpy.types.Collection | None:
    bbCollName = f"{modelName}_BoundingBox"

    if bbCollName in bpy.data.collections:
        return bpy.data.collections[bbCollName]

    boundingBox = getModelBoundingBox(modelName)
    if boundingBox is None:
        return None

    boundingBoxObj = bpy.data.objects.new(f"{modelName}_BoundingBox", None)
    bbColl = bpy.data.collections.new(bbCollName)
    bbColl.objects.link(boundingBoxObj)
    boundingBoxObj.empty_display_type = "CUBE"

    boundingBoxObj.location = boundingBox[:3]
    boundingBoxObj.scale = boundingBox[-3:]

    return bbColl

def searchDirForModel(dir: str, modelName: str, depth = 0) -> str | None:
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

def getModelBoundingBox(modelName):
    searchDirs = getPreferences().assetDirs
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
        modelDTTFile.read(4) # id
        numFiles = read_uint32(modelDTTFile)
        fileOffsetsOffset = read_uint32(modelDTTFile)
        fileExtensionsOffset = read_uint32(modelDTTFile)

        fileOffsets = []
        modelDTTFile.seek(fileOffsetsOffset)
        for i in range(numFiles):
            fileOffsets.append(read_uint32(modelDTTFile))

        fileExtensions = []
        modelDTTFile.seek(fileExtensionsOffset)
        for i in range(numFiles):
            fileExtensions.append(to_string(modelDTTFile.read(4)))

        for i, ext in enumerate(fileExtensions):
            if ext == "wmb":
                modelDTTFile.seek(fileOffsets[i] + 16)
                boundingBox = [read_float(modelDTTFile) for _ in range(6)]
                return boundingBox

def linkAssetModel(modelName, isParentRotated: bool) -> bpy.types.Collection | None:
    linkedCollName = f"{modelName}_linked"

    # link file for first object
    if linkedCollName not in bpy.data.collections:
        searchDirs = getPreferences().assetBlendDirs
        searchDirs = [dir.directory for dir in searchDirs]

        filePath = ""
        for pathName in searchDirs:
            if not os.path.isdir(pathName):
                continue

            modelPath = searchDirForModel(pathName, modelName + ".blend")
            if modelPath is not None:
                filePath = modelPath
                break

        if not filePath:
            return None

        libName = f"{modelName}.blend"
        if libName in bpy.data.libraries:
            bpy.data.libraries.remove(bpy.data.libraries[libName])
        with bpy.data.libraries.load(filepath = filePath, link = True, relative = True) as (data_from, data_to):
            data_to.collections = [modelName]
        if modelName in bpy.data.objects and bpy.data.objects[modelName].instance_type == "COLLECTION":
            bpy.data.objects.remove(bpy.data.objects[modelName], do_unlink=True)
        linkedColl = bpy.data.collections[modelName]
        linkedColl.name = linkedCollName
        if isParentRotated and len(linkedColl.objects) > 0:
            linkedColl.objects[0].rotation_euler[0] = 0

    return bpy.data.collections[linkedCollName]
