import bpy

class c_colTreeNodes(object):
    def __init__(self):
        def get_colTreeNodes():
            colTreeNodes = []
            b_colTreeNodes = bpy.context.scene['colTreeNodes']
            for key in b_colTreeNodes:
                val = b_colTreeNodes[key]
                p1 = [val[0], val[1], val[2]]
                p2 = [val[3], val[4], val[5]]
                left = int(val[6])
                right = int(val[7])
                colTreeNodes.append([p1, p2, left, right])
            return colTreeNodes

        def get_colTreeNodesSize(colTreeNodes):
            colTreeNodesSize = len(colTreeNodes) * 32
            return colTreeNodesSize

        self.colTreeNodes = get_colTreeNodes()
        self.colTreeNodesSize = get_colTreeNodesSize(self.colTreeNodes)
        self.colTreeNodesCount = len(self.colTreeNodes)