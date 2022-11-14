import bpy
from xml.etree.ElementTree import Element, SubElement

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
	if collection["uuid"] == parentUuid:	# TODO parent uuid fuckery
		if not uuid in collection.children:
			coll = bpy.data.collections.new(nameHint or uuid)
			coll["uuid"] = uuid
			collection.children.link(coll)
		return collection.children[uuid]

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
