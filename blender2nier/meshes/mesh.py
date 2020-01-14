import bpy, bmesh, math

class c_mesh(object):
    def __init__(self, offsetMeshes, numMeshes, obj):

        def get_BoundingBox(self, obj):
            x = obj.dimensions[0]
            y = obj.dimensions[1]/2
            z = obj.dimensions[2]/2
            u = x/2
            v = y
            w = z
            return [x, y, z, u, v, w]

        def get_materials(self, obj):
            materials = []
            obj_mesh_name = obj.name.split('-')[1]
            for mesh in bpy.data.objects:
                if mesh.type == 'MESH' and mesh.name.split('-')[1] == obj_mesh_name:
                    for slot in mesh.material_slots:
                        material = slot.material
                        for indx, mat in enumerate(bpy.data.materials):
                            if mat == material:
                                matID = indx
                                if matID not in materials:
                                    materials.append(matID)
                                    
            materials.sort()
            return materials

        def get_bones(self, obj):
            bones = []
            obj_mesh_name = obj.name.split('-')[1]
            for mesh in bpy.data.objects:
                if mesh.type == 'MESH' and mesh.name.split('-')[1] == obj_mesh_name:
                    for vertexGroup in mesh.vertex_groups:
                        boneName = vertexGroup.name.replace('bone', '')
                        if int(boneName) not in bones:
                            bones.append(int(boneName))
            if len(bones) == 0:
                bones.append(0)

            bones.sort()
            return bones
      
        self.bones = get_bones(self, obj)

        self.nameOffset = offsetMeshes + numMeshes * 44

        self.boundingBox = get_BoundingBox(self, obj)

        self.name = obj.name.split('-')[1]

        self.offsetMaterials = self.nameOffset + len(self.name) + 1

        self.materials =  get_materials(self, obj)

        self.numMaterials = len(self.materials)

        self.offsetBones = self.offsetMaterials + 2*self.numMaterials

        self.numBones = len(self.bones)     

        def get_mesh_StructSize(self):
            mesh_StructSize = 0
            mesh_StructSize += 4 + 24 + 4 + 4 + 4 + 4
            mesh_StructSize += len(self.name) + 1
            mesh_StructSize += len(self.materials) * 2
            mesh_StructSize += len(self.bones) * 2
            return mesh_StructSize

        self.mesh_StructSize = get_mesh_StructSize(self)

        self.blenderObj = obj