import bpy, bmesh, math
from blender2nier.util import Vector3

class c_bones(object):
    def __init__(self):

        def get_bones(self):
            _bones = []
            numBones = 0
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE':
                    numBones = len(obj.data.bones)

            if numBones > 1:
                ID = 0
                parentIndex = -1
                localPosition = Vector3(0, 0, 0)
                localRotation = Vector3(0, 0, 0)  
                localScale = Vector3(1, 1, 1)  
                position = localPosition
                rotation = localRotation
                scale = localScale
                tPosition = localPosition
                blenderName = '_0'
                bone = [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz, blenderName]
                _bones.append(bone)

                for obj in bpy.data.objects:
                    if obj.type == 'ARMATURE':
                        for bone in obj.data.bones:
                            ID = bone['ID']
                            if bone.parent:
                                parentIndex = int(bone.parent.name[-1])                                                         
                            else:
                                parentIndex = 0
                            localPosition = Vector3(round(bone.head_local[0], 6), round(bone.head_local[1], 6), round(bone.head_local[2], 6))
                            localRotation = Vector3(0, 0, 0)                                                                    # I haven't seen anything here besides 0, 0, 0.
                            localScale = Vector3(1, 1, 1)                                                                       # Same here but 1, 1, 1. Makes sense. Bones don't "really" have scale.

                            position = localPosition
                            rotation = localRotation
                            scale = localScale

                            tPosition = localPosition

                            blenderName = bone.name
                            bone = [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz, blenderName]
                            _bones.append(bone)
                
            elif numBones == 1:
                for obj in bpy.data.objects:
                    if obj.type == 'ARMATURE':
                        for bone in obj.data.bones:
                            ID = bone['ID']
                            parentIndex = -1                                                         
                            localPosition = Vector3(round(bone.head_local[0], 6), round(bone.head_local[1], 6), round(bone.head_local[2], 6))
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