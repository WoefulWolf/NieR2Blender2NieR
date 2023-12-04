from __future__ import annotations
from math import degrees, tan
from typing import List
import bpy
from ..common.motUtils import KeyFrame, KeyFrameCombo, fovToFocalLength, getArmatureObject, getBoneFCurve, getObjFCurve
from ..common.mot import MotRecord

class PropertyAnimation:
	_propertyNameToIndex = {
		"location": 0,
		"rotation_euler": 1,
		"scale": 2,
	}
	propertyName: str
	channelIndex: int
	bone: bpy.types.PoseBone|None
	object: bpy.types.Object|None
	keyFrames: List[KeyFrame]
	armatureObj: bpy.types.Object
	
	@staticmethod
	def fromRecord(record: MotRecord) -> PropertyAnimation:
		anim = PropertyAnimation()
		anim.propertyName = record.getPropertyPath()
		anim.channelIndex = record.getPropertyIndex()
		anim.armatureObj = getArmatureObject()
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


class PropertyObjectAnimation:
	_propertyNameToIndex = {
		"location": 0,
		"rotation_euler": 1,
		"scale": 2,
	}
	propertyName: str
	channelIndex: int
	object: bpy.types.Object
	keyFrames: List[KeyFrame]
	
	@staticmethod
	def fromRecord(record: MotRecord, object: bpy.types.Object) -> PropertyObjectAnimation:
		anim = PropertyObjectAnimation()
		anim.propertyName = record.getPropertyPath()
		anim.channelIndex = record.getPropertyIndex()
		anim.object = object
		anim.keyFrames = record.interpolation.toKeyFrames()
		if anim.propertyName.startswith("unknown_"):
			anim.object[anim.propertyName] = [0.0]
			anim.propertyName = f"[\"{anim.propertyName}\"]"
		if anim.propertyName == "data.lens":
			anim.object.data.lens_unit = "FOV"
		return anim

	def getFCurve(self) -> bpy.types.FCurve:
		if self.propertyName != "data.lens":
			return getObjFCurve(self.object, self.propertyName, self.channelIndex)
		else:
			return getObjFCurve(self.object.data, "lens", 0)
			
	def applyToBlender(self):
		animProp = self.object.path_resolve(self.propertyName)
		c = self.channelIndex
		# set all keyframe values
		for motKeyFrame in self.keyFrames:
			value = motKeyFrame.value

			if self.propertyName != "data.lens":
				animProp[c] = value
				self.object.keyframe_insert(data_path=self.propertyName, index=c, frame=motKeyFrame.frame)
			else:
				fovRad = value
				focalLength = fovToFocalLength(self.object.data, fovRad)
				self.object.data.lens = focalLength
				self.object.data.keyframe_insert(data_path="lens", frame=motKeyFrame.frame)

		# set all keyframe interpolations
		fCurve = self.getFCurve()
		for i in range(len(self.keyFrames)):
			curKf = KeyFrameCombo(self.keyFrames[i], fCurve.keyframe_points[i])
			prevKf = None
			if i > 0:
				prevKf = KeyFrameCombo(self.keyFrames[i-1], fCurve.keyframe_points[i-1])
			curKf.mot.applyInterpolation(prevKf, curKf)
