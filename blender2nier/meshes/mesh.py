import bpy, bmesh, math

class c_mesh(object):
    def __init__(self, offsetMeshes, numMeshes, obj):

        def get_BoundingBox(self, obj,):
            x = obj.dimensions[0]
            y = obj.dimensions[1]/2
            z = obj.dimensions[2]/2
            u = x/2
            v = y
            w = z
            return [x, y, z, u, v, w]

        def get_materials(self, obj):
            materials = []
            for slot in obj.material_slots:
                material = slot.material
                for indx, mat in enumerate(bpy.data.materials):
                    if mat == material:
                        materials.append(indx)
                        return materials

        def get_bones(self, obj):
            bones = []
            for vertexGroup in obj.vertex_groups:
                boneName = vertexGroup.name
                bones.append(int(boneName[-1]))
            if len(bones) == 0:
                bones.append(0)
            return bones
      
        self.bones = get_bones(self, obj)

        self.nameOffset = offsetMeshes + numMeshes * 44

        self.boundingBox = get_BoundingBox(self, obj)

        self.name = obj.name.split('-')[1]

        self.offsetMaterials = self.nameOffset + len(self.name) + 1

        self.numMaterials = len(get_materials(self, obj))

        self.offsetBones = self.offsetMaterials + 2*self.numMaterials

        self.numBones = len(self.bones)

        self.materials =  get_materials(self, obj)     

        def get_mesh_StructSize(self):
            mesh_StructSize = 0
            mesh_StructSize += 4 + 24 + 4 + 4 + 4 + 4
            mesh_StructSize += len(self.name) + 1
            mesh_StructSize += len(self.materials) * 2
            mesh_StructSize += len(self.bones) * 2
            return mesh_StructSize

        self.mesh_StructSize = get_mesh_StructSize(self)