import bpy, bmesh, math

class c_mesh(object):
    def __init__(self, offsetMeshes, obj, bones):

        def get_BoundingBox(self, obj,):
            x = obj.dimensions[0]
            y = obj.dimensions[1]
            z = obj.dimensions[2]
            u = x/2
            v = y/2
            m = z/2
            return [x, y, z, u, v, m]

        def get_materials(self, obj):
            materials = []
            for indx, slot in enumerate(obj.material_slots):
                material = slot.material
                materials.append(indx)
            return materials

        self.nameOffset = offsetMeshes + 88

        self.boundingBox = get_BoundingBox(self, obj)

        self.offsetMaterials = self.nameOffset + len(obj.name) + 1

        self.numMaterials = len(get_materials(self, obj))

        self.offsetBones = self.offsetMaterials + 2*self.numMaterials

        self.numBones = len(bones.bones)

        self.name = obj.name[:-4]

        self.materials =  get_materials(self, obj)

        self.bones = 0                                  # TODO LATER IM LAZY

        def get_mesh_StructSize(self):
            mesh_StructSize = 0
            mesh_StructSize += 4 + 24 + 4 + 4 + 4 + 4
            mesh_StructSize += len(self.name) + 1
            mesh_StructSize += len(self.materials) * 2
            mesh_StructSize += 2
            return mesh_StructSize

        self.mesh_StructSize = get_mesh_StructSize(self)