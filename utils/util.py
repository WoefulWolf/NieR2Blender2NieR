from __future__ import annotations
from functools import wraps
import json
import os
import textwrap
from threading import Timer
from time import time
from typing import Callable, Dict, List
import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .ioUtils import read_uint32
from ..consts import ADDON_NAME, DAT_EXTENSIONS


class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.xyz = [x, y, z]

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
        self.layout.alignment = 'CENTER'
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def drawMultilineLabel(context, text, parent):
    """Stolen from https://b3d.interplanety.org/en/multiline-text-in-blender-interface-panels/"""
    chars = int(context.region.width / (6 *  bpy.context.preferences.system.ui_scale))   # 6 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    col = parent.column(align=True)
    for text_line in text_lines:
        col.label(text=text_line)

def getUsedMaterials():
    materials = []
    for obj in (x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"):
        for slot in obj.material_slots:
            material = slot.material
            if material not in materials:
                materials.append(material)
    return materials

def getObjectCenter(obj):
    obj_local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    #obj_global_bbox_center = obj.matrix_world @ obj_local_bbox_center
    return obj_local_bbox_center

def getGlobalBoundingBox():
    xVals = []
    yVals = []
    zVals = []

    for obj in (x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"):
        xVals.extend([getObjectCenter(obj)[0] - obj.dimensions[0]/2, getObjectCenter(obj)[0] + obj.dimensions[0]/2])
        yVals.extend([getObjectCenter(obj)[1] - obj.dimensions[1]/2, getObjectCenter(obj)[1] + obj.dimensions[1]/2])
        zVals.extend([getObjectCenter(obj)[2] - obj.dimensions[2]/2, getObjectCenter(obj)[2] + obj.dimensions[2]/2])

    minX = min(xVals)
    maxX = max(xVals)
    minY = min(yVals)
    maxY = max(yVals)
    minZ = min(zVals)
    maxZ = max(zVals)

    midPoint = [(minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2]
    scale = [maxX - midPoint[0], maxY - midPoint[1], maxZ - midPoint[2]]
    return midPoint, scale

def getObjKey(obj):
    p1 = obj.name.split('-')
    if p1[0].isdigit():
        return f"{int(p1[0]):04d}-"
    else:
        return f"0000-{obj.name}"

def objectsInCollectionInOrder(collectionName):
    return sorted(bpy.data.collections[collectionName].objects, key=getObjKey) if collectionName in bpy.data.collections else []

def allObjectsInCollectionInOrder(collectionName):
    return sorted(bpy.data.collections[collectionName].all_objects, key=getObjKey) if collectionName in bpy.data.collections else []

def getChildrenInOrder(obj: bpy.types.Object) -> List[bpy.types.Object]:
    return sorted(obj.children, key=getObjKey)

def getAllBonesInOrder(collectionName):
    for obj in bpy.data.collections[collectionName].all_objects:
        if obj.type == 'ARMATURE':
            return list(obj.data.bones)

def getBoneIndexByName(collectionName, name):
    for i, bone in enumerate(getAllBonesInOrder(collectionName)):
        if bone.name == name:
            return i

def create_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

def print_class(obj):
    print ('\n'.join(sorted(['%s:\t%s ' % item for item in obj.__dict__.items() if item[0].find('Offset') < 0 or item[0].find('unknown') < 0 ])))
    print('\n')

def getObjectVolume(obj):
    return np.prod(obj.dimensions)

def volumeInsideOther(volumeCenter, volumeScale, otherVolumeCenter, otherVolumeScale):
    xVals = [volumeCenter[0] - volumeScale[0]/2, volumeCenter[0] + volumeScale[0]/2]
    yVals = [volumeCenter[1] - volumeScale[1]/2, volumeCenter[1] + volumeScale[1]/2]
    zVals = [volumeCenter[2] - volumeScale[2]/2, volumeCenter[2] + volumeScale[2]/2]

    other_xVals = [otherVolumeCenter[0] - otherVolumeScale[0]/2, otherVolumeCenter[0] + otherVolumeScale[0]/2]
    other_yVals = [otherVolumeCenter[1] - otherVolumeScale[1]/2, otherVolumeCenter[1] + otherVolumeScale[1]/2]
    other_zVals = [otherVolumeCenter[2] - otherVolumeScale[2]/2, otherVolumeCenter[2] + otherVolumeScale[2]/2]

    if (max(xVals) <= max(other_xVals) and max(yVals) <= max(other_yVals) and max(zVals) <= max(other_zVals)):
        if (min(xVals) >= min(other_xVals) and min(yVals) >= min(other_yVals) and min(zVals) >= min(other_zVals)):
            return True
    return False

def getDistanceTo(pos, otherPos):
    return np.linalg.norm(otherPos - pos)

def getVolumeSurrounding(volumeCenter, volumeScale, otherVolumeCenter, otherVolumeScale):
    xVals = [volumeCenter[0] - volumeScale[0]/2, volumeCenter[0] + volumeScale[0]/2, otherVolumeCenter[0] - otherVolumeScale[0]/2, otherVolumeCenter[0] + otherVolumeScale[0]/2]
    yVals = [volumeCenter[1] - volumeScale[1]/2, volumeCenter[1] + volumeScale[1]/2, otherVolumeCenter[1] - otherVolumeScale[1]/2, otherVolumeCenter[1] + otherVolumeScale[1]/2]
    zVals = [volumeCenter[2] - volumeScale[2]/2, volumeCenter[2] + volumeScale[2]/2, otherVolumeCenter[2] - otherVolumeScale[2]/2, otherVolumeCenter[2] + otherVolumeScale[2]/2]

    minX = min(xVals)
    maxX = max(xVals)
    minY = min(yVals)
    maxY = max(yVals)
    minZ = min(zVals)
    maxZ = max(zVals)

    midPoint = [(minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2]
    scale = [maxX - midPoint[0], maxY - midPoint[1], maxZ - midPoint[2]]
    return midPoint, scale

class custom_ColTreeNode:
    def __init__(self):
        self.index = -1
        self.bObj = None

        self.position = [0, 0, 0]
        self.scale = [1, 1, 1]

        self.left = -1
        self.right = -1

        self.offsetMeshIndices = 0
        self.meshIndexCount = 0
        self.meshIndices = []

        self.structSize = 12 + 12 + (4 * 4)

    def getVolume(self):
        return np.prod(self.scale)

def triangulate_meshes(collection: str):
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.collections[collection].all_objects:
        if obj.type == 'MESH':
            # Triangulate
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            bm.to_mesh(me)
            bm.free()

def centre_origins(collection: str):
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.cursor.location = [0, 0, 0]
    for obj in bpy.data.collections[collection].all_objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            obj.select_set(False)

def setExportFieldsFromImportFile(filepath: str, isDatImport: bool) -> None:
    dir = os.path.dirname(filepath)
    if isDatImport:
        filename = os.path.basename(filepath)
        basename, ext = os.path.splitext(filename)
        datExt = ext if ext in DAT_EXTENSIONS else ".dat"
        datExtractedDir = os.path.join(dir, "nier2blender_extracted", basename + datExt)
        dttExtraDir = os.path.join(dir, "nier2blender_extracted", basename + ".dtt")
    else:
        filename = os.path.basename(dir)
        basename, ext = os.path.splitext(filename)
        datExt = ext if ext in DAT_EXTENSIONS else ".dat"
        parentDir = os.path.dirname(dir)
        if ext == ".dtt" or ext in DAT_EXTENSIONS:
            datExtractedDir = os.path.join(parentDir, basename + ".dat")
            dttExtraDir = os.path.join(parentDir, basename + ".dtt")
        else:
            print("Unknown DAT folder type")
            return
    
    if os.path.exists(datExtractedDir):
        bpy.context.scene.DatContents.clear()
        importContentsFileFromFolder(datExtractedDir, bpy.context.scene.DatContents)
    if os.path.exists(dttExtraDir):
        bpy.context.scene.DttContents.clear()
        importContentsFileFromFolder(dttExtraDir, bpy.context.scene.DttContents)

def getPreferences():
    return bpy.context.preferences.addons[ADDON_NAME].preferences

startTime = -1
timings: Dict[str, Dict|float] = {}

def setTiming(path: List[str], time: float, inner: Dict|None = None):
    if inner is None:
        inner = timings
    if len(path) == 1 and type(inner.get(path[0])) is dict:
        path.append("_TOTAL")
    if len(path) == 1:
        if path[0] not in inner:
            inner[path[0]] = 0
        inner[path[0]] += time
    else:
        if path[0] not in inner:
            inner[path[0]] = {}
        setTiming(path[1:], time, inner[path[0]])

def resetTimings():
    global timings, startTime
    timings = {}
    startTime = time()

def timing(path: List[str]):
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kw):
            # t1 = time()
            result = f(*args, **kw)
            # t2 = time()
            # setTiming(path, t2 - t1)
            return result
        return wrap
    return decorator

def printTimingsSection(total: float, inner: Dict, indent: int = 0):
    for key in inner:
        if type(inner[key]) is dict:
            print(" " * indent + key + ":")
            printTimingsSection(total, inner[key], indent + 4)
        else:
            print(f"{' ' * indent}{key}: {inner[key]/total:.1%}")

def printTimings():
    print("Timings:")
    print(json.dumps(timings, indent=4))
    total = time() - startTime
    print("Total: " + str(total))
    printTimingsSection(total, timings)

def setViewportColorTypeToObject():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = "SOLID"
                        space.shading.color_type = "OBJECT"

def importContentsFileFromFolder(folderPath: str, contentsList: bpy.types.CollectionProperty) -> bool:
    # search for metadata or json file
    datInfoJson = ""
    fileOrderMetadata = ""
    for file in os.listdir(folderPath):
        if file == "dat_info.json":
            datInfoJson = os.path.join(folderPath, file)
            break
        elif file == "file_order.metadata":
            fileOrderMetadata = os.path.join(folderPath, file)
    if datInfoJson:
        readJsonDatInfo(datInfoJson, contentsList)
    elif fileOrderMetadata:
        readFileOrderMetadata(fileOrderMetadata, contentsList)
    else:
        return False
    return True

def getFileSortingKey(file: str):
    base, ext = os.path.splitext(file)
    return (base.lower(), ext.lower())

def readJsonDatInfo(filepath: str, contentsList: bpy.types.CollectionProperty):
    with open(filepath, "r") as f:
        filesData = json.load(f)
    files = []
    dir = os.path.dirname(filepath)
    for file in filesData["files"]:
        files.append(os.path.join(dir, file))
    # remove duplicates and sort
    files = list(set(files))
    files.sort(key=getFileSortingKey)
    
    for file in files:
        added_file = contentsList.add()
        added_file.filepath = file
    
    # some old dev versions don't have these properties, for backwards compatibility
    if "basename" in filesData:
        bpy.context.scene.ExportFileName = filesData["basename"]
    else:
        bpy.context.scene.ExportFileName = os.path.splitext(os.path.basename(dir))[0]
    if "ext" in filesData:
        if filesData["ext"] != "dtt":
            bpy.context.scene.DatExtension = filesData["ext"].lower()
    elif not os.path.dirname(filepath).endswith(".dtt"):
        bpy.context.scene.DatExtension = "dat"

def readFileOrderMetadata(filepath: str, contentsList: bpy.types.CollectionProperty):
    if filepath.endswith("hash_order.metadata"):
        raise Exception("hash_order.metadata is not supported! Please use 'file_order.metadata' instead.")
        
    with open(filepath, "rb") as f:
        num_files = read_uint32(f)
        name_length = read_uint32(f)
        files = []
        for i in range(num_files):
            files.append(f.read(name_length).decode("utf-8").strip("\x00"))
        # remove duplicates and sort
        files = list(set(files))
        files.sort(key=getFileSortingKey)

        for file in files:
            added_file = contentsList.add()
            added_file.filepath = os.path.join(os.path.dirname(filepath), file)
    
    ext = os.path.splitext(filepath)[1]
    if ext == ".dtt" or ext in DAT_EXTENSIONS:
        bpy.context.scene.DatExtension = ext[1:]
        bpy.context.scene.ExportFileName = os.path.basename(filepath)[:-4]

def saveDatInfo(filepath: str, files: List[str], filename: str):
    files = list(set(files))
    files.sort(key=getFileSortingKey)
    base, ext = os.path.splitext(filename)
    with open(filepath, 'w') as f:
        jsonFiles = {
            "version": 1,
            "files": files,
            "basename": base,
            "ext": ext[1:]
        }
        json.dump(jsonFiles, f, indent=4)

class throttle(object):
    leading: bool
    trailing: bool

    timeout: Timer
    milliseconds: float
    previous: float
    function: Callable|None
    args: List
    kwargs: Dict

    def __init__(self, milliseconds: float, leading=False, trailing=True):
        self.leading = leading
        self.trailing = trailing
        self.milliseconds = milliseconds
        self.timeout = None
        self.previous = 0
        self.function = None
    
    def later(self):
        self.previous = time() if self.leading else 0
        self.timeout = None
        self.function(*self.args, **self.kwargs)
    
    def __call__(self, fn):
        self.function = fn
        def wrapper(*args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            now = time() * 1000
            if self.previous != 0 and not self.leading:
                self.previous = now
            remaining = self.milliseconds - (now - self.previous)
            if remaining <= 0 or remaining > self.milliseconds:
                if self.timeout:
                    self.timeout.cancel()
                    self.timeout = None
                self.previous = now
                fn(*args, **kwargs)
            elif not self.timeout and self.trailing:
                self.timeout = Timer(remaining / 1000, self.later)
                self.timeout.start()
        return wrapper

def clamp(value: float, min: float, max: float) -> float:
    return min if value < min else max if value > max else value

def newGeometryNodesModifier(obj: bpy.types.Object) -> bpy.types.NodesModifier:
    modifier: bpy.types.NodesModifier = obj.modifiers.new("Geometry Nodes", "NODES")
    nodeTree = modifier.node_group
    if nodeTree is None:
        nodeTree = bpy.data.node_groups.new("Geometry Nodes", "GeometryNodeTree")
        modifier.node_group = nodeTree

        inputNode = nodeTree.nodes.new("NodeGroupInput")
        inputNode.location = (-200, 0)
        inputNode.outputs.new("NodeSocketGeometry", "Geometry")

        outputNode = nodeTree.nodes.new("NodeGroupOutput")
        outputNode.location = (200, 0)
        outputNode.inputs.new("NodeSocketGeometry", "Geometry")

        nodeTree.links.new(inputNode.outputs["Geometry"], outputNode.inputs["Geometry"])
    return modifier

