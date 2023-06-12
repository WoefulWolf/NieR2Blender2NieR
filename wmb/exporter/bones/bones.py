import bpy
import numpy as np
from ....utils.util import Vector3, getAllBonesInOrder
import mathutils as mu

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
                for bone in getAllBonesInOrder("WMB"):
                    ID = bone['ID']

                    if bone.parent:
                        parentIndex = getAllBonesInOrder("WMB").index(bone.parent)                                                     
                    else:
                        parentIndex = -1

                    # APOSE_position
                    position = Vector3(bone.head_local[0], bone.head_local[1], bone.head_local[2])
                
                    localRotation = [0, 0, 0]
                    rotation = [0, 0, 0]
                    
                    tPosition = [0, 0, 0]
                    localPosition = [0, 0, 0]
                    for obj in bpy.data.collections["WMB"].all_objects:
                        if obj.type == 'ARMATURE':
                            for pBone in obj.pose.bones:
                                if pBone.name == bone.name:
                                    #localRotation
                                    mat = pBone.matrix_basis.inverted().to_euler()
                                    localRotation[0] = mat.x
                                    localRotation[1] = mat.y
                                    localRotation[2] = mat.z

                                    #rotation
                                    full_rot_mat = pBone.matrix_basis.inverted().copy()
                                    for parent_pb in pBone.parent_recursive:
                                        full_rot_mat = parent_pb.matrix_basis.inverted() @ full_rot_mat
                                    euler = full_rot_mat.to_euler()
                                    rotation[0] = euler.x
                                    rotation[1] = euler.y
                                    rotation[2] = euler.z
                                    
                                    #TPOSE_worldPosition
                                    full_trans = pBone.head
                                    tPosition[0] = full_trans.x
                                    tPosition[1] = full_trans.y
                                    tPosition[2] = full_trans.z

                                    #TPOSE_localPosition
                                    trans = pBone.head - (pBone.parent.head if pBone.parent else mu.Vector([0, 0, 0]))
                                    localPosition[0] = trans[0]
                                    localPosition[1] = trans[1]
                                    localPosition[2] = trans[2]
                                    break
                            break

                    localScale = Vector3(1, 1, 1)                           
                    scale = localScale

                    blenderName = bone.name
                    
                    bone = [ID, parentIndex, localPosition, localRotation, localScale.xyz, position.xyz, rotation, scale.xyz, tPosition, blenderName]
                    _bones.append(bone)
                
            elif numBones == 1:
                for bone in getAllBonesInOrder("WMB"):
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