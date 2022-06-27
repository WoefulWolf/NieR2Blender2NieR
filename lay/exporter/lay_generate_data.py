from .lay_assets import Assets
from .lay_modelEntries import ModelEntries


class LAY_Data():
    def __init__(self):
        print("Generating Lay Data...")
        currentOffset = 0

        # Header
        currentOffset += 32

        # ModelEntries
        print("[>] Generating modelEntries...")
        self.offsetModelEntries = currentOffset
        self.modelEntries = ModelEntries()
        currentOffset += self.modelEntries.structSize

        # Assets
        print("[>] Generating assets and instances...")
        self.offsetAssets = currentOffset
        self.assets = Assets()
        currentOffset += self.assets.structSize

        # Instances are stores within asset objects
        self.offsetInstances = currentOffset
        self.instancesCount = self.assets.totalInstancesCount