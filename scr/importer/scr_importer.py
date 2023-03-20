import bpy
import os
from bpy_extras.io_utils import ImportHelper
from ...wmb.importer import wmb_importer  # Assuming wmb_importer.py is in root/wmb/importer

from . import SCRFile, SCR2File

class ImportSCR(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.scr"
    bl_label = "Import SCR"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".scr"
    filter_glob: bpy.props.StringProperty(default="*.scr", options={'HIDDEN'})

    def execute(self, context):
        # Clear existing scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True)

        # Load SCR file
        with open(self.filepath, 'rb') as f:
            if SCR2File.is_bayo2(f):
                scr = SCR2File.SCR2File(f)
            else:
                scr = SCRFile.SCRFile(f)

        # Load models
        for model_data in scr.each_model():
            # Load .wmb model using your existing .wmb importer function
            # You can pass the model_data file-like object directly to the function
            # or save it to a temporary file and pass the file path
            import_wmb_models(model_data)

        return {'FINISHED'}

def import_wmb_models(scr_file):
    for model in scr_file.models:
        wmb_importer.main(False, model)

def menu_func_import(self, context):
    self.layout.operator(ImportSCR.bl_idname, text="SCR (.scr)")

def register():
    bpy.utils.register_class(ImportSCR)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportSCR)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
