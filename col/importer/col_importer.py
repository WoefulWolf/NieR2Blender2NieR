import math

import bpy

from .col import Col


def main(colFilePath):
    # Setup Viewport
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = "SOLID"
                        space.shading.color_type = "OBJECT"
                        space.shading.show_backface_culling = True

    with open(colFilePath, "rb") as colFile:
        print("Parsing Col file...", colFilePath)
        col = Col(colFile)

    # Create COL Collection
    colCollection = bpy.data.collections.get("COL")
    if not colCollection:
        colCollection = bpy.data.collections.new("COL")
        bpy.context.scene.collection.children.link(colCollection)

    # Create meshes
    for meshIdx, mesh in enumerate(col.meshes):
        meshName = col.nameGroups.names[mesh.nameIndex]

        # Create batches
        for batchIdx, batch in enumerate(mesh.batches):
            objName = str(meshIdx) + "-" + meshName + "-" + str(batchIdx)
            objMesh = bpy.data.meshes.new(objName)
            obj = bpy.data.objects.new(objName, objMesh)
            colCollection.objects.link(obj)
            #obj.display_type = 'WIRE'
            obj.show_wire = True
            objMesh.from_pydata(batch.vertices, [], batch.indices)
            objMesh.update(calc_edges=True)

            try:
                obj.collisionType = str(mesh.collisionType)
            except:
                print("[!] Collision mesh flagged with unknown collisionType:", mesh.collisionType)
                obj.collisionType = "-1"
                obj["UNKNOWN_collisionType"] = mesh.collisionType

            obj.slidable = bool(mesh.slidable)
            obj["unknownByte"] = mesh.unknownByte

            try:
                obj.surfaceType = str(mesh.surfaceType)
            except:
                print("[!] Collision mesh flagged with unknown surfaceType:", mesh.surfaceType)
                obj.surfaceType = "-1"
                obj["UNKNOWN_surfaceType"] = mesh.surfaceType

            obj.rotation_euler = (math.radians(90),0,0)

    # Create colTreeNodes Sub-Collection
    colTreeNodesCollection = bpy.data.collections.get("col_colTreeNodes")
    if not colTreeNodesCollection:
        colTreeNodesCollection = bpy.data.collections.new("col_colTreeNodes")
        colCollection.children.link(colTreeNodesCollection)

    try:
        bpy.context.view_layer.active_layer_collection.children["COL"].children["col_colTreeNodes"].hide_viewport = True
    except:
        pass
    
    # Create colTreeNodes
    rootNode = bpy.data.objects.new("Root_col", None)
    rootNode.hide_viewport = True
    colTreeNodesCollection.objects.link(rootNode)
    rootNode.rotation_euler = (math.radians(90),0,0)
    for nodeIdx, node in enumerate(col.colTreeNodes):
        objName = str(nodeIdx) + "_" + str(node.left) + "_" + str(node.right) + "_col"
        obj = bpy.data.objects.new(objName, None)
        colTreeNodesCollection.objects.link(obj)
        obj.parent = rootNode
        obj.empty_display_type = 'CUBE'

        obj.location = node.p1
        obj.scale = node.p2

        if len(node.meshIndices) > 0:
            obj["meshIndices"] = node.meshIndices
    
    print('Importing finished. ;)')
    return {'FINISHED'}