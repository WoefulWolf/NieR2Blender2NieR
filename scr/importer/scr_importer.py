import bpy
import os
import struct
from pathlib import Path
import shutil
# Replace the import statement below with the correct path to your WMB importer
from ...wmb.importer import wmb_importer  # Assuming wmb_importer.py is in root/wmb/importer

class ImportSCR:
    def main(file_path, context):
        print('Beginning export')
        head = os.path.split(file_path)[0]
        with open(file_path, 'rb') as f:
            id = f.read(4)
            print('ID read')
            if id != b'SCR\x00':
                raise ValueError("Wrong file type")
    
            f.seek(0)
            header = struct.unpack('<4s2hI', f.read(12))
            num_models = header[2]
            offset_offsets_models = header[3]
        
            f.seek(offset_offsets_models)
            offsets_models = struct.unpack(f'<{num_models}I', f.read(num_models * 4))
            print('Offsets found')
        
            model_headers = []
            for i in range(num_models):
                f.seek(offsets_models[i])
                model_header = struct.unpack('<I64s9f18h', f.read(140))
                model_headers.append(model_header)
                print('Model header read')
        
            model_data = []
            for i in range(num_models):
                f.seek(model_headers[i][0])
                if i == num_models - 1:
                    size = os.path.getsize(file_path) - model_headers[i][0]
                else:
                    size = offsets_models[i+1] - model_headers[i][0]
                if size > 0:
                    model = f.read(size)
                    model_data.append(model)
                    print('SCR read completed')
                    print('Beginning extract')
                    if not os.path.exists(head + '/extracted_scr'):
                        os.makedirs(head + '/extracted_scr')
                
                    for i, (header, model) in enumerate(zip(model_headers, model_data)):
                        file_name = header[1].decode('utf-8').rstrip('\x00')
                        file_path = f"{head}/extracted_scr/{file_name}.wmb"
                        with open(file_path, 'wb') as f2:
                            f2.write(model)
                    print('SCR extract completed')
                    if not (context):
                        print('Beginning WMB import')                    
                        ImportSCR.import_models(file_path)  
                        
                print('SCR extract completed')
                
            return {'FINISHED'}

    @staticmethod
    def import_models(file_path):
            wmb_importer.main(False, file_path)

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