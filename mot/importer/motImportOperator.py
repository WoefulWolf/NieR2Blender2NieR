import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
import os

from .motImporter import importMot

class ImportNierMot(bpy.types.Operator, ImportHelper):
    """Import a Nier Animation mot file"""
    bl_idname = "import_scene.mot"
    bl_label = "Import Nier Animation Data"
    bl_options = {'UNDO'}

    bulkImport: bpy.props.BoolProperty(name="Bulk Import", description="Import all mot files in the folder", default=False)
    filename_ext = ".mot"
    filter_glob: bpy.props.StringProperty(default="*.mot", options={'HIDDEN'})

    def execute(self, context):
        from .motImporter import importMot

        if not self.bulkImport:
            importMot(self.filepath, not self.bulkImport)
            self.report({'INFO'}, "Imported mot file")
        else:
            path = self.filepath if os.path.isdir(self.filepath) else os.path.dirname(self.filepath)
            allMotFiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".mot")]
            for i, file in enumerate(allMotFiles):
                print(f"Importing {file} ({i+1}/{len(allMotFiles)})")
                importMot(os.path.join(path, file), not self.bulkImport)
            
            print(f"Imported {len(allMotFiles)} mot files from {path}")
            self.report({'INFO'}, f"Imported {len(allMotFiles)} mot files")

        return {'FINISHED'}
