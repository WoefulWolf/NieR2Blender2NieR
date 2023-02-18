import bpy
from mathutils import Vector
import re
import os
from typing import List
from ..common.motUtils import KeyFrame, Spline, getArmatureObject
from ..common.mot import MotFile, MotHeader, MotRecord, MotInterpolValues, MotInterpolSplines

class AnimationObject:
	curve: bpy.types.FCurve
	property: str
	channel: int
	bone: bpy.types.PoseBone|None
	object: bpy.types.Object|None
	keyFrames: List[KeyFrame]
	valueOffset: float

def getAllAnimationObjects(arm: bpy.types.Object) -> List[AnimationObject]:
	curves = arm.animation_data.action.fcurves
	animObjs: List[AnimationObject] = []
	for curve in curves:
		animObj = AnimationObject()
		animObj.curve = curve
		dataPath = curve.data_path
		if dataPath.startswith("pose.bones["):
			boneName = re.search(r"pose\.bones\[\"(.*)\"\]", dataPath).group(1)
			bone = arm.pose.bones[boneName]
			animObj.bone = bone
			animObj.object = None
		else:
			animObj.bone = None
			animObj.object = arm
		animObj.channel = curve.array_index
		if "location" in dataPath:
			animObj.property = "location"
		elif "rotation_euler" in dataPath:
			animObj.property = "rotation"
		elif "scale" in dataPath:
			animObj.property = "scale"
		else:
			raise Exception("Unknown property: " + dataPath)
		if animObj.property == "location" and animObj.bone is not None:
			parentBonePos = animObj.bone.parent.bone.head_local[animObj.channel] if animObj.bone.parent else 0
			parentOffset = animObj.bone.bone.head_local[animObj.channel] - parentBonePos
			animObj.valueOffset = parentOffset
		else:
			animObj.valueOffset = 0
		animObj.keyFrames = []
		animObjs.append(animObj)

	return animObjs

def getInterpolationType(curve: bpy.types.FCurve) -> int:
	# single constant keyframe
	if len(curve.keyframe_points) == 1:
		return 0
	# baked animation; all keyframe 1 frame apart
	elif len(curve.keyframe_points) >= 2 and all(
		curve.keyframe_points[i].co[0] == curve.keyframe_points[i - 1].co[0] + 1
			and curve.keyframe_points[i].interpolation == "LINEAR"
		for i in range(1, len(curve.keyframe_points))
	):
		return 1
	# bezier interpolation
	elif len(curve.keyframe_points) >= 2 and all(
		curve.keyframe_points[i].interpolation == "BEZIER"
		for i in range(len(curve.keyframe_points))
	):
		return 4
	else:
		raise Exception(
			f"Unsupported interpolation type for curve {curve.data_path} {curve.array_index}\n" +
			"There are 3 supported interpolation types:\n" +
			"1. Single constant keyframe\n" +
			"2. Baked animation; all keyframe 1 frame apart (linear interpolation)\n" +
			"3. Bezier interpolation"
		)

def makeConstInterpolation(animObj: AnimationObject, record: MotRecord):
	value = animObj.curve.keyframe_points[0].co[1]
	value += animObj.valueOffset
	record.value = value
	record.interpolation = None
	record.interpolationsCount = 0

def makeBakedInterpolation(animObj: AnimationObject, record: MotRecord):
	values = [
		keyFrame.co[1] + animObj.valueOffset
		for keyFrame in animObj.curve.keyframe_points
	]
	interpolation = MotInterpolValues()
	interpolation.values = values
	record.interpolation = interpolation
	record.interpolationsCount = len(values)

