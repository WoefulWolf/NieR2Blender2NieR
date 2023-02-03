import bpy
from math import radians

def objRotationWrapper(obj: bpy.types.Object):
	if obj.parent is not None \
		and abs(obj.parent.rotation_euler[0] - radians(90)) < 0.001 \
		and obj.rotation_euler[0] == 0:
		return
	
	# make invisible parent with 90° rotation on x axis
	parentObj = bpy.data.objects.new("RotationWrapper", None)
	parentObj.hide_viewport = True
	parentObj.rotation_euler[0] = radians(90)
	obj.rotation_euler[0] = 0
	obj.users_collection[0].objects.link(parentObj)
	obj.parent = parentObj
