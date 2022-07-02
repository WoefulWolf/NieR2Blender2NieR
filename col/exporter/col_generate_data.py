from .col_boneMap import BoneMap, BoneMap2
from .col_colTreeNodes import ColTreeNodes
from .col_meshes import Meshes
from .col_namegroups import NameGroups


class COL_Data:
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

        # Bone maps
        self.boneMap = BoneMap()
        self.boneMap2 = BoneMap2()

        # Meshes
        print("[>] Generating meshes...")
        self.offsetMeshes = currentOffset
        self.meshes = Meshes(currentOffset, self.nameGroups, self.boneMap, self.boneMap2)
        self.meshCount = len(self.meshes.meshes)
        currentOffset += self.meshes.structSize

        # BoneMap offsets
        self.boneMapCount = len(self.boneMap.map)
        self.offsetBoneMap = currentOffset if self.boneMapCount > 0 else 0
        currentOffset += self.boneMap.structSize

        # BoneMap2 offsets
        self.boneMap2Count = len(self.boneMap2.map)
        self.offsetBoneMap2 = currentOffset if self.boneMap2Count > 0 else 0
        currentOffset += self.boneMap2.structSize

        # MeshMap
        self.offsetMeshMap = 0
        self.meshMapCount = 0

        # ColTreeNodes
        print("[>] Generating colTreeNodes...")
        self.offsetColTreeNodes = currentOffset
        self.colTreeNodes = ColTreeNodes(currentOffset, generateColTree)
        self.colTreeNodeCount = len(self.colTreeNodes.colTreeNodes)
        currentOffset += self.colTreeNodes.structSize