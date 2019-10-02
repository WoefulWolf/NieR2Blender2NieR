from blender2nier.util import *

def create_wmb_bones(wmb_file, data):

    for bone in data.bones.bones:               # [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz]
        write_Int16(wmb_file, bone[0])          # ID
        write_Int16(wmb_file, bone[1])          # parentIndex
        write_xyz(wmb_file, bone[2])            # localPosition.xyx
        write_xyz(wmb_file, bone[3])            # localRotation.xyz
        write_xyz(wmb_file, bone[4])            # localScale.xyz
        write_xyz(wmb_file, bone[5])            # position.xyz
        write_xyz(wmb_file, bone[6])            # rotation.xyz
        write_xyz(wmb_file, bone[7])            # scale.xyz
        write_xyz(wmb_file, bone[8])            # tPosition.xyz