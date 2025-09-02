import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ...utils.visibilitySwitcher import enableVisibilitySelector
from ...utils.util import setExportFieldsFromImportFile, getAllMeshObjectsInOrder

def copy_property_group(source_obj, target_obj, prop_name="mesh_group_props"):
    source_props = getattr(source_obj, prop_name, None)
    target_props = getattr(target_obj, prop_name, None)

    if not source_props or not target_props:
        print("Property group not found on one of the objects.")
        return

    # Copy each property using RNA
    for prop_id in source_props.bl_rna.properties:
        if prop_id.is_readonly or prop_id.identifier in ["rna_type", "updated"]:
            continue  # Skip read-only/internal/updated properties

        value = getattr(source_props, prop_id.identifier)
        setattr(target_props, prop_id.identifier, value)

def on_mesh_group_props_update(self, context):
    if self.updated:
        return
    if not context.object:
        return
    source_obj = context.object
    source_mesh_name = source_obj.name.split('.')[0]
    objects = getAllMeshObjectsInOrder('WMB')
    for obj in objects:
        if obj == source_obj:
            continue
        mesh_name = obj.name.split('.')[0]
        if mesh_name == source_mesh_name:
            obj.mesh_group_props.updated = True
            copy_property_group(source_obj, obj)
            obj.mesh_group_props.updated = False

class MeshGroupProps(bpy.types.PropertyGroup):
    updated: bpy.props.BoolProperty(
        name="Updated",
        default=False
    )
    # Index
    override_index: bpy.props.BoolProperty(
        name="Override Index",
        default=False,
        update=on_mesh_group_props_update
    )
    index: bpy.props.IntProperty(
        name="Index",
        default=-1,
        update=on_mesh_group_props_update
    )
    lod_level: bpy.props.IntProperty(
        name="LOD Level",
        default=0,
        update=on_mesh_group_props_update
    )
    lod_name: bpy.props.StringProperty(
        name="LOD Name",
        default="LOD0",
        update=on_mesh_group_props_update
    )


class B2N_PT_MeshGroupProperties(bpy.types.Panel):
    bl_label = "NieR:Automata Mesh Group Properties"
    bl_idname = "OBJECT_PT_mesh_group_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Index
        box = layout.box()
        row = box.row()
        row.prop(obj.mesh_group_props, "override_index")
        if obj.mesh_group_props.override_index:
            row.prop(obj.mesh_group_props, "index")
        # LOD
        box = layout.box()
        row = box.row()
        row.prop(obj.mesh_group_props, "lod_name", text="")
        row.prop(obj.mesh_group_props, "lod_level")

class ImportNierWmb(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata WMB File.'''
    bl_idname = "import_scene.wmb_data"
    bl_label = "Import WMB Data"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)
    import_mesh_indices: bpy.props.BoolProperty(name="Import Mesh Group Indices (Bayonetta 3)", default=False)

    def execute(self, context):
        from . import wmb_importer
        if self.reset_blend:
            wmb_importer.reset_blend()

        setExportFieldsFromImportFile(self.filepath, False)
        enableVisibilitySelector()

        return wmb_importer.main(False, self.filepath, self.import_mesh_indices)
