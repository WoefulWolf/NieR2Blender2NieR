import bpy

class c_unknownWorldData(object):
    def __init__(self):
        def get_unknownWorldData():
            unknownWorldData = []
            b_unknownWorldData = bpy.context.scene['unknownWorldData']
            for key in b_unknownWorldData:
                val = b_unknownWorldData[key]
                unknownWorldData.append([val[0], val[1], val[2], val[3], val[4], val[5]])
            return unknownWorldData

        def get_unknownWorldDataSize(unknownWorldData):
            unknownWorldDataSize = len(unknownWorldData) * 24
            return unknownWorldDataSize

        self.unknownWorldData = get_unknownWorldData()
        self.unknownWorldDataSize = get_unknownWorldDataSize(self.unknownWorldData)
        self.unknownWorldDataCount = len(self.unknownWorldData)