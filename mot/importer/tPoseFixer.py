import bpy

TPOSE_BONES = ['_006', '_a06', '_00a', '_a0a']

def get_parent_object(obj):
	if obj.name in TPOSE_BONES:
		return True

	parent = obj.parent
    
	if parent != None and parent.name not in TPOSE_BONES:
		get_parent_object(parent)
	elif parent == None:
		return False
	else:
		return True
        
FIXED_FLAG = "FIXED_T-POSE"
def fixTPose(armObj: bpy.types.Object):
	if FIXED_FLAG in armObj and armObj[FIXED_FLAG]:
		return
	print("Applying T-Pose")
	
	# apply armature as rest pose
	bpy.context.view_layer.objects.active = armObj
	armObj.select_set(True)
	bpy.ops.object.mode_set(mode="POSE")
	for pbone in armObj.pose.bones:
		if get_parent_object(pbone):
			pbone.rotation_quaternion = pbone['TPose_Rotation']
	
	bpy.ops.object.mode_set(mode="OBJECT")
    
	# apply armature modifiers on all armature children
	child: bpy.types.Object
	for child in armObj.children:
		if child.type != "MESH":
			continue
		for mod in child.modifiers:
			if mod.type != "ARMATURE":
				continue
			bpy.context.view_layer.objects.active = child
			bpy.ops.object.modifier_apply(modifier=mod.name)

	bpy.context.view_layer.objects.active = armObj
	armObj.select_set(True)
	bpy.ops.object.mode_set(mode="POSE")
    
	bpy.ops.pose.armature_apply()
	bpy.ops.object.mode_set(mode="OBJECT")
	
	# add armature modifier back
	for child in armObj.children:
		if child.type != "MESH":
			continue
		mod: bpy.types.ArmatureModifier
		mod = child.modifiers.new(name="Armature", type="ARMATURE")
		mod.object = armObj

	armObj[FIXED_FLAG] = True
