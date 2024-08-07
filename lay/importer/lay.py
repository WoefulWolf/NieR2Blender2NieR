from ...utils.ioUtils import to_string, read_float, read_uint32, read_uint8


# Based on binary template by NSA Cloud

class Header:
    def __init__(self, layFile):
        self.id = layFile.read(4)
        self.unknownVer = read_float(layFile)

        self.modelListOffset = read_uint32(layFile)
        self.modelListCount = read_uint32(layFile)

        self.assetsOffset = read_uint32(layFile)
        self.assetsCount = read_uint32(layFile)

        self.instancesOffset = read_uint32(layFile)
        self.instancesCount = read_uint32(layFile)

class ModelEntry:
    def __init__(self, layFile):
        self.dir = layFile.read(2)
        self.id = layFile.read(2)

class Asset:
    def __init__(self, layFile):
        self.name = to_string(layFile.read(32))

        self.position = [read_float(layFile) for val in range(3)]
        self.rotation = [read_float(layFile) for val in range(3)]
        self.scale = [read_float(layFile) for val in range(3)]

        self.null0 = read_uint32(layFile)
        self.unknownIndex = read_uint32(layFile)
        self.null1 = [read_uint8(layFile) for val in range(32)]

        self.instanceCount = read_uint32(layFile)

        self.instances = []

class Instance:
    def __init__(self, layFile):
        self.position = [read_float(layFile) for val in range(3)]
        self.rotation = [read_float(layFile) for val in range(3)]
        self.scale = [read_float(layFile) for val in range(3)]

class Lay:
    def __init__(self, layFile):
        self.header = Header(layFile)

        layFile.seek(self.header.modelListOffset)
        self.modelList: list[ModelEntry] = []
        for i in range(self.header.modelListCount):
            self.modelList.append(ModelEntry(layFile))

        layFile.seek(self.header.assetsOffset)
        self.assets: list[Asset] = []
        for i in range(self.header.assetsCount):
            self.assets.append(Asset(layFile))

        layFile.seek(self.header.instancesOffset)
        self.instances: list[Instance] = []
        for i in range(self.header.instancesCount):
            self.instances.append(Instance(layFile))

        currentInstanceIndex = 0
        for asset in self.assets:
            for i in range(asset.instanceCount):
                asset.instances.append(self.instances[currentInstanceIndex])
                currentInstanceIndex = currentInstanceIndex + 1