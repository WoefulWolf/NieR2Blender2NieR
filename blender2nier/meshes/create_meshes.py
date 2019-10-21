import bpy, bmesh, math
from blender2nier.meshes.mesh import *

class c_meshes(object):
    def __init__(self, offsetMeshes):

        def get_meshes(self, offsetMeshes):
            meshes = []
            meshes_names_added = []
            numMeshes = 0
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    if obj.name[:-4] not in meshes_names_added:
                        numMeshes += 1
                        meshes_names_added.append(obj.name[:-4])

            meshes_names_added = []
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    if obj.name[:-4] not in meshes_names_added:
                        mesh = c_mesh(offsetMeshes, numMeshes, obj)
                        meshes.append(mesh)
                        meshes_names_added.append(mesh.name)
                        offsetMeshes += len(mesh.name) + 1 + mesh.numMaterials * 2 + mesh.numBones * 2

            return meshes

        def get_meshes_StructSize(self, meshes):
            meshes_StructSize = 0
            for mesh in meshes:
                meshes_StructSize += mesh.mesh_StructSize
            return meshes_StructSize

        self.meshes = get_meshes(self, offsetMeshes)

        self.meshes_StructSize = get_meshes_StructSize(self, self.meshes)