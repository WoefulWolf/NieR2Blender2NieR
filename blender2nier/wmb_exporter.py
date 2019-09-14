import bpy, bmesh, math
from blender2nier.util import *
from blender2nier.generate_data import *
from blender2nier.header.wmb_header import *
from blender2nier.bones.wmb_bones import *

def reset_blend():
    print('Preparing .blend File:')
    for obj in bpy.data.objects:
        if obj.type not in ['MESH', 'ARMATURE']:
            print('[-] Removing ', obj)
            bpy.data.objects.remove(obj)

def main(filepath):
    reset_blend()

    wmb_file = create_wmb(filepath)

    generated_data = c_generate_data()

    create_wmb_header(wmb_file, generated_data)

    #create_wmb_bones(wmb_file, generated_data)
    
    close_wmb(wmb_file)
    return {'FINISHED'}