import bpy

class NameGroup:
    def __init__(self, name, startOffset):
        self.name = name
        self.startOffset = startOffset   

class NameGroups:
    def __init__(self, nameGroupsStartOffset):
        
        # Get all names to add
        names_to_add = []
        for obj in bpy.data.collections['COL'].objects:
            if obj.type == 'MESH':
                name = obj.name.split("-")[1]
                if name not in names_to_add:
                    names_to_add.append(name)

        # Create the namegroups and structSize
        self.structSize = len(names_to_add) * 4
        currentStartOffset = nameGroupsStartOffset + self.structSize
        self.nameGroups = []
        for name in names_to_add:
            self.nameGroups.append(NameGroup(name, currentStartOffset))
            currentStartOffset += len(name) + 1
            self.structSize += len(name) + 1

    def get_nameIndex(self, name):
        for idx, nameGroup in enumerate(self.nameGroups):
            if name == nameGroup.name:
                return idx

from ..util import *

def write_col_namegroups(col_file, data):
    col_file.seek(data.offsetNameGroups)

    for nameGroup in data.nameGroups.nameGroups:
        write_uInt32(col_file, nameGroup.startOffset)

    for nameGroup in data.nameGroups.nameGroups:
        print("[>]", nameGroup.name)
        write_string(col_file, nameGroup.name)