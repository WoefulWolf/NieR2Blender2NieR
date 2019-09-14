import bpy, bmesh, math

from blender2nier.vertexGroups.vertexGroup import c_vertexGroup

class c_vertexGroups(object):
    def __init__(self, offsetVertexGroups):
        self.offsetVertexGroups = offsetVertexGroups

        def get_vertexGroups(self, offsetVertexGroups):
            vertexGroupIndex = []

            for obj in bpy.data.objects:
                    if obj.type == 'MESH':
                        obj_name = obj.name.split('_')
                        obj_vertexGroupIndex = int(obj_name[-1])
                        if not obj_vertexGroupIndex in vertexGroupIndex:
                            vertexGroupIndex.append(obj_vertexGroupIndex)
            
            vertexGroups = []
            for index in vertexGroupIndex:
                if len(vertexGroups) == 0:
                    vertexGroups.append(c_vertexGroup(index, offsetVertexGroups))
                else:
                    vertexGroups.append(c_vertexGroup(index, vertexGroups[index-1].vertexGroupStart + vertexGroups[index-1].vertexGroupSize))

            return vertexGroups

        self.vertexGroups = get_vertexGroups(self, self.offsetVertexGroups)

        def get_vertexGroupsSize(self, vertexGroups):
            vertexGroupsSize = 0

            for vertexGroup in vertexGroups:
                vertexGroupsSize += vertexGroup.vertexGroupSize
            return vertexGroupsSize

        self.vertexGroups_StructSize = get_vertexGroupsSize(self, self.vertexGroups)