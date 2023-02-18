from __future__ import annotations
from typing import List
import bpy
from .motUtils import *
from ...utils.ioUtils import *
from io import BufferedReader

class MotFile:
	header: MotHeader
	records: List[MotRecord]

	def fromFile(self, file: BufferedReader):
		self.header = MotHeader()
		self.header.fromFile(file)
		self.records = [
			MotRecord().fromFile(file)
			for _ in range(self.header.recordsCount)
		]
	
	def writeToFile(self, file: BufferedReader):
		self.header.writeToFile(file)
		for record in self.records:
			record.writeToFile(file)
		trailingRecord = MotRecord()
		trailingRecord.makeTrailingRecord()
		trailingRecord.writeToFile(file)
		for record in self.records:
			if record.interpolation is None:
				continue
			record.interpolation.writeToFile(file)

class MotHeader:
	magic: int
	hash: int
	flag: int
	frameCount: int
	recordsOffset: int
	recordsCount: int
	unknown: int
	animationName: str

	def fromFile(self, file: BufferedReader):
		self.magic = read_uint32(file)
		self.hash = read_uint32(file)
		self.flag = read_uint16(file)
		self.frameCount = read_int16(file)
		self.recordsOffset = read_uint32(file)
		self.recordsCount = read_uint32(file)
		self.unknown = read_uint32(file)
		self.animationName = file.read(20).decode("utf-8").rstrip("\0")
	
	def fillDefaults(self):
		self.magic = 0x746F6D
		self.hash = 538051589
		self.flag = 0
		self.frameCount = 0
		self.recordsOffset = 0
		self.recordsCount = 0
		self.unknown = 0
		self.animationName = ""
	
	def writeToFile(self, file: BufferedReader):
		write_uInt32(file, self.magic)
		write_uInt32(file, self.hash)
		write_uInt16(file, self.flag)
		write_Int16(file, self.frameCount)
		write_uInt32(file, self.recordsOffset)
		write_uInt32(file, self.recordsCount)
		write_uInt32(file, self.unknown)
		animationName = self.animationName.encode("utf-8")
		animationName += b"\0" * (20 - len(animationName))
		file.write(animationName)

class MotRecord:
	boneIndex: int
	propertyIndex: int
	interpolationType: int
	interpolationsCount: int
	unknown: int
	value: float
	interpolationsOffset: int
	interpolation: MotInterpolation

	def fromFile(self, file: BufferedReader) -> MotRecord:
		self.boneIndex = read_int16(file)
		self.propertyIndex = read_int8(file)
		self.interpolationType = read_int8(file)
		self.interpolationsCount = read_int16(file)
		self.unknown = read_uint16(file)

		if self.interpolationType == 0:
			self.value = read_float(file)
		else:
			self.interpolationsOffset = read_uint32(file)

		self.interpolation = MotInterpolation.fromRecordAndFile(self, file)
		return self
	
	def makeTrailingRecord(self):
		self.boneIndex = 32767
		self.propertyIndex = 0
		self.interpolationType = 0
		self.interpolationsCount = 0
		self.unknown = 0
		self.value = 0
		self.interpolationsOffset = 0
		self.interpolation = None
	
	def writeToFile(self, file: BufferedReader):
		write_Int16(file, self.boneIndex)
		write_Int8(file, self.propertyIndex)
		write_Int8(file, self.interpolationType)
		write_Int16(file, self.interpolationsCount)
		write_uInt16(file, self.unknown)
		if self.interpolationType == 0:
			write_float(file, self.value)
		else:
			write_uInt32(file, self.interpolationsOffset)
	
	def getBone(self) -> bpy.types.PoseBone|None:
		rig = getArmatureObject()
		boneName: str = ""
		if self.boneIndex == -1:
			return None
		else:
			for bone in rig.data.bones:
				if bone["ID"] == self.boneIndex:
					boneName = bone.name
					break
		if not boneName:
			return None
		return rig.pose.bones.get(boneName)
	
	def getPropertyPath(self) -> str:
		if self.propertyIndex in {0, 1, 2}:
			return "location"
		elif self.propertyIndex in {3, 4, 5}:
			return "rotation_euler"
		elif self.propertyIndex in {7, 8, 9}:
			return "scale"
		else:
			raise Exception(f"Unknown property index: {self.propertyIndex}")
	
	def getPropertyIndex(self) -> int:
		if self.propertyIndex in {0, 3, 7}:
			return 0
		elif self.propertyIndex in {1, 4, 8}:
			return 1
		elif self.propertyIndex in {2, 5, 9}:
			return 2
		else:
			raise Exception(f"Unknown property index: {self.propertyIndex}")

