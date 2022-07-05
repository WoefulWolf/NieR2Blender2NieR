import time

from ...utils.ioUtils import create_wmb, close_wmb
from .generate_data import *
from .write_wmb import *

normals_flipped = False

def flip_all_normals():
    normals_flipped = True
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.data.flip_normals()
    print('Flipped normals of all meshes.')

def purge_unused_materials():
    for material in bpy.data.materials:
        if not material.users:
            print('Purging unused material:', material)
            bpy.data.materials.remove(material)

def prepare_blend():
    print('Preparing .blend File:')
    for obj in bpy.data.collections['WMB'].all_objects:
        if obj.type not in ['MESH', 'ARMATURE', 'EMPTY']:
            print(obj.type, obj.name)
            print('[-] Removed ', obj)
            bpy.data.objects.remove(obj)

def restore_blend():
    print('Restoring .blend File:')
    # Do shit here if needed
    print('EXPORT COMPLETE. :D')
    return {'FINISHED'}

def main(filepath):
    start_time = int(time.time())
    prepare_blend()
    
    wmb_file = create_wmb(filepath)

    generated_data = c_generate_data()

    print('-=# All Data Generated. Writing WMB... #=-')

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

    if generated_data.colTreeNodes is not None:
        print('Writing colTreeNodes.')
        create_wmb_colTreeNodes(wmb_file, generated_data)

    print('Writing boneSets.')
    if hasattr(generated_data, 'boneSet'):
        create_wmb_boneSet(wmb_file, generated_data)

    if generated_data.boneMap is not None:
        print('Writing boneMap.')
        create_wmb_boneMap(wmb_file, generated_data)

    print('Writing meshes.')
    create_wmb_meshes(wmb_file, generated_data)

    print('Writing materials.')
    create_wmb_materials(wmb_file, generated_data)

    if generated_data.unknownWorldData is not None:
        print('Writing unknownWorldData.')
        create_wmb_unknownWorldData(wmb_file, generated_data)

    print('Finished writing. Closing file..')
    close_wmb(wmb_file, generated_data)

    end_time = int(time.time())
    export_duration = end_time - start_time
    export_min, export_sec = divmod(export_duration, 60)
    export_min = str(export_min).zfill(2)
    export_sec = str(export_sec).zfill(2)
    formatted_export = export_min + ':' + export_sec
    print(' - WMB generation took:', formatted_export, 'minutes.')
    
    return {'FINISHED'}