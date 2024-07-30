import math
from typing import List, Dict

import bpy

from .col import Col, Batch
from ...utils.util import centre_origins, setViewportColorTypeToObject
from mathutils import Matrix


def main(colFilePath):
    # Setup Viewport
    setViewportColorTypeToObject()

    with open(colFilePath, "rb") as colFile:
        print("Parsing Col file...", colFilePath)
        col = Col(colFile)

    bpy.context.scene["exportColTree"] = len(col.colTreeNodes) > 0
    bpy.context.scene["exportColMeshMap"] = len(col.meshMaps) > 0

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

            if mesh.batchType == 2 and batch.boneIndex != -1 or mesh.batchType == 3:
                bindBones(obj, mesh.batchType, batch, col.boneMaps, col.boneMaps2)

            try:
                obj.collisionType = str(mesh.collisionType)
            except:
                print("[!] Collision mesh flagged with unknown collisionType:", mesh.collisionType)
                obj.collisionType = "-1"
                obj["UNKNOWN_collisionType"] = mesh.collisionType

            obj.colModifier = str(mesh.modifier)
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
    
    centre_origins("COL")
    print('Importing finished. ;)')
    return {'FINISHED'}

def bindBones(obj: bpy.types.Object, batchType: int, batch: Batch, boneMap: List[int], boneMap2: List[int]):
    armature: bpy.types.Armature = None
    if "WMB" in bpy.data.collections:
        for armObj in bpy.data.collections["WMB"].all_objects:
            if armObj.type == "ARMATURE":
                armature = armObj
                break
    if not armature:
        raise "No armature found in WMB collection"

    def getBoneI(boneId: int):
        if batchType == 2:
            boneIndex = boneMap[boneId]
        elif batchType == 3:
            boneIndex = boneMap2[boneId]
        else:
            raise "Unknown batchType"

        for bone in armature.data.bones:
            if int(bone["ID"]) == boneIndex:
                return int(bone.name[4:])
        raise "Bone not found"

    # parent obj to armature
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    obj.select_set(True)
    bpy.ops.object.parent_set(type="ARMATURE")
    armature.select_set(False)
    obj.select_set(False)

    # make vertex groups
    if batchType == 2:
        vertexGroup = obj.vertex_groups.new(name=f"bone{getBoneI(batch.boneIndex)}")
        for i in range(batch.vertexCount):
            vertexGroup.add([i], 1.0, "REPLACE")
    elif batchType == 3:
        vertexGroups: Dict[int: bpy.types.VertexGroup] = {}
        for vertI in range(batch.vertexCount):
            for i in range(4):
                if batch.bones[vertI][i] == 0 and batch.boneWeights[vertI][i] == 0.0:
                    continue
                if batch.bones[vertI][i] not in vertexGroups:
                    vertexGroups[batch.bones[vertI][i]] = obj.vertex_groups.new(name=f"bone{getBoneI(batch.bones[vertI][i])}")
                vertexGroups[batch.bones[vertI][i]].add([vertI], batch.boneWeights[vertI][i], "REPLACE")

    # move obj to bone location (first non 0 bone?)
    if batchType == 2:
        firstBone = batch.boneIndex
        bone = armature.pose.bones[f"bone{getBoneI(firstBone)}"]
        boneGlobalLoc = armature.matrix_world @ bone.matrix @ bone.location
        obj.location = boneGlobalLoc