class MotInterpolation:
	record: MotRecord
	
	def fromFile(self, file: BufferedReader):
		raise NotImplementedError()

	def toKeyFrames(self) -> List[KeyFrame]:
		raise NotImplementedError()
	
	def getKeyframeIndices(self) -> List[int]:
		raise NotImplementedError()
	
	def writeToFile(self, file: BufferedReader):
		raise NotImplementedError()
	
	def size(self) -> int:
		raise NotImplementedError()

	@staticmethod
	def applyInterpolationToKeyFrame(prev: KeyFrameCombo|None, cur: KeyFrameCombo):
		raise NotImplementedError()

	@staticmethod
	def fromRecordAndFile(record: MotRecord, file: BufferedReader) -> MotInterpolation:
		interpolation: MotInterpolation

		if record.interpolationType == 0 or record.interpolationType == -1:
			interpolation = MotInterpolConst()
		elif record.interpolationType == 1:
			interpolation = MotInterpolValues()
		elif record.interpolationType == 2:
			interpolation = MotInterpol2()
		elif record.interpolationType == 3:
			interpolation = MotInterpol3()
		elif record.interpolationType == 4:
			interpolation = MotInterpolSplines()
		elif record.interpolationType == 5:
			interpolation = MotInterpol5()
		elif record.interpolationType == 6:
			interpolation = MotInterpol6()
		elif record.interpolationType == 7:
			interpolation = MotInterpol7()
		elif record.interpolationType == 8:
			interpolation = MotInterpol8()
		else:
			raise Exception(f"Unknown interpolation flag: {record.interpolationType}")
		
		interpolation.record = record
		interpolation.fromFile(file)

		return interpolation

class MotInterpolConst(MotInterpolation):
	value: float

	def fromFile(self, file: BufferedReader):
		self.value = self.record.value
	
	def writeToFile(self, file: BufferedReader):
		pass

	def size(self) -> int:
		return 0
	
	def toKeyFrames(self) -> List[KeyFrame]:
		keyframe = KeyFrame()
		keyframe.interpolationType = "CONSTANT"
		keyframe.frame = 0
		keyframe.value = self.value
		keyframe.applyInterpolation = MotInterpolConst.applyInterpolationToKeyFrame
		return [keyframe]
	
	def getKeyframeIndices(self) -> List[int]:
		return [0]
	
	@staticmethod
	def applyInterpolationToKeyFrame(prev: KeyFrameCombo|None, cur: KeyFrameCombo):
		cur.blend.interpolation = "CONSTANT"

class MotInterpolValues(MotInterpolation):
	values: List[float]

	def fromFile(self, file: BufferedReader):
		pos = file.tell()
		file.seek(pos + self.record.interpolationsOffset - 12)

		self.values = []
		for _ in range(self.record.interpolationsCount):
			self.values.append(read_float(file))
		
		file.seek(pos)

	def writeToFile(self, file: BufferedReader):
		for value in self.values:
			write_float(file, value)

	def size(self) -> int:
		return len(self.values) * 4
		
	def toKeyFrames(self) -> List[KeyFrame]:
		keyframes = []
		for i, value in enumerate(self.values):
			keyframe = KeyFrame()
			keyframe.interpolationType = "LINEAR"
			keyframe.frame = i
			keyframe.value = value
			keyframes.append(keyframe)
			keyframe.applyInterpolation = MotInterpolValues.applyInterpolationToKeyFrame
		return keyframes
	
	def getKeyframeIndices(self) -> List[int]:
		return list(range(len(self.values)))
	
	@staticmethod
	def applyInterpolationToKeyFrame(prev: KeyFrameCombo|None, cur: KeyFrameCombo):
		cur.blend.interpolation = "LINEAR"
		
class MotInterpol2(MotInterpolValues):
	p: float
	dp: float
	valuesQuantized: List[int]

	def fromFile(self, file: BufferedReader):
		pos = file.tell()
		file.seek(pos + self.record.interpolationsOffset - 12)

		self.p = read_float(file)
		self.dp = read_float(file)
		self.valuesQuantized = [
			read_uint16(file)
			for _ in range(self.record.interpolationsCount)
		]
		self.values = [
			self.p + self.dp * quantized
			for quantized in self.valuesQuantized
		]

		file.seek(pos)
	
	def writeToFile(self, file: BufferedReader):
		write_float(file, self.p)
		write_float(file, self.dp)
		for quantized in self.valuesQuantized:
			write_uInt16(file, quantized)
		# align to 4 bytes
		byteSize = 8 + 2 * len(self.valuesQuantized)
		endAlign = alignTo4(byteSize) - byteSize
		for _ in range(endAlign):
			write_uInt8(file, 0)

	def size(self) -> int:
		return alignTo4(8 + 2 * len(self.valuesQuantized))
		
