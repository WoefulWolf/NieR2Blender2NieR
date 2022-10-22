
import re
import bpy
from .shared import SyncObjectsType
from ..lay.importer.lay_importer import updateVisualizationObject

def getSyncCollection() -> bpy.types.Collection:
	if "Sync" not in bpy.data.collections:
		syncColl = bpy.data.collections.new("Sync")
		bpy.context.scene.collection.children.link(syncColl)
	return bpy.data.collections["Sync"]

def newObjFromType(type: int, name: str, **kwargs) -> bpy.types.Object:
	obj = bpy.data.objects.new(name, None)
	getSyncCollection().objects.link(obj)

	if type == SyncObjectsType["entity"]:
		updateVisualizationObject(obj, kwargs["modelName"], False)
	else:
		raise NotImplementedError(f"Object type {type} not implemented")
	
	return obj

def findObject(name: str, uuid: str) -> bpy.types.Object | None:
	obj = bpy.data.objects.get(name)
	if obj is not None:
		return obj
	for obj in getSyncCollection().objects:
		objUuid = re.search(r"[0-9a-f\-]+$", obj.name)
		if objUuid is not None and objUuid.group(0) == uuid:
			return obj
	return None