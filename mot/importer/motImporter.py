import bpy

from .animationData import PropertyAnimation, PropertyObjectAnimation
from ..common.mot import *
from ..common.motUtils import *
from .rotationWrapperObj import objRotationWrapper
from .tPoseFixer import fixTPose

def importMot(file: str, printProgress: bool = True) -> None:
	mot = MotFile()
	with open(file, "rb") as f:
		mot.fromFile(f)
	header = mot.header
	records = mot.records
	
	if hasArmatureAnimation(records):
		importArmatureMot(mot, printProgress)
	if hasCameraAnimation(records):
		importCameraMot(mot, printProgress)
	
	# updated frame range
	bpy.context.scene.frame_start = 0
	bpy.context.scene.frame_end = header.frameCount - 1
	bpy.context.scene.render.fps = 60
	
	print(f"Imported {header.animationName}")

def importArmatureMot(mot: MotFile, printProgress: bool = True) -> None:
	# import mot file
	header = mot.header
	records = mot.records
	
	# ensure that armature is in correct T-Pose
	armatureObj = getArmatureObject()
	fixTPose(armatureObj)
	for obj in [*armatureObj.pose.bones, armatureObj]:
		obj.location = (0, 0, 0)
		obj.rotation_mode = "XYZ"
		obj.rotation_euler = (0, 0, 0)
		obj.scale = (1, 1, 1)
	
	# 90 degree rotation wrapper, to adjust for Y-up
	objRotationWrapper(armatureObj)

	# new animation action
	if header.animationName in bpy.data.actions:
		bpy.data.actions.remove(bpy.data.actions[header.animationName])
	action = bpy.data.actions.new(header.animationName)
	if not armatureObj.animation_data:
		armatureObj.animation_data_create()
	armatureObj.animation_data.action = action
	action["headerFlag"] = header.flag
	action["headerUnknown"] = header.unknown
	
	# create keyframes
	motRecords: List[MotRecord] = []
	for record in records:
		if not record.getBone() and record.boneIndex != -1:
			print(f"WARNING: Bone {record.boneIndex} not found in armature")
			continue
		motRecords.append(record)

	animations: List[PropertyAnimation] = []
	for record in motRecords:
		animations.append(PropertyAnimation.fromRecord(record))
	
	# apply to blender
	for i, animation in enumerate(animations):
		if printProgress and i % 10 == 0:
			print(f"Importing {i+1}/{len(animations)}")
		animation.applyToBlender()

def importCameraMot(mot: MotFile, printProgress: bool = True):
	# Steps:
	# 1. Find or create camera
	# 2. Find or create camera target
	# 3. Create camera animation
	# 4. Create camera target animation
	# 5. Load .mot file
	
	# import mot file
	header = mot.header
	records = mot.records

	# set up camera and target
	target = getCameraTarget(True)
	cam = getCameraObject(True)
	objRotationWrapper(cam)
	objRotationWrapper(target)

	# new animation actions
	camAnimationName = f"{header.animationName} - Camera"
	targetAnimationName = f"{header.animationName} - Target"
	if camAnimationName in bpy.data.actions:
		bpy.data.actions.remove(bpy.data.actions[camAnimationName])
	if targetAnimationName in bpy.data.actions:
		bpy.data.actions.remove(bpy.data.actions[targetAnimationName])
	camAction = bpy.data.actions.new(camAnimationName)
	targetAction = bpy.data.actions.new(targetAnimationName)
	if not cam.animation_data:
		cam.animation_data_create()
	if not target.animation_data:
		target.animation_data_create()
	cam.animation_data.action = camAction
	target.animation_data.action = targetAction
	camAction["headerFlag"] = header.flag
	camAction["headerUnknown"] = header.unknown
	targetAction["headerFlag"] = header.flag
	targetAction["headerUnknown"] = header.unknown

	# create keyframes
	motRecords: List[MotRecord] = []
	for record in records:
		if record.boneIndex not in { cameraId, camTargetId }:
			print(f"WARNING: ID {record.boneIndex} doesn't match camera or target")
			continue
		motRecords.append(record)

	camAnimations: List[PropertyObjectAnimation] = []
	targetAnimations: List[PropertyObjectAnimation] = []
	for record in motRecords:
		if record.boneIndex == cameraId:
			camAnimations.append(PropertyObjectAnimation.fromRecord(record, cam))
		elif record.boneIndex == camTargetId:
			targetAnimations.append(PropertyObjectAnimation.fromRecord(record, target))
	
	# apply to blender
	for i, animation in enumerate(camAnimations):
		print(f"Importing {i+1}/{len(camAnimations)}")
		animation.applyToBlender()
	for i, animation in enumerate(targetAnimations):
		print(f"Importing {i+1}/{len(targetAnimations)}")
		animation.applyToBlender()

def hasArmatureAnimation(records: list[MotRecord]) -> bool:
	for record in records:
		if record.boneIndex not in { cameraId, camTargetId }:
			return True
	return False

def hasCameraAnimation(records: list[MotRecord]) -> bool:
	for record in records:
		if record.boneIndex in { cameraId, camTargetId }:
			return True
	return False