class MotInterpol3(MotInterpolValues):
	p: float
	dp: float
	valuesQuantized: List[int]

	def fromFile(self, file: BufferedReader):
		pos = file.tell()
		file.seek(pos + self.record.interpolationsOffset - 12)

		self.p = read_PgHalf(file)
		self.dp = read_PgHalf(file)
		self.valuesQuantized = [
			read_uint8(file)
			for _ in range(self.record.interpolationsCount)
		]
		self.values = [
			self.p + self.dp * quantized
			for quantized in self.valuesQuantized
		]

		file.seek(pos)
	
	def writeToFile(self, file: BufferedReader):
		write_PgHalf(file, self.p)
		write_PgHalf(file, self.dp)
		for quantized in self.valuesQuantized:
			write_uInt8(file, quantized)
		# align to 4 bytes
		byteSize = 4 + len(self.valuesQuantized)
		endAlign = alignTo4(byteSize) - byteSize
		for _ in range(endAlign):
			write_uInt8(file, 0)

	def size(self) -> int:
		return alignTo4(4 + len(self.valuesQuantized))
		
class MotInterpolSplines(MotInterpolation):
	splines: List[Spline]

	def fromFile(self, file: BufferedReader):
		pos = file.tell()
		file.seek(pos + self.record.interpolationsOffset - 12)

		self.splines = []
		for _ in range(self.record.interpolationsCount):
			spline = Spline()
			spline.frame = read_uint16(file)
			read_uint16(file)	# dummy
			spline.value = read_float(file)
			spline.m0 = read_float(file)
			spline.m1 = read_float(file)
			self.splines.append(spline)

		file.seek(pos)
	
	def writeToFile(self, file: BufferedReader):
		for spline in self.splines:
			write_uInt16(file, spline.frame)
			write_uInt16(file, 0)
			write_float(file, spline.value)
			write_float(file, spline.m0)
			write_float(file, spline.m1)

	def size(self) -> int:
		return len(self.splines) * 16
		
	def toKeyFrames(self) -> List[KeyFrame]:
		keyframes = []
		for spline in self.splines:
			keyframe = KeyFrame()
			keyframe.interpolationType = "BEZIER"
			keyframe.frame = spline.frame
			keyframe.value = spline.value
			keyframe.m0 = spline.m0
			keyframe.m1 = spline.m1
			keyframes.append(keyframe)
			keyframe.applyInterpolation = MotInterpolSplines.applyInterpolationToKeyFrame
		return keyframes

	def getKeyframeIndices(self) -> List[int]:
		return [spline.frame for spline in self.splines]
	
	@staticmethod
	def applyInterpolationToKeyFrame(prev: KeyFrameCombo|None, cur: KeyFrameCombo):
		if prev is None:
			return
		# hermit spline out/in slopes --> hermit spline out/in tangents
		m_prev = prev.mot.m1
		m_cur = cur.mot.m0
		hermit_prev = slopeToVec2D(m_prev)
		hermit_cur = slopeToVec2D(m_cur)
		# hermit spline out/in tangents --> bezier spline out/in tangents
		bezier_prev = hermitVecToBezierVec(hermit_prev)
		bezier_cur = hermitVecToBezierVec(hermit_cur) * -1
		# scale to frame distance
		xDist = cur.blend.co.x - prev.blend.co.x
		bezier_prev.x *= xDist
		bezier_cur.x *= xDist
		# offset point positions based on keyframe
		handle_prev_out = prev.blend.co + bezier_prev
		handle_cur_in = cur.blend.co + bezier_cur
		# set bezier handles
		cur.blend.interpolation = "BEZIER"
		prev.blend.handle_right_type = "FREE"
		cur.blend.handle_left_type = "FREE"
		prev.blend.handle_right = handle_prev_out
		cur.blend.handle_left = handle_cur_in

class MotInterpol5(MotInterpolSplines):
	p: float
	dp: float
	m0: float
	dm0: float
	m1: float
	dm1: float
	quantizedSplines: List[Spline]

	def fromFile(self, file: BufferedReader):
		pos = file.tell()
		file.seek(pos + self.record.interpolationsOffset - 12)

		self.p = read_float(file)
		self.dp = read_float(file)
		self.m0 = read_float(file)
		self.dm0 = read_float(file)
		self.m1 = read_float(file)
		self.dm1 = read_float(file)
		self.splines = []
		self.quantizedSplines = []
		for _ in range(self.record.interpolationsCount):
			spline = Spline()
			spline.frame = read_uint16(file)
			cp = read_uint16(file)
			cm0 = read_uint16(file)
			cm1 = read_uint16(file)
			spline.value = self.p + self.dp * cp
			spline.m0 = self.m0 + self.dm0 * cm0
			spline.m1 = self.m1 + self.dm1 * cm1
			self.splines.append(spline)
			self.quantizedSplines.append(Spline(spline.frame, cp, cm0, cm1))

		file.seek(pos)
	
	def writeToFile(self, file: BufferedReader):
		write_float(file, self.p)
		write_float(file, self.dp)
		write_float(file, self.m0)
		write_float(file, self.dm0)
		write_float(file, self.m1)
		write_float(file, self.dm1)
		for spline in self.quantizedSplines:
			write_uInt16(file, spline.frame)
			write_uInt16(file, spline.value)
			write_uInt16(file, spline.m0)
			write_uInt16(file, spline.m1)

	def size(self) -> int:
		return 6 * 4 + len(self.splines) * 8
		
