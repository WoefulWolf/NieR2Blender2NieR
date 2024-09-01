# Stolen and adapted from RaiderB https://github.com/ArthurHeitmann/NierDocs/blob/master/tools/datRepacker/datRepacker.py
# Also inspired by https://github.com/xxk-i/DATrepacker/blob/master/dat.py
from typing import List
from ...utils.ioUtils import write_uInt32, write_Int16
import zlib
import os

def crc32(text: str) -> int:
	return zlib.crc32(text.encode('ascii')) & 0xFFFFFFFF

class HashData:
    inFiles: List[str]
    preHashShift: int
    bucketOffsets: List[int]
    hashes: List[int]
    fileIndices: List[int]

    def __init__(self, inFiles: List[str]):
        self.inFiles = inFiles
        self.preHashShift = 0
        self.bucketOffsets = []
        self.hashes = []
        self.fileIndices = []

        self.generateHashData()

    def getStructSize(self):
        return 16 + 2*len(self.bucketOffsets) + 4*len(self.hashes) + 2*len(self.fileIndices)

    def write(self, file):
        bucketsSize = len(self.bucketOffsets) * 2
        hashesSize = len(self.hashes) * 4

        write_uInt32(file, self.preHashShift)
        write_uInt32(file, 16)
        write_uInt32(file, 16 + bucketsSize)
        write_uInt32(file, 16 + bucketsSize + hashesSize)

        for bucketOffset in self.bucketOffsets:
            write_Int16(file, bucketOffset)
        for hash in self.hashes:
            write_uInt32(file, hash)
        for fileIndex in self.fileIndices:
            write_Int16(file, fileIndex)

    def calculateShift(self, fileNumber: int) -> int:
        for i in range(31):
            if 1 << i >= fileNumber:
                return 31 - i
        return 0

    def generateHashData(self):
        self.preHashShift = self.calculateShift(len(self.inFiles))
        bucketOffsetsSize = 1 << (31 - self.preHashShift)
        self.bucketOffsets = [-1] * bucketOffsetsSize
        fileNames = [os.path.basename(file) for file in self.inFiles]

        nameIndicesHashes = [
            [fileNames[i], i, (crc32(fileNames[i].lower()) & 0x7fffffff)]
            for i in range(len(self.inFiles))
        ]

        nameIndicesHashes.sort(key=lambda x: x[2] >> self.preHashShift)

        self.hashes = [x[2] for x in nameIndicesHashes]
        self.hashes.sort(key=lambda x: x >> self.preHashShift)

        for i in range(len(nameIndicesHashes)):
            if self.bucketOffsets[nameIndicesHashes[i][2] >> self.preHashShift] == -1:
                self.bucketOffsets[nameIndicesHashes[i][2] >> self.preHashShift] = i
            self.fileIndices.append(nameIndicesHashes[i][1])