def makeBezierInterpolation(animObj: AnimationObject, record: MotRecord):
	interpolation = MotInterpolSplines()
	interpolation.splines = []
	for i in range(len(animObj.curve.keyframe_points)):
		keyFrame = animObj.curve.keyframe_points[i]
		spline = Spline()
		spline.frame = round(keyFrame.co[0])
		spline.value = keyFrame.co[1] + animObj.valueOffset
		# in hermit slope
		if i == 0:
			spline.m0 = 0
		else:
			# get handles
			prevKeyFrame = animObj.curve.keyframe_points[i - 1]
			inHandle = Vector(keyFrame.handle_left)
			# normalize to x range 0-1
			xDist = keyFrame.co[0] - prevKeyFrame.co[0]
			inHandle -= keyFrame.co
			inHandle.x /= xDist
			# determine hermit vector
			rightVec = inHandle * 3
			# calculate slope
			rightSlope = rightVec.y / rightVec.x
			# set slope
			spline.m0 = rightSlope
		# out hermit slope
		if i == len(animObj.curve.keyframe_points) - 1:
			spline.m1 = 0
		else:
			# get handles
			nextKeyFrame = animObj.curve.keyframe_points[i + 1]
			outHandle = Vector(keyFrame.handle_right)
			# normalize to x range 0-1
			xDist = nextKeyFrame.co[0] - keyFrame.co[0]
			outHandle -= keyFrame.co
			outHandle.x /= xDist
			# determine hermit vector
			leftVec = outHandle * 3
			# calculate slope
			leftSlope = leftVec.y / leftVec.x
			# set slope
			spline.m1 = leftSlope
		interpolation.splines.append(spline)
	record.interpolation = interpolation
	record.interpolationsCount = len(interpolation.splines)

def makeRecords(animObjs: List[AnimationObject]) -> List[MotRecord]:
	records: List[MotRecord] = []
	for animObj in animObjs:
		record = MotRecord()
		record.boneIndex = animObj.bone.bone["ID"] if animObj.bone else -1
		if animObj.property == "location":
			record.propertyIndex = animObj.channel
		elif animObj.property == "rotation":
			record.propertyIndex = animObj.channel + 3
		elif animObj.property == "scale":
			record.propertyIndex = animObj.channel + 7
		else:
			raise Exception("Unknown property: " + animObj.property)
		record.unknown = 0
		record.interpolationType = getInterpolationType(animObj.curve)
		if record.interpolationType == 0:
			makeConstInterpolation(animObj, record)
		elif record.interpolationType == 1:
			makeBakedInterpolation(animObj, record)
		elif record.interpolationType == 4:
			makeBezierInterpolation(animObj, record)
		else:
			raise Exception("Unknown interpolation type: " + str(record.interpolationType))
		
		records.append(record)

	return records

def addAdditionPatchRecords(path: str, currentRecords: List[MotRecord]):
	with open(path, "rb") as f:
		mot = MotFile()
		mot.fromFile(f)
	
	arm = getArmatureObject()
	allCurrentBoneIds = set([
		bone.bone["ID"]
		for bone in arm.pose.bones
	])
	for record in currentRecords:
		allCurrentBoneIds.add(record.boneIndex)
	allFileBoneIds = set([
		record.boneIndex
		for record in mot.records
	])
	allMissingBoneIds = allFileBoneIds - allCurrentBoneIds
	missingRecords = [
		record
		for record in mot.records
		if record.boneIndex in allMissingBoneIds
	]
	print(f"Adding {len(missingRecords)} missing records for {len(allMissingBoneIds)} bones")
	currentRecords.extend(missingRecords)
	currentRecords.sort(key=lambda record: record.boneIndex * 10 + record.propertyIndex)


def exportMot(path: str, patchExisting: bool):
	arm = getArmatureObject()
	if arm is None:
		raise Exception("No armature found")
	
	# get animation data
	animObjs = getAllAnimationObjects(arm)
	records = makeRecords(animObjs)

	# if patching, inject records of missing bones
	if patchExisting:
		addAdditionPatchRecords(path, records)
	
	# make header
	header = MotHeader()
	header.fillDefaults()
	action = arm.animation_data.action
	if "headerFlag" in action:
		header.flag = action["headerFlag"]
	if "headerUnknown" in action:
		header.unknown = action["headerUnknown"]
	header.frameCount = bpy.context.scene.frame_end + 1
	animationName = action.name
	fileName = os.path.basename(os.path.splitext(path)[0])
	if animationName != fileName:
		print(f"Warning: Animation name '{animationName}' does not match file name '{fileName}'")
		print(f"Using animation name '{animationName}'")
	header.animationName = animationName
	header.recordsCount = len(records)
	header.recordsOffset = 44

	# determine interpolation offsets relative to record position
	offset = 44 + (len(records) + 1) * 12
	for i, record in enumerate(records):
		if record.interpolation is None:
			continue
		curRecordOffset = 44 + i * 12
		record.interpolationsOffset = offset - curRecordOffset 
		offset += record.interpolation.size()
	
	# write file
	file = MotFile()
	file.header = header
	file.records = records
	with open(path, "wb") as f:
		file.writeToFile(f)

	print("Done ;)")
