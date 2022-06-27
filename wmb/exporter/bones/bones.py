import bpy

from ....util import Vector3


class c_bones(object):
    def __init__(self):

        def get_bones(self):
            _bones = []
            numBones = 0
            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'ARMATURE':
                    numBones = len(obj.data.bones)
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

                            localPosition = Vector3(bone['localPosition'][0], bone['localPosition'][1], bone['localPosition'][2])

                            localRotation = Vector3(bone['localRotation'][0], bone['localRotation'][1], bone['localRotation'][2])
                            localScale = Vector3(1, 1, 1)                                                                       # Same here but 1, 1, 1. Makes sense. Bones don't "really" have scale.

                            position = Vector3(bone.head_local[0], bone.head_local[1], bone.head_local[2])
                            rotation = Vector3(bone['worldRotation'][0], bone['worldRotation'][1], bone['worldRotation'][2])
                            scale = localScale

                            tPosition = Vector3(bone['TPOSE_worldPosition'][0], bone['TPOSE_worldPosition'][1], bone['TPOSE_worldPosition'][2])

                            blenderName = bone.name

                            bone = [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz, blenderName]
                            _bones.append(bone)
                
            elif numBones == 1:
                for obj in bpy.data.collections['WMB'].all_objects:
                    if obj.type == 'ARMATURE':
                        for bone in obj.data.bones:
                            ID = bone['ID']
                            parentIndex = -1                                                         
                            localPosition = Vector3(bone['localPosition'][0], bone['localPosition'][1], bone['localPosition'][2])
                            localRotation = Vector3(0, 0, 0)                                                                    # I haven't seen anything here besides 0, 0, 0.
                            localScale = Vector3(1, 1, 1)                                                                       # Same here but 1, 1, 1. Makes sense. Bones don't "really" have scale.

                            position = localPosition
                            rotation = localRotation
                            scale = localScale

                            tPosition = localPosition

                            blenderName = bone.name
                            bone = [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz, blenderName]
                            _bones.append(bone)

            return _bones
                        
        self.bones = get_bones(self)
        self.bones_StructSize = len(self.bones) * 88