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
import glob
from collections import defaultdict

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
    for obj in getAllMeshObjectsInOrder('WMB'):
        for slot in obj.material_slots:
            material = slot.material
            if material not in materials:
                materials.append(material)
    return materials

def getNodeWithLabel(nodes, label):
    for node in nodes:
        if node.label == label:
            return node
    return None

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
    return obj.name

def objectsInCollectionInOrder(collectionName):
    return sorted(bpy.data.collections[collectionName].objects, key=getObjKey) if collectionName in bpy.data.collections else []

def allObjectsInCollectionInOrder(collectionName):
    return sorted(bpy.data.collections[collectionName].all_objects, key=getObjKey) if collectionName in bpy.data.collections else []

def getAllObjectsWithMaterial(collectionName, materialName):
    return [obj for obj in getAllMeshObjectsInOrder(collectionName) if obj.material_slots[0].material.name == materialName]

def getAllMeshObjectsInOrder(collectionName):
    objs = [obj for obj in allObjectsInCollectionInOrder(collectionName) if obj.type == "MESH"]
    objs = sorted(
        objs,
        key=lambda obj: (obj.mesh_group_props.lod_level < 0, obj.mesh_group_props.lod_level if obj.mesh_group_props.lod_level >= 0 else float('inf'))
    )
    objs = sorted(
        objs,
        key=lambda obj: obj.mesh_group_props.index if obj.mesh_group_props.override_index else float('inf')
    )
    return objs

def calculateVertexFlags(obj):
    # Has bones = 7, 8, 10, 11
    # 1 UV  = 0, 3
    # 2 UVs = 1, 4, 7, 10
    # 3 UVs = 5, 8, 11
    # 4 UVs = 14
    # 5 UVs = 12
    # Has Color = 3, 4, 5, 10, 11, 12, 14

    if getPreferences().maximizeShaderCompatibility:
        if len(obj.data.uv_layers) == 0:
            obj.data.uv_layers.new(name="UVMap1")

        if len(obj.data.uv_layers) == 1:
            obj.data.uv_layers.new(name="UVMap2")

        if len(obj.data.vertex_colors) == 0:
            vertex_color = obj.data.vertex_colors.new()
            vertex_color.active = True
            for loop_idx in range(len(obj.data.loops)):
                vertex_color.data[loop_idx].color = [0, 0, 0, 0]

    # You cannot have bones without at least 2 UVs
    if 'boneSetIndex' in obj and obj['boneSetIndex'] != -1:
        if len(obj.data.uv_layers) == 1:
            new_layer = obj.data.uv_layers.new(name="UVMap2")

    if len(obj.data.uv_layers) == 1:         # 0, 3
        if obj.data.vertex_colors:
            return 3
        else:
            return 0
    elif len(obj.data.uv_layers) == 2:       # 1, 4, 7, 10
        if 'boneSetIndex' in obj and obj['boneSetIndex'] != -1:        # > 7, 10
            if obj.data.vertex_colors:       # >> 10
                return 10
            else:                                               # >> 7
                return 7
        else:                                                   # > 1, 4
            if obj.data.vertex_colors:       # >> 4
                return 4
            else:                                               # >> 1
                return 1
    elif len(obj.data.uv_layers) == 3:       # 5, 8, 11
        if 'boneSetIndex' in obj and obj['boneSetIndex'] != -1:
            if obj.data.vertex_colors:       # >> 11
                return 11
            else:                                               # >> 8
                return 8
        else:                                                   # >> 5
            return 5
    elif len(obj.data.uv_layers) == 4:       # 14
        return 14
    elif len(obj.data.uv_layers) == 5:       # 12
        return 12
    else:
        return None

def getMeshVertexGroups(collectionName):
    meshes = getAllMeshObjectsInOrder(collectionName)
    group_map = {}

    for mesh in meshes:
        identifier = (calculateVertexFlags(mesh), mesh.mesh_group_props.lod_level)
        if identifier not in group_map:
            group_map[identifier] = []
        group_map[identifier].append(mesh)
    return list(group_map.values())

