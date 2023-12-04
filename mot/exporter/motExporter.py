import bpy
from mathutils import Vector
import re
import os
from typing import Callable, List
from ..common.motUtils import KeyFrame, Spline, focalLengthToFov, getArmatureObject, getCameraObject, getCameraTarget, cameraId, camTargetId
from ..common.mot import MotFile, MotHeader, MotRecord, MotInterpolValues, MotInterpolSplines

class AnimationObject:
	curve: bpy.types.FCurve
	property: str
	channel: int
	bone: bpy.types.PoseBone|None
	object: bpy.types.Object|None
	keyFrames: List[KeyFrame]
	valueOffset: float

def getAllAnimationObjects(obj: bpy.types.Object) -> List[AnimationObject]:
	curves = list(obj.animation_data.action.fcurves)
	if obj.type == "CAMERA":
		curves.extend(obj.data.animation_data.action.fcurves)
	animObjs: List[AnimationObject] = []
	for curve in curves:
		animObj = AnimationObject()
		animObj.curve = curve
		dataPath = curve.data_path
		if dataPath.startswith("pose.bones["):
			boneName = re.search(r"pose\.bones\[\"(.*)\"\]", dataPath).group(1)
			bone = obj.pose.bones[boneName]
			animObj.bone = bone
			animObj.object = None
		else:
			animObj.bone = None
			animObj.object = obj
		animObj.channel = curve.array_index
		if "location" in dataPath:
			animObj.property = "location"
		elif "rotation_euler" in dataPath:
			animObj.property = "rotation"
		elif "scale" in dataPath:
			animObj.property = "scale"
		elif "lens" in dataPath:
			animObj.property = "lens"
		elif "[\"unknown_14\"]" == dataPath:
			animObj.property = "unknown_14"
		elif "rotation_quaternion" in dataPath:
			raise Exception("Quaternion rotation not supported. Use euler rotation instead and delete the quaternion rotation fcurves")
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

def makeConstInterpolation(animObj: AnimationObject, record: MotRecord, transformValue: Callable[[float], float]):
	value = animObj.curve.keyframe_points[0].co[1]
	value += animObj.valueOffset
	record.value = transformValue(value)
	record.interpolation = None
	record.interpolationsCount = 0

def makeBakedInterpolation(animObj: AnimationObject, record: MotRecord, transformValue: Callable[[float], float]):
	values = [
		keyFrame.co[1] + animObj.valueOffset
		for keyFrame in animObj.curve.keyframe_points
	]
	values = list(map(transformValue, values))
	interpolation = MotInterpolValues()
	interpolation.values = values
	record.interpolation = interpolation
	record.interpolationsCount = len(values)

def makeBezierInterpolation(animObj: AnimationObject, record: MotRecord, transformValue: Callable[[float], float]):
	interpolation = MotInterpolSplines()
	interpolation.splines = []
	for i in range(len(animObj.curve.keyframe_points)):
		keyFrame = animObj.curve.keyframe_points[i]
		spline = Spline()
		spline.frame = round(keyFrame.co[0])
		spline.value = transformValue(keyFrame.co[1] + animObj.valueOffset)
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

def makeRecords(
	animObjs: List[AnimationObject],
	specialBoneIndex: int|None,
) -> List[MotRecord]:
	records: List[MotRecord] = []
	for animObj in animObjs:
		record = MotRecord()
		transformValue = lambda value: value
		if specialBoneIndex is None:
			record.boneIndex = animObj.bone.bone["ID"] if animObj.bone else -1
		else:
			record.boneIndex = specialBoneIndex
		if animObj.property == "location":
			record.propertyIndex = animObj.channel
		elif animObj.property == "rotation":
			record.propertyIndex = animObj.channel + 3
		elif animObj.property == "scale":
			record.propertyIndex = animObj.channel + 7
		elif animObj.property == "lens":
			record.propertyIndex = 15
			transformValue = lambda value: focalLengthToFov(animObj.object.data, value)
		elif animObj.property == "unknown_14":
			record.propertyIndex = 14
		else:
			raise Exception("Unknown property: " + animObj.property)
		record.unknown = 0
		record.interpolationType = getInterpolationType(animObj.curve)
		if record.interpolationType == 0:
			makeConstInterpolation(animObj, record, transformValue)
		elif record.interpolationType == 1:
			makeBakedInterpolation(animObj, record, transformValue)
		elif record.interpolationType == 4:
			makeBezierInterpolation(animObj, record, transformValue)
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
	cam = getCameraObject(False)
	target = getCameraTarget(False)
	if arm is None and cam is None and target is None:
		raise Exception("No armature or camera found")
	
	mot = MotFile()
	mot.header = MotHeader()
	mot.records = []
	mot.header.fillDefaults()
	mot.header.frameCount = bpy.context.scene.frame_end + 1
	mot.header.recordsOffset = 44

	# if patching, inject records of missing bones
	if patchExisting:
		addAdditionPatchRecords(path, mot.records)

	if arm is not None:
		appendObjAnimations(path, arm, mot)
	if cam is not None:
		appendObjAnimations(path, cam, mot, cameraId)
	if target is not None:
		appendObjAnimations(path, target, mot, camTargetId)
	
	# determine interpolation offsets relative to record position
	offset = mot.header.recordsOffset + (len(mot.records) + 1) * 12
	for i, record in enumerate(mot.records):
		if record.interpolation is None:
			continue
		curRecordOffset = mot.header.recordsOffset + i * 12
		record.interpolationsOffset = offset - curRecordOffset 
		offset += record.interpolation.size()
	
	with open(path, "wb") as f:
		mot.writeToFile(f)

	print("Done ;)")

def appendObjAnimations(
	path: str,
	obj: bpy.types.Object,
	mot: MotFile,
	specialBoneIndex: int|None = None,
):
	# get animation data
	animObjs = getAllAnimationObjects(obj)
	records = makeRecords(animObjs, specialBoneIndex)
	mot.records.extend(records)
	
	# update header
	header = mot.header
	action = obj.animation_data.action
	if "headerFlag" in action:
		header.flag = action["headerFlag"]
	if "headerUnknown" in action:
		header.unknown = action["headerUnknown"]
	if not header.animationName:
		animationName = action.name.split(" - ")[0]
		fileName = os.path.basename(os.path.splitext(path)[0])
		if animationName != fileName:
			print(f"Warning: Animation name '{animationName}' does not match file name '{fileName}'")
			print(f"Using animation name '{animationName}'")
		header.animationName = animationName
	header.recordsCount += len(records)
