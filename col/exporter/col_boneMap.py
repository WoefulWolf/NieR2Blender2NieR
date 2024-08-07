from io import BufferedWriter
from typing import List, Dict

import bpy

from ...utils.util import getBoneID

from ...utils.ioUtils import write_uInt32

class BoneMap:
    map: List[int]
    boneToMapIndex: Dict[str, int]
    structSize: int
    type = 1

    def __init__(self):
        armature = getArmature()
        if not armature:
            self.map = []
            self.structSize = 0
            return
        allBones = []
        for obj in bpy.data.collections["COL"].objects:
            if not self.isObjPartOfMap(obj):
                continue
            for vg in obj.vertex_groups:
                bone = armature.pose.bones[vg.name]
                if bone not in allBones:
                    allBones.append(bone)

        self.map = [
            getBoneID(bone) for bone in allBones
        ]
        self.boneToMapIndex = {
            bone.name: i for i, bone in enumerate(allBones)
        }

        self.structSize = len(self.map) * 4

    def isObjPartOfMap(self, obj: bpy.types.Object) -> bool:
        return len(obj.vertex_groups) == 1

    def writeToFile(self, offset: int, file: BufferedWriter):
        file.seek(offset)
        for boneId in self.map:
            write_uInt32(file, boneId)

class BoneMap2(BoneMap):
    type = 2

    def isObjPartOfMap(self, obj: bpy.types.Object) -> bool:
        return len(obj.vertex_groups) > 1

    def writeToFile(self, offset: int, file: BufferedWriter):
        file.seek(offset)
        for boneId in self.map:
            write_uInt32(file, boneId)

def getArmature() -> bpy.types.Armature:
    if "WMB" in bpy.data.collections:
        for armObj in bpy.data.collections["WMB"].all_objects:
            if armObj.type == "ARMATURE":
                return armObj
    return None
