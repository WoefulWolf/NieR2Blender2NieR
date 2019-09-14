import bpy, bmesh, math
from blender2nier.bones.bones import *
from blender2nier.vertexGroups.vertexGroups import *

def get_numBatches():
    numBatches = 0
    return numBatches

def get_bones():
    bones = c_bones()
    return bones.bones

def get_vertexGroups():
    vertexGroups = c_vertexGroups(10, 0)
    return vertexGroups