from .col_colTreeNodes import ColTreeNodes
from .col_meshes import Meshes
from .col_namegroups import NameGroups


class COL_Data():
    def __init__(self, generateColTree):
        print("Generating Col Data...")
        currentOffset = 0

        # Header
        currentOffset += 56

        # Namegroups
        print("[>] Generating nameGroups...")
        self.offsetNameGroups = currentOffset
        self.nameGroups = NameGroups(currentOffset)
        self.nameGroupCount= len(self.nameGroups.nameGroups)
        currentOffset += self.nameGroups.structSize

        # Meshes
        print("[>] Generating meshes...")
        self.offsetMeshes = currentOffset
        self.meshes = Meshes(currentOffset, self.nameGroups)
        self.meshCount = len(self.meshes.meshes)
        currentOffset += self.meshes.structSize

        # BoneMap
        self.offsetBoneMap = 0
        self.boneMapCount = 0

        # BoneMap2
        self.offsetBoneMap2 = 0
        self.boneMap2Count = 0

        # MeshMap
        self.offsetMeshMap = 0
        self.meshMapCount = 0

        # ColTreeNodes
        print("[>] Generating colTreeNodes...")
        self.offsetColTreeNodes = currentOffset
        self.colTreeNodes = ColTreeNodes(currentOffset, generateColTree)
        self.colTreeNodeCount = len(self.colTreeNodes.colTreeNodes)
        currentOffset += self.colTreeNodes.structSize