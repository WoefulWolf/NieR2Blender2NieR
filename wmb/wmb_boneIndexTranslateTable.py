from ..util import *

def create_wmb_boneIndexTranslateTable(wmb_file, data):
    wmb_file.seek(data.boneIndexTranslateTable_Offset)

    for entry in data.boneIndexTranslateTable.firstLevel:    # firstLevel
        write_Int16(wmb_file, entry)

    for entry in data.boneIndexTranslateTable.secondLevel:   # secondLevel
        write_Int16(wmb_file, entry)

    for entry in data.boneIndexTranslateTable.thirdLevel:    # thirdLevel
        write_Int16(wmb_file, entry)