class MotInterpol6(MotInterpolSplines):
	p: float
	dp: float
	m0: float
	dm0: float
	m1: float
	dm1: float
	quantizedSplines: List[Spline]

	def fromFile(self, file: BufferedReader):
		pos = file.tell()
		file.seek(pos + self.record.interpolationsOffset - 12)

		self.p = read_PgHalf(file)
		self.dp = read_PgHalf(file)
		self.m0 = read_PgHalf(file)
		self.dm0 = read_PgHalf(file)
		self.m1 = read_PgHalf(file)
		self.dm1 = read_PgHalf(file)
		self.splines = []
		self.quantizedSplines = []
		for _ in range(self.record.interpolationsCount):
			spline = Spline()
			spline.frame = read_uint8(file)
			cp = read_uint8(file)
			cm0 = read_uint8(file)
			cm1 = read_uint8(file)
			spline.value = self.p + self.dp * cp
			spline.m0 = self.m0 + self.dm0 * cm0
			spline.m1 = self.m1 + self.dm1 * cm1
			self.splines.append(spline)
			self.quantizedSplines.append(Spline(spline.frame, cp, cm0, cm1))
		
		file.seek(pos)
	
	def writeToFile(self, file: BufferedReader):
		write_PgHalf(file, self.p)
		write_PgHalf(file, self.dp)
		write_PgHalf(file, self.m0)
		write_PgHalf(file, self.dm0)
		write_PgHalf(file, self.m1)
		write_PgHalf(file, self.dm1)
		for spline in self.quantizedSplines:
			write_uInt8(file, spline.frame)
			write_uInt8(file, spline.value)
			write_uInt8(file, spline.m0)
			write_uInt8(file, spline.m1)

	def size(self) -> int:
		return 6 * 2 + len(self.splines) * 4
		
class MotInterpol7(MotInterpol6):
	def fromFile(self, file: BufferedReader):
		super().fromFile(file)

		absoluteFrame = 0
		for spline in self.splines:
			spline.frame += absoluteFrame
			absoluteFrame = spline.frame

class MotInterpol8(MotInterpolSplines):
	p: float
	dp: float
	m0: float
	dm0: float
	m1: float
	dm1: float
	quantizedSplines: List[Spline]

	def fromFile(self, file: BufferedReader):
		pos = file.tell()
		file.seek(pos + self.record.interpolationsOffset - 12)

		self.p = read_PgHalf(file)
		self.dp = read_PgHalf(file)
		self.m0 = read_PgHalf(file)
		self.dm0 = read_PgHalf(file)
		self.m1 = read_PgHalf(file)
		self.dm1 = read_PgHalf(file)
		self.splines = []
		self.quantizedSplines = []
		for _ in range(self.record.interpolationsCount):
			spline = Spline()
			spline.frame = readBe_uint16(file)
			cp = read_uint8(file)
			cm0 = read_uint8(file)
			cm1 = read_uint8(file)
			spline.value = self.p + self.dp * cp
			spline.m0 = self.m0 + self.dm0 * cm0
			spline.m1 = self.m1 + self.dm1 * cm1
			self.splines.append(spline)
			self.quantizedSplines.append(Spline(spline.frame, cp, cm0, cm1))

		file.seek(pos)
	
	def writeToFile(self, file: BufferedReader):
		write_PgHalf(file, self.p)
		write_PgHalf(file, self.dp)
		write_PgHalf(file, self.m0)
		write_PgHalf(file, self.dm0)
		write_PgHalf(file, self.m1)
		write_PgHalf(file, self.dm1)
		for spline in self.quantizedSplines:
			writeBe_uint16(file, spline.frame)
			write_uInt8(file, spline.value)
			write_uInt8(file, spline.m0)
			write_uInt8(file, spline.m1)
		byteSize = 12 + len(self.quantizedSplines) * 5
		endAlign = alignTo4(byteSize) - byteSize
		for _ in range(endAlign):
			write_uInt8(file, 0)

	def size(self) -> int:
		return alignTo4(6 * 2 + len(self.splines) * 5)
