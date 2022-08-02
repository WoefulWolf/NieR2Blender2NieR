import os
import traceback
import xml.etree.ElementTree as ET

import bpy
from bpy_extras.io_utils import ImportHelper

class ImportNierYaxXml(bpy.types.Operator, ImportHelper):
    """Load a Nier:Automata Yax XML File."""
    bl_idname = "import_scene.yax_xml"
    bl_label = "Import Yax XML Data"
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = ".xml"
    filter_glob: bpy.props.StringProperty(default="*.xml", options={'HIDDEN'})

    importAllRecursively: bpy.props.BoolProperty(name="Import all recursively", default=False)

    def doImport(self, filepath):
        from .xmlToBlender import importXml
        try:
            xmlRoot = ET.parse(filepath).getroot()
            prefix = os.path.split(filepath)[1].split('.')[0]
            importXml(xmlRoot, prefix)
        except Exception as e:
            print("Failed to import " + filepath)
            print(traceback.format_exc())

    def execute(self, context):
        if self.importAllRecursively:
            directory = os.path.split(self.filepath)[0]
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".xml"):
                        self.doImport(os.path.join(root, file))
            print("Imported all files!")
        else:
            self.doImport(self.filepath)
        return {'FINISHED'}
