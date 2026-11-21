from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import bpy
from mathutils import Vector

class KeyFrame:
	interpolationType: str
	frame: int
	value: float
	m0: float|None
	m1: float|None
	applyInterpolation: Callable[[KeyFrameCombo|None, KeyFrameCombo], None]
	
	def __init__(self):
		self.interpolationType = ""
		self.frame = 0
		self.value = 0
		self.m0 = None
		self.m1 = None
		self.applyInterpolation = lambda kfData, kf: None

	def toString(self) -> str:
		return f"({self.frame}, {round(self.value, 2)})"
@dataclass
class KeyFrameCombo:
	mot: KeyFrame
	blend: bpy.types.Keyframe

class Spline:
	frame: int
	value: float
	m0: float
	m1: float

	def __init__(self, frame: int = None, value: float = None, m0: float = None, m1: float = None):
		self.frame = frame
		self.value = value
		self.m0 = m0
		self.m1 = m1

def getArmatureObject() -> bpy.types.Object:
	activeObj = bpy.context.active_object
	if activeObj is not None and activeObj.type == "ARMATURE":
		return activeObj
	allArmatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
	if len(allArmatures) == 0:
		return None
	wmbColl = bpy.data.collections.get("WMB")
	if wmbColl is None:
		return allArmatures[0]
	armaturesInWmbColl = [obj for obj in wmbColl.all_objects if obj.type == "ARMATURE"]
	if len(armaturesInWmbColl) == 0:
		return allArmatures[0]
	return armaturesInWmbColl[0]

def getActionFCurves(obj: bpy.types.Object):
	"""The F-curves the object's assigned action holds for the object, or None.

	Since Blender 4.4 an action keeps its F-curves per slot, in the channelbag of the slot the object is assigned,
	and Blender 5.0 removed the old Action.fcurves list; before 4.4 the F-curves are on the action itself."""
	animData = obj.animation_data
	if animData is None or animData.action is None:
		return None
	if bpy.app.version < (4, 4):
		return animData.action.fcurves
	from bpy_extras.anim_utils import action_get_channelbag_for_slot
	channelbag = action_get_channelbag_for_slot(animData.action, animData.action_slot)
	return channelbag.fcurves if channelbag is not None else None

def getAllActionFCurves(action: bpy.types.Action) -> list:
	"""Every F-curve list of an action: one per channelbag (one per slot) since Blender 4.4, the action's own before."""
	if bpy.app.version < (4, 4):
		return [action.fcurves]
	return [channelbag.fcurves for layer in action.layers for strip in layer.strips for channelbag in strip.channelbags]

def getBoneFCurve(armatureObj: bpy.types.Object, bone: bpy.types.PoseBone, property: str, index: int) -> bpy.types.FCurve:
	fCurves = getActionFCurves(armatureObj)
	if fCurves is None:
		return None
	return fCurves.find(f"pose.bones[\"{bone.name}\"].{property}", index=index)

def getObjFCurve(obj: bpy.types.Object, property: str, index: int) -> bpy.types.FCurve:
	fCurves = getActionFCurves(obj)
	if fCurves is None:
		return None
	return fCurves.find(property, index=index)

def interpolateLinearVal(p0: KeyFrame, p1: KeyFrame, frame: int) -> float:
	return \
		(1 - (frame - p0.frame) / (p1.frame - p0.frame)) * p0.value + \
		(frame - p0.frame) / (p1.frame - p0.frame) * p1.value

def interpolateSplineVal(p0: KeyFrame, p1: KeyFrame, frame: int) -> Spline:
	# float t = (float)(index - keys[i].index)/(keys[i+1].index - keys[i].index)
	# float val = (2*t^3 - 3*t^2 + 1)*p0 + (t^3 - 2*t^2 + t)*m0 + (-2*t^3 + 3*t^2)*p1 + (t^3 - t^2)*m1;
	
	t = (frame - p0.frame) / (p1.frame - p0.frame)
	val = (2 * t ** 3 - 3 * t ** 2 + 1) * p0.value + (t ** 3 - 2 * t ** 2 + t) * p0.m1 + (-2 * t ** 3 + 3 * t ** 2) * p1.value + (t ** 3 - t ** 2) * p1.m1
	spline = Spline()
	spline.frame = frame
	spline.value = val
	spline.m0 = p0.m1 * (1 - t) + p1.m0 * t
	spline.m1 = spline.m0
	return spline

def slopeToVec2D(slope: float) -> Vector:
	v = Vector((1, slope))
	v.normalize()
	return v

def hermitVecToBezierVec(vec: Vector) -> Vector:
	return vec / 3

def alignTo4(num: int) -> int:
	return (num + 3) & ~3
