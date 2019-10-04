import bpy, bmesh, math
from blender2nier.meshes.mesh import *

class c_meshes(object):
    def __init__(self, offsetMeshes, bones):

        def get_meshes(self, offsetMeshes, bones):
            meshes = []
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    mesh = c_mesh(offsetMeshes, obj, bones)
                    meshes.append(mesh)
                    offsetMeshes += len(mesh.name) + 1 + 4
            return meshes

        def get_meshes_StructSize(self, meshes):
            meshes_StructSize = 0
            for mesh in meshes:
                meshes_StructSize += mesh.mesh_StructSize
            return meshes_StructSize

        self.meshes = get_meshes(self, offsetMeshes, bones)

        self.meshes_StructSize = get_meshes_StructSize(self, self.meshes)