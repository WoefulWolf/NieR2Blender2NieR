import bmesh
import bpy

from .col_colTreeNodes import write_col_colTreeNodes
from .col_generate_data import COL_Data
from .col_header import write_col_header
from .col_meshes import write_col_meshes
from .col_namegroups import write_col_namegroups


def main(filepath, generateColTree):
    data = COL_Data(generateColTree)

    print('Creating col file: ', filepath)
    col_file = open(filepath, 'wb')

    print("Writing Header:")
    write_col_header(col_file, data)

    print("Writing NameGroups:")
    write_col_namegroups(col_file, data)

    print("Writing Meshes & Batches...")
    write_col_meshes(col_file, data)

    print("Writing ColTreeNodes...")
    write_col_colTreeNodes(col_file, data)

    print("Finished exporting", filepath, "\nGood luck! :S")

    col_file.flush()
    col_file.close()

def triangulate_meshes():
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.collections['COL'].all_objects:
        if obj.type == 'MESH':
            # Triangulate
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            bm.to_mesh(me)
            bm.free()   

def centre_origins():
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.cursor.location = [0, 0, 0]
    for obj in bpy.data.collections['COL'].all_objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            obj.select_set(False)