from __future__ import annotations
from functools import wraps
import json
import os
import textwrap
from time import time
from typing import Dict, List
import bmesh
import bpy
import numpy as np
from mathutils import Vector

from ..consts import ADDON_NAME


class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.xyz = [x, y, z]

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

def setExportFieldsFromImportFile(filepath: str) -> None:
    head = os.path.split(filepath)[0]
    tail = os.path.split(filepath)[1]
    tailless_tail = tail[:-4]
    extract_dir = os.path.join(head, 'nier2blender_extracted')

    bpy.context.scene.DatDir = os.path.join(extract_dir, tailless_tail + '.dat')
    bpy.context.scene.DttDir = os.path.join(extract_dir, tailless_tail + '.dtt')
    bpy.context.scene.ExportFileName = tailless_tail

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
