import bpy
import os
import struct
from pathlib import Path

# Replace the import statement below with the correct path to your WMB importer
from ...wmb.importer import wmb_importer  # Assuming wmb_importer.py is in root/wmb/importer

def ImportSCR(file_path, context):
    with open(file_path, 'rb') as scr_file:
        # Read header
        header = struct.unpack('<4s2hI', scr_file.read(12))
        num_models = header[2]
        offset_offsets_models = header[3]

        # Read model offsets
        scr_file.seek(offset_offsets_models)
        offsets_models = struct.unpack(f'<{num_models}I', scr_file.read(4 * num_models))

        # Read model headers
        model_headers = []
        for offset in offsets_models:
            scr_file.seek(offset)
            model_header = struct.unpack('<I64s9f18h', scr_file.read(108))
            model_headers.append(model_header)

        # Read model data and call WMB importer for each model
        for i, model_header in enumerate(model_headers):
            scr_file.seek(model_header[0])
            if i == num_models - 1:
                size = os.path.getsize(file_path) - model_header[0]
            else:
                size = offsets_models[i + 1] - model_header[0]

            model_data = scr_file.read(size)
            model_name = model_header[1].decode('utf-8').rstrip('\x00')

            # Save model data to a temporary file
            temp_wmb_file = Path(file_path).parent / f'{model_name}.wmb'
            with open(temp_wmb_file, 'wb') as wmb_file:
                wmb_file.write(model_data)

            # Call the WMB importer
            wmb_importer.main(str(temp_wmb_file), context)

            # Delete the temporary WMB file
            os.remove(temp_wmb_file)

def reset_blend():
    #bpy.ops.object.mode_set(mode='OBJECT')
    for collection in bpy.data.collections:
        for obj in collection.objects:
            collection.objects.unlink(obj)
        bpy.data.collections.remove(collection)
    for bpy_data_iter in (bpy.data.objects, bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.libraries):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    for amt in bpy.data.armatures:
        bpy.data.armatures.remove(amt)
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
        obj.user_clear()