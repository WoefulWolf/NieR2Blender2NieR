import bpy, bmesh, math
from blender2nier.util import *
from blender2nier.generate_data import *
from blender2nier.wmb.wmb_header import *
from blender2nier.wmb.wmb_bones import *
from blender2nier.wmb.wmb_boneIndexTranslateTable import *
from blender2nier.wmb.wmb_vertexGroups import *
from blender2nier.wmb.wmb_batches import *
from blender2nier.wmb.wmb_lods import *
from blender2nier.wmb.wmb_meshMaterials import *
from blender2nier.wmb.wmb_boneMap import *
from blender2nier.wmb.wmb_meshes import *
from blender2nier.wmb.wmb_materials import *
from blender2nier.wmb.wmb_boneSet import *

normals_flipped = False

def flip_all_normals():
    normals_flipped = True
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.data.flip_normals()
    print('Flipped normals of all meshes.')

def prepare_blend():
    print('Preparing .blend File:')
    print('Triangulating meshes.')
    for obj in bpy.data.objects:
        if obj.type == 'MESH':

            # Triangulate meshes
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_add(type='TRIANGULATE')
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Triangulate")

            # Add object to pool to have tangents calculated in parallel
        if obj.type not in ['MESH', 'ARMATURE']:
            print('[-] Removed ', obj)
            bpy.data.objects.remove(obj)

def restore_blend():
    print('Restoring .blend File:')
    if normals_flipped:
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                obj.data.flip_normals()

def main(filepath):
    prepare_blend()
    
    wmb_file = create_wmb(filepath)

    generated_data = c_generate_data()

    create_wmb_header(wmb_file, generated_data)

    print('Writing bones.')
    if generated_data.bones is not None:
        create_wmb_bones(wmb_file, generated_data)

    print('Writing boneIndexTranslateTable.')
    if hasattr(generated_data, 'boneIndexTranslateTable'):
        create_wmb_boneIndexTranslateTable(wmb_file, generated_data)

    print('Writing vertexGroups.')
    create_wmb_vertexGroups(wmb_file, generated_data)

    print('Writing batches.')
    create_wmb_batches(wmb_file, generated_data)
    
    print('Writing LODs.')
    create_wmb_lods(wmb_file, generated_data)

    print('Writing meshMaterials.')
    create_wmb_meshMaterials(wmb_file, generated_data)

    print('Writing boneSets.')
    if hasattr(generated_data, 'boneSet'):
        create_wmb_boneSet(wmb_file, generated_data)

    print('Writing boneMap.')
    if generated_data.boneMap is not None:
        create_wmb_boneMap(wmb_file, generated_data)

    print('Writing meshes.')
    create_wmb_meshes(wmb_file, generated_data)

    print('Writing materials.')
    create_wmb_materials(wmb_file, generated_data)

    print('Finished writing. Closing file..')
    close_wmb(wmb_file)

    restore_blend()
    
    print('EXPORT COMPLETE. :D')
    return {'FINISHED'}