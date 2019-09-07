import bpy, bmesh, math
from blender2nier.util import *
from blender2nier.wmb_header import *

def reset_blend():
    print('Preparing .blend File:')
    for obj in bpy.data.objects:
        if obj.type not in ['MESH', 'ARMATURE']:
            print('[-] Removing ', obj)
            bpy.data.objects.remove(obj)

def main(filepath):
    reset_blend()

    wmb_file = create_wmb(filepath)

    create_wmb_head(wmb_file)
    
    close_wmb(wmb_file)
    return {'FINISHED'}