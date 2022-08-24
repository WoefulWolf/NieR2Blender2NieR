from .mesh import *
from ....utils.util import allObjectsInCollectionInOrder

class c_meshes(object):
    def __init__(self, offsetMeshes):

        def get_meshes(self, offsetMeshes):
            meshes = []

            meshObjectNames = []
            for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                obj_name = obj.name.split('-')[1]
                meshObjectNames.append(obj_name)

            meshNames = [] 
            [meshNames.append(i) for i in meshObjectNames if i not in meshNames]
            numMeshes = len(meshNames)

            #sort mesh names by meshGroupIndex
            meshNamesSorted = [None] * numMeshes
            for meshName in meshNames:
                for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                    obj_name = obj.name.split('-')[1]
                    if obj_name == meshName:
                        meshNamesSorted[obj["meshGroupIndex"]] = meshName
                        break
            print("Meshes to generate:", meshNamesSorted)

            meshes_added = []
            for meshName in meshNamesSorted:
                for obj in (x for x in allObjectsInCollectionInOrder('WMB') if x.type == "MESH"):
                    obj_name = obj.name.split('-')[1]
                    if obj_name == meshName:
                        if obj_name not in meshes_added:
                            print('[+] Generating Mesh', meshName)
                            mesh = c_mesh(offsetMeshes, numMeshes, obj)
                            meshes.append(mesh)
                            meshes_added.append(obj_name)
                            offsetMeshes += len(mesh.name) + 1 + mesh.numMaterials * 2 + mesh.numBones * 2
                            break

            return meshes

        def get_meshes_StructSize(self, meshes):
            meshes_StructSize = 0
            for mesh in meshes:
                meshes_StructSize += mesh.mesh_StructSize
            return meshes_StructSize

        self.meshes = get_meshes(self, offsetMeshes)

        self.meshes_StructSize = get_meshes_StructSize(self, self.meshes)