def getColMeshGroups(collectionName):
    def objToKey(obj):
        return str({
            'name': getMeshName(obj),
            'col_type': obj.col_mesh_props.col_type,
            'unk_col_type': obj.col_mesh_props.unk_col_type,
            'modifier': obj.col_mesh_props.modifier,
            'surface_type': obj.col_mesh_props.surface_type,
            'unk_surface_type': obj.col_mesh_props.unk_surface_type,
            'unk_byte': obj.col_mesh_props.unk_byte,
        })

    meshes = getAllMeshObjectsInOrder(collectionName)

    if bpy.context.scene["exportColTree"]:
        return [[x] for x in meshes]

    group_map = {}

    for mesh in meshes:
        identifier = objToKey(mesh)
        if identifier not in group_map:
            group_map[identifier] = []
        group_map[identifier].append(mesh)
    return list(group_map.values())

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
        
def getAllMeshNamesInOrder(collectionName):
    mesh_names = []
    for obj in getAllMeshObjectsInOrder(collectionName):
        mesh_name = getMeshName(obj)
        if mesh_name not in mesh_names:
            mesh_names.append(mesh_name)
    return mesh_names

def getMeshName(obj):
    return obj.name.split('.')[0].split('-')[0]

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

def setColourByCollisionType(obj):
    try:
        opacity = bpy.context.scene.collisionTools.globalAlpha
    except:
        opacity = 1.0

    collisionType = int(obj.col_mesh_props.col_type)
    if collisionType == 127:
        obj.color = [0.0, 1.0, 0.0, opacity]
    elif collisionType == 88:
        obj.color = [0.0, 0.5, 1.0, opacity]
    elif collisionType == 3:
        obj.color = [1.0, 0.5, 0.0, opacity]
    elif collisionType == 255:
        obj.color = [1.0, 0.0, 0.0, opacity]
    else:
        obj.color = [1.0, 0.45, 1.0, opacity]

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

def restore_import_pose(collection: str):
    if "NONE" in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions["NONE"])
    action = bpy.data.actions.new("NONE")
    for obj in allObjectsInCollectionInOrder(collection):
        if obj.type == "ARMATURE":
            if obj.animation_data:
                obj.animation_data.action = action
                bpy.context.view_layer.update()

            bpy.context.view_layer.objects.active = obj
            bpy.ops.b2n.restoreimportpose()
            obj.location = (0, 0, 0)
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = (0, 0, 0)
            obj.scale = (1, 1, 1)

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

def getTexture(texture_dir, texture_name):
    def either(c):
        return '[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c

    # First check if the texture is in the texture directory
    texture_search = os.path.join(texture_dir, ''.join(either(char) for char in texture_name) + ".*")
    texture_files = glob.glob(texture_search, recursive=True)
    if len(texture_files) > 0:
        return texture_files[0]
    
    # If not, check the preferences texture directories
    for dir in getPreferences().textureDirs:
        texture_search = os.path.join(dir.directory, ''.join(either(char) for char in texture_name) + ".*")
        texture_files = glob.glob(texture_search, recursive=True)
        if len(texture_files) > 0:
            return texture_files[0]
    return None

def getBoneFromID(bone_id):
    armatureObj = None
    for obj in bpy.data.collections['WMB'].all_objects:
        if obj.type == 'ARMATURE':
            armatureObj = obj
            break

    for bone in armatureObj.data.bones:
        if bone.name.split("_")[0].replace("bone", "").isdigit():
            if bone.name.split("_")[0].replace("bone", "") == str(bone_id):
                return bone

    return None

def boneHasID(bone):
    return bone.name.split("_")[0].replace("bone", "").isdigit()

def getBoneID(bone):
    return int(bone.name.split("_")[0].replace("bone", ""))

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

def getVersionString():
    from .. import __init__ as addon_main
    version = addon_main.bl_info["version"]
    version_string = ".".join(map(str, version))
    return version_string

def getFullVersionText():
    version_string = getVersionString()
    return f'WMB created with Blender2NieR v{version_string} by Woeful_Wolf'

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

