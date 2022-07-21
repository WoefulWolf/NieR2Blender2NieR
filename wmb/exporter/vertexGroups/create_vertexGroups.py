import bpy
from ....utils.util import timing

from .vertexGroup import c_vertexGroup


class c_vertexGroups(object):
    @timing(["main", "c_generate_data", "c_vertexGroup"])
    def __init__(self, offsetVertexGroups):
        self.offsetVertexGroups = offsetVertexGroups

        def get_vertexGroups(self, offsetVertexGroups):
            vertexGroupIndex = []

            for obj in bpy.data.collections['WMB'].all_objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('-')
                    obj_vertexGroupIndex = int(obj_name[-1])
                    if obj_vertexGroupIndex not in vertexGroupIndex:
                        vertexGroupIndex.append(obj_vertexGroupIndex)

            vertexGroupIndex.sort()

            vertexesOffset = offsetVertexGroups + len(vertexGroupIndex) * 48
            
            vertexGroups = []
            for index in vertexGroupIndex:
                print('[+] Creating Vertex Group', index)
                vertexGroups.append(c_vertexGroup(index, vertexesOffset))
                vertexesOffset += vertexGroups[index].vertexGroupSize
            return vertexGroups

        self.vertexGroups = get_vertexGroups(self, self.offsetVertexGroups)

        def get_vertexGroupsSize(self, vertexGroups):
            vertexGroupsSize = len(vertexGroups) * 48

            for vertexGroup in vertexGroups:
                vertexGroupsSize += vertexGroup.vertexGroupSize
            return vertexGroupsSize

        self.vertexGroups_StructSize = get_vertexGroupsSize(self, self.vertexGroups)