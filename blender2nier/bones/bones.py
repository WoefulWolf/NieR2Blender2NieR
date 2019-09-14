import bpy, bmesh, math
from blender2nier.util import Vector3

class c_bones(object):
    def __init__(self):

        def get_bones(self):
            _bones = []
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE':
                    for bone in obj.data.bones:
                        bone_shortID_split = bone.name.split('_')                                                          # Think this refers to the games boneID table, dunno what everything is so just check binary for now.
                        try:
                            bone_shortID = int(bone_shortID_split[-1])
                        except ValueError:
                            bone_shortID = -1

                        parentIndex = -1                                                                                    # This is complicated, will maybe sort out later

                        localPosition = Vector3(round(bone.head[0], 6), round(bone.head[1], 6), round(bone.head[2], 6))
                        localRotation = Vector3(0, 0, 0)                                                                    # I haven't seen anything here 0, 0, 0.
                        localScale = Vector3(1, 1, 1)                                                                       # Same here but 1, 1, 1. Makes sense. Bones don't "really" have scale.

                        position = localPosition
                        rotation = localRotation
                        scale = localScale

                        tPosition = localPosition

                        bone = [bone_shortID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz]
                        _bones.append(bone)
            return _bones
                        
        self.bones = get_bones(self)
        self.bones_StructSize = len(self.bones) * 88