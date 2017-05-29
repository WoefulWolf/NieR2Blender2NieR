import os
import sys
from nier2blender.util import *

class WTA(object):
	def __init__(self, wta_fp):
		super(WTA, self).__init__()
		self.magicNumber = wta_fp.read(4)
		if self.magicNumber == b'WTB\x00':
			self.unknown04 = to_int(wta_fp.read(4))
			self.textureCount = to_int(wta_fp.read(4))
			self.textureOffsetArrayOffset = to_int(wta_fp.read(4))
			self.textureSizeArrayOffset = to_int(wta_fp.read(4))
			self.unknownArrayOffset1 = to_int(wta_fp.read(4))
			self.textureIdentifierArrayOffset = to_int(wta_fp.read(4))
			self.unknownArrayOffset2 = to_int(wta_fp.read(4))
			self.wtaTextureOffset = [0] * self.textureCount
			self.wtaTextureSize = [0] * self.textureCount
			self.wtaTextureIdentifier = [0] * self.textureCount
			self.unknownArray1 = [0] * self.textureCount
			self.unknownArray2 = [] 
			for i in range(self.textureCount):
				wta_fp.seek(self.textureOffsetArrayOffset + i * 4)
				self.wtaTextureOffset[i] = to_int(wta_fp.read(4))
				wta_fp.seek(self.textureSizeArrayOffset + i * 4)
				self.wtaTextureSize[i] =  to_int(wta_fp.read(4)) 
				wta_fp.seek(self.textureIdentifierArrayOffset + i * 4)
				self.wtaTextureIdentifier[i] = "%08x"%to_int(wta_fp.read(4))
				wta_fp.seek(self.unknownArrayOffset1 + i * 4)
				self.unknownArray1[i] = "%08x"%to_int(wta_fp.read(4))
			wta_fp.seek(self.unknownArrayOffset2 )
			unknownval =  (wta_fp.read(4))
			while unknownval:
				self.unknownArray2.append(to_int(unknownval))
				unknownval =  (wta_fp.read(4))
			self.pointer2 = hex(wta_fp.tell())	
	def getTextureByIndex(self, texture_index, texture_fp):
		texture_fp.seek(self.wtaTextureOffset[texture_index])
		texture = texture_fp.read(self.wtaTextureSize[texture_index])
		return texture

	def getTextureByIdentifier(self, textureIdentifier, texture_fp):
		for index in range(self.textureCount):
			if self.wtaTextureIdentifier[index] == textureIdentifier:
				return self.getTextureByIndex(index,texture_fp)
		return False