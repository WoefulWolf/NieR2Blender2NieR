from __future__ import annotations
import bpy
import re
from typing import List, Dict
from .motUtils import getArmatureObject

# there are some bones that should not be animated when animating pl000f

commonBoneIds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 2640, 2816, 2817, 2818, 3136, 4094, 4095]
differentBoneIds = [2560, 2561, 2576, 2577, 2592, 2593, 2608, 2609, 3102, 3103, 3104, 3105, 3106, 3107, 3232, 3233, 3234, 3235, 3236, 3237, 3238, 3239, 3240, 3241, 3242, 3243]
missingBoneIds = [2562, 2563, 2656, 2657, 3072, 3073, 3074, 3075, 3076, 3077, 3078, 3079, 3080, 3081, 3082, 3083, 3084, 3085, 3086, 3087, 3088, 3089, 3090, 3091, 3092, 3093, 3094, 3095, 3096, 3097, 3098, 3099, 3100, 3101, 3108, 3109, 3110, 3111, 3112, 3113, 3114, 3120, 3121, 3152, 3153, 3154, 3155, 3156, 3157, 3158, 3159, 3160, 3161, 3162, 3163, 3164, 3165, 3166, 3167, 3168, 3169, 3170, 3171, 3172, 3173, 3184, 3185, 3186, 3187, 3188, 3189, 3190, 3191, 3192, 3193, 3194, 3195, 3196, 3197, 3198, 3199, 3200, 3201, 3202, 3203, 3204, 3205, 3206, 3207, 3208, 3209, 3210, 3211, 3212, 3213, 3214, 3215, 3216, 3217, 3218, 3219, 3220, 3221, 3222, 3223, 3224, 3225, 3226, 3227, 3228, 3229, 3230, 3231, 3244, 3245, 3246, 3247, 3248, 3249, 3250, 3251, 3252, 3253, 3254, 3255, 3256, 3257, 3258, 3259, 3260, 3261, 3262, 3263, 3264, 3265, 3266, 3267, 3268, 3269, 3270, 3271, 3272, 3273, 3280, 3281, 3282, 3283, 3284, 3285, 3286, 3287, 3288, 3289, 3290]
invalidBoneIds = [*differentBoneIds, *missingBoneIds]

def isPl000f(path: str|None = None, animationName: str|None = None, armature: bpy.types.Object|None = None):
	if path is None and animationName is None and armature is None:
		return False
	if path is not None and "pl000f" in path:
		return True
	if animationName is not None and "pl000f" in animationName:
		return True
	if armature is not None and armature.animation_data is not None:
		action = armature.animation_data.action
		if action is not None and "pl000f" in action.name:
			return True
	return False

def getInvalidBoneIds(armature: bpy.types.Object):
	boneIds = []
	for bone in armature.pose.bones:
		boneId = bone.bone["ID"]
		if boneId in invalidBoneIds:
			boneIds.append(boneId)
	boneIds.sort()
	return boneIds

def makeBoneIndexToIdLookup(armature: bpy.types.Object) -> Dict[int, int]:
	boneIndexToId = {}
	bone: bpy.types.PoseBone
	for bone in armature.pose.bones:
		boneName = re.search(r"bone(\d+)", bone.name)
		if boneName is None:
			raise Exception(f"Invalid bone name: {bone.name}! No bone index found!")
		boneIndex = int(boneName.group(1))
		boneId = bone.bone["ID"]
		boneIndexToId[boneIndex] = boneId
	return boneIndexToId

def removeInvalidAnimations(armature: bpy.types.Object, boneIds: List[int], operator: bpy.types.Operator|None = None):
	boneIndexToId = makeBoneIndexToIdLookup(armature)
	removedAnimations = 0
	action: bpy.types.Action
	for action in bpy.data.actions:
		fCurve: bpy.types.FCurve
		for fCurve in action.fcurves:
			if not "pose.bones[" in fCurve.data_path:
				continue
			boneName = re.search(r"pose\.bones\[\"bone(\d+)\"\]", fCurve.data_path)
			if boneName is None:
				continue
			boneIndex = int(boneName.group(1))
			boneId = boneIndexToId[boneIndex]
			if boneId not in boneIds:
				continue
			action.fcurves.remove(fCurve)
			removedAnimations += 1
	print(f"Removed {removedAnimations} f curves")
	if operator is not None:
		operator.report({"INFO"}, f"Removed {removedAnimations} f curves")

def hideInvalidBones(armature: bpy.types.Object, boneIds: List[int], operator: bpy.types.Operator|None = None):
	hiddenBones = 0
	bone: bpy.types.PoseBone
	for bone in armature.pose.bones:
		boneId = bone.bone["ID"]
		if boneId not in boneIds:
			continue
		bone.bone.hide = True
		hiddenBones += 1
	print(f"Hidden {hiddenBones} bones")
	if operator is not None:
		operator.report({"INFO"}, f"Hidden {hiddenBones} bones")

class HidePl000fIrrelevantBones(bpy.types.Operator):
	bl_idname = "object.hide_pl000f_irrelevant_bones"
	bl_label = "Hide pl000f Irrelevant Bones"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		armature = getArmatureObject()
		if armature is None:
			self.report({"ERROR"}, "No armature found!")
			return {"CANCELLED"}
		if not isPl000f(armature=armature):
			print("Warning: No pl000f action found!")
		boneIds = getInvalidBoneIds(armature)
		if len(boneIds) == 0:
			print("Warning: No invalid bone ids found!")
		hideInvalidBones(armature, boneIds, operator=self)
		return {"FINISHED"}

class RemovePl000fIrrelevantAnimations(bpy.types.Operator):
	bl_idname = "object.remove_pl000f_irrelevant_animations"
	bl_label = "Remove pl000f Irrelevant Animations"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		armature = getArmatureObject()
		if armature is None:
			self.report({"ERROR"}, "No armature found!")
			return {"CANCELLED"}
		if not isPl000f(armature=armature):
			print("Warning: No pl000f action found!")
		boneIds = getInvalidBoneIds(armature)
		if len(boneIds) == 0:
			print("Warning: No invalid bone ids found!")
		removeInvalidAnimations(armature, boneIds, operator=self)
		return {"FINISHED"}
