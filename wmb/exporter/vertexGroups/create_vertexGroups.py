import bpy

from .vertexGroup import c_vertexGroup
from ....utils.util import getMeshVertexGroups, calculateVertexFlags


class c_vertexGroups(object):
    def __init__(self, offsetVertexGroups):
        self.offsetVertexGroups = offsetVertexGroups

        def get_vertexGroups(self, offsetVertexGroups):
            meshVertexGroups = getMeshVertexGroups("WMB")

            vertexesOffset = offsetVertexGroups + len(meshVertexGroups) * 48
            
            vertexGroups = []
            for index, vertexGroup in enumerate(meshVertexGroups):
                print('[+] Creating Vertex Group', index, 'with flag', calculateVertexFlags(vertexGroup[0]))
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