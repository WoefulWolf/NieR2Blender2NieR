from __future__ import annotations
from typing import List
import bpy
from ..common.motUtils import KeyFrame, KeyFrameCombo, getArmatureObject, getBoneFCurve, getObjFCurve
from ..common.mot import MotRecord

class PropertyAnimation:
	_propertyNameToIndex = {
		"location": 0,
		"rotation_euler": 1,
		"scale": 2,
	}
	propertyName: str
	propertyNameIndex: int
	channelIndex: int
	bone: bpy.types.PoseBone|None
	object: bpy.types.Object|None
	keyFrames: List[KeyFrame]
	flag: int
	armatureObj: bpy.types.Object
	
	@staticmethod
	def fromRecord(record: MotRecord) -> PropertyAnimation:
		anim = PropertyAnimation()
		anim.propertyName = record.getPropertyPath()
		anim.propertyNameIndex = PropertyAnimation._propertyNameToIndex[anim.propertyName]
		anim.channelIndex = record.getPropertyIndex()
		anim.armatureObj = getArmatureObject()
		anim.flag = record.interpolationType
		if record.boneIndex != -1:
			anim.bone = record.getBone()
			anim.object = None
		else:
			anim.object = anim.armatureObj
			anim.bone = None
		anim.keyFrames = record.interpolation.toKeyFrames()
		return anim

	def getFCurve(self) -> bpy.types.FCurve:
		if self.bone:
			return getBoneFCurve(self.armatureObj, self.bone, self.propertyName, self.channelIndex)
		else:
			return getObjFCurve(self.object, self.propertyName, self.channelIndex)
			
	def applyToBlender(self):
		# print("=================")
		# print(self.bone.name)
		# print(self.propertyName, self.channelIndex)

		parentOffset = 0
		if self.propertyName == "location" and self.bone is not None:
			parentBonePos = self.bone.parent.bone.head_local[self.channelIndex] if self.bone.parent else 0
			parentOffset = self.bone.bone.head_local[self.channelIndex] - parentBonePos

		animObj = self.bone or self.object
		animProp = animObj.path_resolve(self.propertyName)
		c = self.channelIndex
		# set all keyframe values
		for motKeyFrame in self.keyFrames:
			value = motKeyFrame.value

			if self.propertyName == "location":
				value -= parentOffset
			
			animProp[c] = value
			animObj.keyframe_insert(data_path=self.propertyName, index=c, frame=motKeyFrame.frame)

		# set all keyframe interpolations
		fCurve = self.getFCurve()
		for i in range(len(self.keyFrames)):
			curKf = KeyFrameCombo(self.keyFrames[i], fCurve.keyframe_points[i])
			prevKf = None
			if i > 0:
				prevKf = KeyFrameCombo(self.keyFrames[i-1], fCurve.keyframe_points[i-1])
			curKf.mot.applyInterpolation(prevKf, curKf)
