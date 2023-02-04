import bpy

from .animationData import PropertyAnimation
from ..common.mot import *
from ..common.motUtils import *
from .rotationWrapperObj import objRotationWrapper
from .tPoseFixer import fixTPose

def importMot(file: str, printProgress: bool = True) -> None:
	# import mot file
	mot = MotFile()
	with open(file, "rb") as f:
		mot.fromFile(f)
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
	record: MotRecord
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
	
	# updated frame range
	bpy.context.scene.frame_start = 0
	bpy.context.scene.frame_end = header.frameCount - 1
	bpy.context.scene.render.fps = 60
	
	print(f"Imported {header.animationName} from {file}")
