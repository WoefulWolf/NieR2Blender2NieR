# Stolen and adapted from RaiderB https://github.com/ArthurHeitmann/NierDocs/blob/master/tools/datRepacker/datRepacker.py
from typing import List
from ...utils.ioUtils import write_uInt32, write_Int16
import zlib
import os

def crc32(text: str) -> int:
	return zlib.crc32(text.encode('ascii')) & 0xFFFFFFFF

def next_power_of_2_bits(x: int) -> int:  
    return 1 if x == 0 else (x - 1).bit_length()

class HashData:
    preHashShift: int
    bucketOffsets: List[int]
    hashes: List[int]
    fileIndices: List[int]

    def __init__(self, preHashShift: int):
        self.preHashShift = preHashShift
        self.bucketOffsets = []
        self.hashes = []
        self.fileIndices = []

    def getStructSize(self):
        return 4 + 2*len(self.bucketOffsets) + 4*len(self.hashes) + 4*len(self.fileIndices)

    def write(self, file):
        bucketsOffset = 4*4
        hashesOffset = bucketsOffset + len(self.bucketOffsets)*2
        fileIndicesOffset = hashesOffset + len(self.hashes)*4

        write_uInt32(file, self.preHashShift)
        write_uInt32(file, bucketsOffset)
        write_uInt32(file, hashesOffset)
        write_uInt32(file, fileIndicesOffset)

        for bucketOffset in self.bucketOffsets:
            write_Int16(file, bucketOffset)
        for hash in self.hashes:
            write_uInt32(file, hash)
        for fileIndex in self.fileIndices:
            write_Int16(file, fileIndex)

def generateHashData(files) -> bytes:
    preHashShift = min(31, 32 - next_power_of_2_bits(len(files)))
    bucketOffsetsSize = 1 << (31 - preHashShift)
    bucketOffsets = [-1] * bucketOffsetsSize
    hashes = [0] * len(files)
    fileIndices = list(range(len(files)))
    fileNames = [os.path.basename(i) for i in files.copy()]
    print(fileNames)

    # generate hashes
    for i in range(len(files)):
        fileName = os.path.basename(files[i])
        hash = crc32(fileName.lower())
        otherHash = (hash & 0x7FFFFFFF)
        hashes[i] = otherHash
    # sort by first half byte (x & 0x70000000)
    # sort indices & hashes at the same time
    hashes, fileIndices, fileNames = zip(*sorted(zip(hashes, fileIndices, fileNames), key=lambda x: x[0] & 0x70000000))
    # generate bucket list
    for i in range(len(files)):
        bucketOffsetsIndex = hashes[i] >> preHashShift
        if bucketOffsets[bucketOffsetsIndex] == -1:
            bucketOffsets[bucketOffsetsIndex] = i

    # print bucket offsets, hashes, fileIndeces
    print("bucketOffsets")
    for i in range(len(bucketOffsets)):
        print(f"{i}: {bucketOffsets[i]}")
    print("hashes")
    for i in range(len(hashes)):
        print(f"{i}: 0x{hashes[i]:08X}")
    print("fileIndices")
    for i in range(len(fileIndices)):
        print(f"{i}: {fileIndices[i]}")

    hashData = HashData(preHashShift)
    hashData.bucketOffsets = bucketOffsets
    hashData.hashes = hashes
    hashData.fileIndices = fileIndices
    return hashData