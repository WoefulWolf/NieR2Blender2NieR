import bpy
import numpy as np
from ....utils.util import Vector3

def get_bone_tPosition(bone):
    if 'TPOSE_worldPosition' in bone:
        return Vector3(bone['TPOSE_worldPosition'][0], bone['TPOSE_worldPosition'][1], bone['TPOSE_worldPosition'][2])
    else:
        return Vector3(bone.head_local[0], bone.head_local[1], bone.head_local[2])

def get_bone_localPosition(bone):
    if bone.parent:
        if 'TPOSE_worldPosition' in bone.parent:
            parentTPosition = Vector3(bone.parent['TPOSE_worldPosition'][0], bone.parent['TPOSE_worldPosition'][1], bone.parent['TPOSE_worldPosition'][2])
            return get_bone_tPosition(bone) - parentTPosition
        else:
            return get_bone_tPosition(bone) - bone.parent.head_local
    else:
        return Vector3(0, 0, 0)

class c_bones(object):
    def __init__(self):

        def get_bones(self):
            _bones = []
            numBones = 0
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    numBones = len(obj.data.bones)
                    break
                    first_bone = obj.data.bones[0]

            if numBones > 1:
                for obj in bpy.data.collections['WMB'].all_objects:
                    if obj.type == 'ARMATURE':
                        for bone in obj.data.bones:
                            ID = bone['ID']

                            if bone.parent:
                                parent_name = bone.parent.name.replace('bone', '')
                                parentIndex = int(parent_name)                                                      
                            else:
                                parentIndex = -1

                            position = Vector3(bone.head_local[0], bone.head_local[1], bone.head_local[2])
                            tPosition = get_bone_tPosition(bone)
                            localPosition = get_bone_localPosition(bone)

                            child_tPosition = get_bone_tPosition(bone.children[0]) if len(bone.children) > 0 else Vector3(0, 0, 0)
                        

                            if 'localRotation' in bone:
                                localRotation = Vector3(bone['localRotation'][0], bone['localRotation'][1], bone['localRotation'][2])
                            else:
                                localRotation = Vector3(0, 0, 0)

                            if 'worldRotation' in bone:
                                rotation = Vector3(bone['worldRotation'][0], bone['worldRotation'][1], bone['worldRotation'][2])
                            else:
                                rotation = Vector3(0, 0, 0)

                            localScale = Vector3(1, 1, 1)                           
                            scale = localScale

                            blenderName = bone.name

                            bone = [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz, blenderName]
                            _bones.append(bone)
                        break
                
            elif numBones == 1:
                for obj in bpy.data.collections['WMB'].all_objects:
                    if obj.type == 'ARMATURE':
                        for bone in obj.data.bones:
                            ID = bone['ID']
                            parentIndex = -1                                                         
                            #localPosition = Vector3(bone['localPosition'][0], bone['localPosition'][1], bone['localPosition'][2])
                            localPosition = Vector3(bone.head_local[0], bone.head_local[1], bone.head_local[2])
                            localRotation = Vector3(0, 0, 0)
                            localScale = Vector3(1, 1, 1)

                            position = localPosition
                            rotation = localRotation
                            scale = localScale

                            tPosition = localPosition

                            blenderName = bone.name
                            bone = [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz, blenderName]
                            _bones.append(bone)
                        break

            return _bones
                        
        self.bones = get_bones(self)
        self.bones_StructSize = len(self.bones) * 88