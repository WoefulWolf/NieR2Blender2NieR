import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..exporter.col_ui_manager import enableCollisionTools
from ...utils.util import setExportFieldsFromImportFile, setColourByCollisionType, isObjInCollection

def updateCollisionType(self, context):
    if not context.object:
        return
    if self.col_type != "-1":
        self.unk_col_type = 0
    setColourByCollisionType(context.object)

def updateSurfaceType(self, context):
    if not context.object:
        return
    if self.surface_type != "-1":
        self.unk_surface_type = 0

collisionTypes = [
    ("-1", "UNKNOWN", ""),
    ("3", "Block Actors", "If modifier is enabled, this will not block players who are jumping (e.g. to prevent accidentally walking off ledges)."),
    ("88", "Water", ""),
    ("127", "Block All (Grabbable)", ""),
    ("255", "Block All", "")
]

colModifierTypes = [
    ("0", "None", ""),
    ("1", "Slidable", ""),
    ("2", "Transparent wall", ""),
    ("8", "Unknown (8)", ""),
    ("32", "Unknown (32)", ""),
    ("129", "Unknown (129)", ""),
]

surfaceTypes = [
    ("-1", "UNKNOWN", ""),
    ("0", "Concrete", ""),
    ("1", "Dirt", ""),
    ("2", "Rock", ""),
    ("3", "Metal Solid", ""),
    ("4", "Rubble", ""),
    ("5", "Metal Grate", ""),
    ("6", "Tree Trunk", ""),
    ("7", "Wood", ""),
    ("8", "Grass 1", ""),
    ("9", "Grass 2", ""),
    ("11", "Water", ""),
    ("12", "Sand", ""),
    ("13", "Gravel 1", ""),
    ("15", "Oil", ""),
    ("16", "Rubble 2", ""),
    ("17", "Crystallized Silicon & Carbon", ""),
    ("18", "Bunker Floor", ""),
    ("22", "Concrete 2", ""),
    ("23", "Metal Hollow", ""),
    ("24", "Flowers", "")
]

class ColMeshProps(bpy.types.PropertyGroup):
    col_type: bpy.props.EnumProperty(name="Collision Type", items=collisionTypes, update=updateCollisionType, default="255")
    unk_col_type: bpy.props.IntProperty(name="Unknown Collision Type", min=0, max=255)
    modifier: bpy.props.EnumProperty(name="Modifier", items=colModifierTypes)
    surface_type: bpy.props.EnumProperty(name="Surface Type", items=surfaceTypes, update=updateSurfaceType, default="0")
    unk_surface_type: bpy.props.IntProperty(name="Unknown Surface Type", min=0, max=255)
    unk_byte: bpy.props.IntProperty(name="Unknown Byte", min=0, max=255)

class B2N_PT_ColMeshProperties(bpy.types.Panel):
    bl_label = "NieR:Automata Collision Mesh Properties"
    bl_idname = "OBJECT_PT_col_mesh_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'MESH' and isObjInCollection(context.object, "COL")

    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        # Collision Type
        box = layout.box()
        row = box.row()
        row.prop(obj.col_mesh_props, "col_type")
        if obj.col_mesh_props.col_type == "-1":
            row = box.row()
            row.prop(obj.col_mesh_props, "unk_col_type")

        # Modifier
        box = layout.box()
        row = box.row()
        row.prop(obj.col_mesh_props, "modifier")

        # Surface Type
        box = layout.box()
        row = box.row()
        row.prop(obj.col_mesh_props, "surface_type")
        if obj.col_mesh_props.surface_type == "-1":
            row = box.row()
            row.prop(obj.col_mesh_props, "unk_surface_type")

        # Unknown Byte
        box = layout.box()
        row = box.row()
        row.prop(obj.col_mesh_props, "unk_byte")


class ImportNierCol(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Col (Collision) File.'''
    bl_idname = "import_scene.col_data"
    bl_label = "Import Col Data"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def execute(self, context):
        from . import col_importer

        setExportFieldsFromImportFile(self.filepath, False)
        enableCollisionTools()

        return col_importer.main(self.filepath)
