from .util import *

# Based on binary template by NSA Cloud

class Header:
    def __init__(self, layFile):
        self.id = layFile.read(4)
        self.unknownVer = to_float(layFile.read(4))

        self.modelListOffset = to_uint(layFile.read(4))
        self.modelListCount = to_uint(layFile.read(4))

        self.assetsOffset = to_uint(layFile.read(4))
        self.assetsCount = to_uint(layFile.read(4))

        self.instancesOffset = to_uint(layFile.read(4))
        self.instancesCount = to_uint(layFile.read(4))

class ModelEntry:
    def __init__(self, layFile):
        self.dir = layFile.read(2)
        self.id = layFile.read(2)

class Asset:
    def __init__(self, layFile):
        self.name = to_string(layFile.read(32))

        self.position = [to_float(layFile.read(4)) for val in range(3)]
        self.rotation = [to_float(layFile.read(4)) for val in range(3)]
        self.scale = [to_float(layFile.read(4)) for val in range(3)]

        self.null0 = to_uint(layFile.read(4))
        self.unknownIndex = to_uint(layFile.read(4))
        self.null1 = [to_uint(layFile.read(1)) for val in range(32)]

        self.instanceCount = to_uint(layFile.read(4))

        self.instances = []

class Instance:
    def __init__(self, layFile):
        self.position = [to_float(layFile.read(4)) for val in range(3)]
        self.rotation = [to_float(layFile.read(4)) for val in range(3)]
        self.scale = [to_float(layFile.read(4)) for val in range(3)]

class Lay:
    def __init__(self, layFile):
        self.header = Header(layFile)

        layFile.seek(self.header.modelListOffset)
        self.modelList = []
        for i in range(self.header.modelListCount):
            self.modelList.append(ModelEntry(layFile))

        layFile.seek(self.header.assetsOffset)
        self.assets = []
        for i in range(self.header.assetsCount):
            self.assets.append(Asset(layFile))

        layFile.seek(self.header.instancesOffset)
        self.instances = []
        for i in range(self.header.instancesCount):
            self.instances.append(Instance(layFile))

        currentInstanceIndx = 0
        for asset in self.assets:
            for i in range(asset.instanceCount):
                asset.instances.append(self.instances[currentInstanceIndx])
                currentInstanceIndx = currentInstanceIndx + 1