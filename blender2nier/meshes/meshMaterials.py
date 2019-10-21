import bpy, bmesh, math

class c_meshMaterials(object):
    def __init__(self, meshes):
        def get_meshMaterials(self):
            meshMaterials = []
            for indx, mesh in enumerate(meshes.meshes):
                meshID = indx
                materialID = mesh.materials[0]                  
                meshMaterial = [meshID, materialID]

                meshMaterials.append(meshMaterial)
            return meshMaterials

        self.meshMaterials = get_meshMaterials(self)
        self.meshMaterials_StructSize = len(self.meshMaterials) * 8
        