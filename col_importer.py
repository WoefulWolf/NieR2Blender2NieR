import bpy, math
from .col import Col

collisionTypes = [
    ("-1", "UNKNOWN", ""),
    ("3", "Block Actors", "If modifier is enabled, this will not block players who are jumping (e.g. to prevent accidentally walking off ledges)."),
    ("88", "Water", ""),
    ("127", "Grabbable Block All", ""),
    ("255", "Block All", "")
]

# Identified by NSA Cloud
surfaceTypes = [
    ("-1", "UNKNOWN", ""),
    ("0", "Concrete1", ""),
    ("1", "Dirt", ""),
    ("2", "Concrete2", ""),
    ("3", "Metal Floor", ""),
    ("4", "Rubble", ""),
    ("5", "Metal Grate", ""),
    ("6", "Gravel", ""),
    ("7", "Rope Bridge", ""),
    ("8", "Grass", ""),
    ("9", "Wood Plank", ""),
    ("11", "Water", ""),
    ("12", "Sand", ""),
    ("13", "Rocky Gravel 1", ""),
    ("15", "Mud", ""),
    ("16", "Rocky Gravel 2", ""),
    ("17", "Concrete 3", ""),
    ("18", "Bunker Floor", ""),
    ("22", "Concrete 4", ""),
    ("23", "Car", ""),
    ("24", "Flowers", "")
]

def setColourByCollisionType(obj):
    opacity = 1.0
    collisionType = int(obj.collisionType)
    if collisionType == 127:
        obj.color = [0.0, 1.0, 0.0, opacity]
    elif collisionType == 88:
        obj.color = [0.0, 0.5, 1.0, opacity]
    elif collisionType == 3:
        obj.color = [1.0, 0.5, 0.0, opacity]
    elif collisionType == 255:
        obj.color = [1.0, 0.0, 0.0, opacity]
    else:
        obj.color = [1.0, 0.45, 1.0, opacity]

def updateCollisionType(self, context):
    setColourByCollisionType(self)

def main(colFilePath):
    bpy.types.Object.collisionType = bpy.props.EnumProperty(name="Collision Type", items=collisionTypes, update=updateCollisionType)
    bpy.types.Object.slidable = bpy.props.BoolProperty(name="Slidable/Modifier")
    bpy.types.Object.surfaceType = bpy.props.EnumProperty(name="Surface Type", items=surfaceTypes)

    # Setup Viewport
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = "SOLID"
                        space.shading.color_type = "OBJECT"
                        space.shading.show_backface_culling = True

    colFile = open(colFilePath, "rb")
    print("Parsing Col file...", colFilePath)
    col = Col(colFile)
    colFile.close()

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
                print("[!] Collision mesh flagged with unknown collsionType:", mesh.collisionType)
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

    bpy.context.view_layer.active_layer_collection.children["COL"].children["col_colTreeNodes"].hide_viewport = True
    
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