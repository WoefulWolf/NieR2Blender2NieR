from ....utils.util import *

def create_wmb_colTreeNodes(wmb_file, data):
    wmb_file.seek(data.colTreeNodes_Offset)

    for colTreeNode in data.colTreeNodes.colTreeNodes:                # [p1, p2, left, right]
        for entry in colTreeNode[0]:                                  # p1
            write_float(wmb_file, entry)
        for entry in colTreeNode[1]:                                  # p2
            write_float(wmb_file, entry)
        write_Int32(wmb_file, colTreeNode[2])                              # left
        write_Int32(wmb_file, colTreeNode[3])                              # right