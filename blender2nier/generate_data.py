from blender2nier.bones.bones import *
from blender2nier.boneIndexTranslateTable.boneIndexTranslateTable import *
from blender2nier.vertexGroups.create_vertexGroups import *
from blender2nier.batches.create_batches import *

class c_generate_data(object):
    headerSize = 136 + 8

    bones = c_bones()
    bones_Size = bones.bones_StructSize

    boneIndexTranslateTable = c_boneIndexTranslateTable(bones)

    vertexGroups = c_vertexGroups(headerSize + bones_Size)

    batches = c_batches()