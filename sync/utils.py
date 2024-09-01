import bpy
from mathutils import Vector
from math import tan, radians
from xml.etree.ElementTree import Element, SubElement
from ..utils.util import clamp

def getRootSyncCollection() -> bpy.types.Collection:
	if "Sync" not in bpy.data.collections:
		syncColl = bpy.data.collections.new("Sync")
		syncColl["uuid"] = "root"
		bpy.context.scene.collection.children.link(syncColl)
	return bpy.data.collections["Sync"]

def _makeSyncCollection(
		uuid: str,
		parentUuid: str,
		nameHint: str|None = None,
		collection: bpy.types.Collection|None = None
	) -> bpy.types.Collection:
	if collection is None:
		collection = getRootSyncCollection()
	if collection["uuid"] == parentUuid:
		if not uuid in collection.children:
			coll = bpy.data.collections.new(nameHint or uuid)
			coll["uuid"] = uuid
			collection.children.link(coll)
			return coll
		return next(coll for coll in collection.children if coll["uuid"] == uuid)

	for child in collection.children:
		found = _makeSyncCollection(uuid, parentUuid, nameHint, child)
		if found:
			return found

	return None

def makeSyncCollection(uuid: str, parentUuid: str, nameHint: str|None = None) -> bpy.types.Collection:
	if not parentUuid:
		parentUuid = getRootSyncCollection()["uuid"]
	coll = _makeSyncCollection(uuid, parentUuid, nameHint)
	if coll is None:
		raise Exception("Failed to make sync collection")
	return coll

def getSyncCollection(uuid: str) -> bpy.types.Collection | None:
	for coll in bpy.data.collections:
		if coll.get("uuid") == uuid:
			return coll
	return None

def findObject(uuid: str) -> bpy.types.Object | None:
	syncObjects = getRootSyncCollection().all_objects
	for obj in syncObjects:
		if obj.get("uuid") == uuid:
			return obj
	return None

def updateXmlChildWithStr(root: Element, tagName: str, newValue: str|None):
	curChild = root.find(tagName)
	if curChild is not None and newValue is not None:
		curChild.text = newValue
	elif curChild is None and newValue is None:
		pass
	elif curChild is not None and newValue is None:
		root.remove(curChild)
	elif curChild is None and newValue is not None:
		SubElement(root, tagName).text = newValue

transparentMatName = "SyncTransparent"
transparentMatColor = (0, 0, 1, 0.333)
def getTransparentMat() -> bpy.types.Material:
	if transparentMatName in bpy.data.materials:
		return bpy.data.materials[transparentMatName]
	mat = bpy.data.materials.new(transparentMatName)
	mat.use_nodes = True
	mat.blend_method = "BLEND"
	mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = transparentMatColor
	return mat

def getActiveRegionView() -> bpy.types.RegionView3D:
	for area in bpy.context.screen.areas:
		if area.type == "VIEW_3D":
			for space in area.spaces:
				if space.type == "VIEW_3D":
					space: bpy.types.SpaceView3D
					return space.region_3d

# def getObjectBoundingSphere(obj: bpy.types.Object) -> tuple[Vector, float]:
# 	# get sphere that contains the bounding box
# 	objBB = obj.bound_box
# 	spherePosX = (objBB[0][0] + objBB[6][0]) / 2
# 	spherePosY = (objBB[0][1] + objBB[6][1]) / 2
# 	spherePosZ = (objBB[0][2] + objBB[6][2]) / 2
# 	spherePos = Vector((spherePosX, spherePosY, spherePosZ))
# 	sphereRadius = 0
# 	for bbPoint in objBB:
# 		bbPointVec = Vector(bbPoint)
# 		dist = (bbPointVec - spherePos).length
# 		if dist > sphereRadius:
# 			sphereRadius = dist
# 	return spherePos, sphereRadius

def getObjectsBoundingSphere(objs: list[bpy.types.Object]) -> tuple[Vector, float]:
	# get sphere that contains the bounding box
	objsBB = []
	for obj in objs:
		if obj.data is not None:
			objBB = obj.bound_box
		else:
			size = obj.empty_display_size
			objBB = [
				[-size, -size, -size],
				[size, -size, -size],
				[size, size, -size],
				[-size, size, -size],
				[-size, -size, size],
				[size, -size, size],
				[size, size, size],
				[-size, size, size],
			]
			if obj.empty_display_type == "CIRCLE":
				for i in range(8):
					objBB[i][1] = 0
		worldBB = [obj.matrix_world @ Vector(bbPoint) for bbPoint in objBB]
		objsBB.append(worldBB)
	spherePosX = (min([bb[0][0] for bb in objsBB]) + max([bb[6][0] for bb in objsBB])) / 2
	spherePosY = (min([bb[0][1] for bb in objsBB]) + max([bb[6][1] for bb in objsBB])) / 2
	spherePosZ = (min([bb[0][2] for bb in objsBB]) + max([bb[6][2] for bb in objsBB])) / 2
	spherePos = Vector((spherePosX, spherePosY, spherePosZ))
	sphereRadius = 0
	for bb in objsBB:
		for bbPoint in bb:
			bbPointVec = Vector(bbPoint)
			dist = (bbPointVec - spherePos).length
			if dist > sphereRadius:
				sphereRadius = dist
	return spherePos, sphereRadius

def frameObjectInViewport(objs: list[bpy.types.Object]):
	if len(objs) == 0:
		return
	regionView = getActiveRegionView()
	spherePos, sphereRadius = getObjectsBoundingSphere(objs)

	# calculate distance to fit the sphere in the viewport
	assumedFov = radians(80)
	dist = sphereRadius / tan(assumedFov / 2)
	dist = clamp(dist, 3, 1000)

	# set the camera position
	camForwardVec = regionView.view_rotation @ Vector((0, 0, -1))
	camPos = spherePos - camForwardVec * dist
	regionView.view_location = camPos
	regionView.view_distance = dist

def deleteRecursively(obj: bpy.types.Object|bpy.types.Collection):
	if isinstance(obj, bpy.types.Object):
		if obj.data is not None and isinstance(obj.data, bpy.types.Mesh):
			data = obj.data
			obj.data = None
			bpy.data.meshes.remove(data, do_unlink=True)
		else:
			bpy.data.objects.remove(obj, do_unlink=True)
		for child in list(obj.children):
			deleteRecursively(child)
	elif isinstance(obj, bpy.types.Collection):
		for child in list(obj.children):
			deleteRecursively(child)
		for child in list(obj.objects):
			deleteRecursively(child)
		bpy.data.collections.remove(obj, do_unlink=True)

def findParentCollection(childUuid: str, parent: bpy.types.Collection|None = None) -> bpy.types.Collection:
	if parent is None:
		parent = getRootSyncCollection()
	if any(child.get("uuid") == childUuid for child in parent.children):
		return parent
	for child in parent.children:
		found = findParentCollection(childUuid, child)
		if found is not None:
			return found
	return None
