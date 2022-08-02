import os

import bpy
from bpy_extras.io_utils import ImportHelper
import xml.etree.ElementTree as ET

class ImportNierSar(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Sar (Skeleton) File.'''
    bl_idname = "import_scene.sar"
    bl_label = "Import Sar Data"
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = ".sar"
    filter_glob: bpy.props.StringProperty(default="*.sar", options={'HIDDEN'})

    tryApplyingOffsets: bpy.props.BoolProperty(name="Try Applying Offsets", default=False)

    onlyToXml: bpy.props.BoolProperty(name="Only Convert To XML", default=False)
    recursivelyImport: bpy.props.BoolProperty(name="Import all recursively", default=False)

    def doImport(self, filepath):
        from . import sarImporter
        from ..common import bxm

        if self.onlyToXml:
            xml = bxm.bxmToXml(filepath)
            with open(filepath + ".xml", "wb") as f:
                f.write(ET.tostring(xml))
        else:
            sarImporter.importSar(filepath, self.tryApplyingOffsets)

    def execute(self, context):
        if self.recursivelyImport:
            directory = os.path.split(self.filepath)[0]
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".sar"):
                        self.doImport(os.path.join(root, file))
            print("Imported all file!")
        else:
            self.doImport(self.filepath)

        return {'FINISHED'}
