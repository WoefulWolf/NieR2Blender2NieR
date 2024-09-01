from __future__ import annotations
from copy import deepcopy
from math import degrees, radians
import re
import time
from xml.etree import ElementTree
from uuid import uuid4

import bmesh
import bpy
from mathutils import Euler, Vector
from ..utils.util import throttle, newGeometryNodesModifier
from ..lay.importer.lay_importer import updateVisualizationObject
from .syncClient import SyncMessage, addOnMessageListener, addOnWsEndListener, disconnectFromWebsocket, sendMsgToServer, msgQueue
from .shared import SyncObjectsType, SyncUpdateType, getDisableDepsgraphUpdates, setDisableDepsgraphUpdates
from .utils import deleteRecursively, findObject, findParentCollection, frameObjectInViewport, getRootSyncCollection, getSyncCollection, getTransparentMat, makeSyncCollection, updateXmlChildWithStr
from ..utils.xmlIntegrationUtils import floatToStr, makeSphereMesh, strToFloat, vecToXmlVec3, vecToXmlVec3Scale, xmlVecToVec3, xmlVecToVec3Scale
from ..dat_dtt.exporter.datHashGenerator import crc32
from xml.etree.ElementTree import Element, SubElement

syncedObjects: dict[str, SyncedObject] = {}

def onWsMsg(msg: SyncMessage):
	global syncedObjects
	setDisableDepsgraphUpdates(True)

	try:
		if msg.method == "update":
			if msg.uuid in syncedObjects:
				syncObj = syncedObjects[msg.uuid]
				syncObj.update(msg)
			else:
				sendMsgToServer(SyncMessage("endSync", msg.uuid, {}))
		elif msg.method == "startSync":
			initAllObjects = list(getRootSyncCollection().all_objects)
			newObj = SyncedObject.fromType(msg)
			syncedObjects[msg.uuid] = newObj
			newAllObjects = list(getRootSyncCollection().all_objects)
			bpy.app.timers.register(
				lambda: highlightNewObjects([obj for obj in newAllObjects if obj not in initAllObjects]),
				first_interval=0.005
			)
		elif msg.method == "endSync":
			if msg.uuid in syncedObjects:
				syncedObjects[msg.uuid].endSync(False)
	finally:
		setDisableDepsgraphUpdates(False)

def highlightNewObjects(objs: list[bpy.types.Object]):
	frameObjectInViewport(objs)
	for obj in objs:
		obj.select_set(True)

def onWsEnd():
	for syncObj in list(syncedObjects.values()):
		syncObj.endSync(False)
	syncedObjects.clear()

def onDepsgraphUpdate(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
	if getDisableDepsgraphUpdates():
		return
	_onDepsgraphUpdateThrottled(scene, depsgraph)
@throttle(10)
def _onDepsgraphUpdateThrottled(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
	setDisableDepsgraphUpdates(True)
	try:
		pendingObjectsQueue: list[SyncedObject] = []
		# check for changes in hierarchical order (breadth-first)
		# root objects don't have parents, so they are processed first
		rootSyncObjects = [syncObj for syncObj in syncedObjects.values() if not syncObj.parentUuid]
		for syncObj in rootSyncObjects:
			if isinstance(syncObj, SyncedXmlObject):
				if not findObject(syncObj.uuid):
					syncObj.endSync()
					continue
			elif isinstance(syncObj, SyncedListObject):
				if not getSyncCollection(syncObj.uuid):
					syncObj.endSync()
					continue
			pendingObjectsQueue.append(syncObj)
		
		processedObjectsOnDepsgraphUpdate = set(syncedObjects.keys())
		while pendingObjectsQueue:
			syncObj = pendingObjectsQueue.pop(0)
			
			if isinstance(syncObj, SyncedListObject):
				newPendingObjects = list(syncObj.objects)
			if syncObj.hasChanged():
				syncObj.onChanged()
			if isinstance(syncObj, SyncedListObject):
				updatedPendingObjects = list(syncObj.objects)
				pendingObjects = [obj for obj in updatedPendingObjects if obj in newPendingObjects]
				removedObjects = [obj for obj in newPendingObjects if obj not in updatedPendingObjects]
				pendingObjectsQueue.extend(pendingObjects)
				for obj in removedObjects:
					if obj.uuid in processedObjectsOnDepsgraphUpdate:
						processedObjectsOnDepsgraphUpdate.remove(obj.uuid)
			
			if syncObj.uuid in processedObjectsOnDepsgraphUpdate:
				processedObjectsOnDepsgraphUpdate.remove(syncObj.uuid)
	
		# for uuid in processedObjectsOnDepsgraphUpdate:
		# 	# dangling objects
		# 	print("dangling object", uuid)
		# 	syncedObjects[uuid].endSync()
	finally:
		setDisableDepsgraphUpdates(False)

class SyncedObject:
	uuid: str
	nameHint: str|None = None
	parentUuid: str|None = None
	allowReparent: bool = False

	def __init__(self, uuid: str, nameHint: str|None, parentUuid: str|None, allowReparent: bool):
		self.uuid = uuid
		self.nameHint = nameHint
		self.parentUuid = parentUuid
		self.allowReparent = allowReparent
	
	@classmethod
	def fromType(cls, msg: SyncMessage):
		uuid = msg.uuid
		type = SyncObjectsType.fromInt(msg.args["type"])
		nameHint = msg.args.get("nameHint", None)
		parentUuid = msg.args.get("parentUuid", None)
		allowReparent = msg.args.get("allowReparent", False)
		if type == SyncObjectsType.list:
			allowListChange = msg.args.get("allowListChange", False)
			return SyncedListObject(uuid, msg, nameHint, parentUuid, allowReparent, allowListChange)
		else:
			xml = ElementTree.fromstring(msg.args["propXml"])
			if type == SyncObjectsType.entity:
				return SyncedEntityObject(uuid, xml, nameHint, parentUuid, allowReparent)
			elif type == SyncObjectsType.area:
				return SyncedAreaObject(uuid, xml, nameHint, parentUuid, allowReparent)
			elif type == SyncObjectsType.bezier:
				return SyncedBezierObject(uuid, xml, nameHint, parentUuid, allowReparent)
			elif type == SyncObjectsType.enemyGeneratorNode:
				return SyncedEMGeneratorNodeObject(uuid, xml, nameHint, parentUuid, allowReparent)
			elif type == SyncObjectsType.enemyGeneratorDist:
				return SyncedEMGeneratorDistObject(uuid, xml, nameHint, parentUuid, allowReparent)
			elif type == SyncObjectsType.camTargetLocation:
				return SyncedCameraTargetLocationObject(uuid, xml, nameHint, parentUuid, allowReparent)
			elif type == SyncObjectsType.camera:
				return SyncedCameraObject(uuid, xml, nameHint, parentUuid, allowReparent)
		raise NotImplementedError()

	def update(self, msg: SyncMessage):
		raise NotImplementedError()
	
	def hasChanged(self) -> bool:
		raise NotImplementedError()
	
	def onChanged(self):
		raise NotImplementedError()
	
	def endSync(self, sendMsg: bool = True):
		raise NotImplementedError()

class SyncedXmlObject(SyncedObject):
	xml: Element
	
	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parentUuid: str|None, allowReparent: bool):
		super().__init__(uuid, nameHint, parentUuid, allowReparent)
		self.xml = xml

	def xmlCmp(self, el1: Element, el2: Element) -> bool:
		if el1.tag != el2.tag:
			return False
		if el1.text != el2.text:
			return False
		if len(el1) != len(el2):
			return False
		for i in range(len(el1)):
			if not self.xmlCmp(el1[i], el2[i]):
				return False
		return True

	def update(self, msg: SyncMessage):
		xmlStr  = msg.args["propXml"]
		xmlRoot = ElementTree.fromstring(xmlStr)
		if not self.xmlCmp(self.xml, xmlRoot):
			print(f"updating {self.uuid}")
			self.updateWithXml(xmlRoot)

	def endSync(self, sendMsg: bool = True):
		if sendMsg:
			sendMsgToServer(SyncMessage("endSync", self.uuid, {}))
		obj = findObject(self.uuid)
		if obj is not None:
			deleteRecursively(obj)
		if self.uuid in syncedObjects:
			del syncedObjects[self.uuid]

	@throttle(0.04)
	def onChanged(self):
		self.xml = self.selfToXml()
		sendMsgToServer(SyncMessage(
			"update",
			self.uuid,
			{
				"propXml": ElementTree.tostring(self.xml, encoding="unicode")
			}
		))
	
	def updateWithXml(self, xmlRoot: Element):
		raise NotImplementedError()
	
	def selfToXml(self) -> Element:
		raise NotImplementedError()
	
	def hasChanged(self) -> bool:
		return not self.xmlCmp(self.xml, self.selfToXml())

class SyncedListObject(SyncedObject):
	objects: list[SyncedObject]
	listType: str
	allowListChange: bool
	
	def __init__(self, uuid: str, msg: SyncMessage, nameHint: str|None, parentUuid: str|None, allowReparent: bool, allowListChange: bool):
		super().__init__(uuid, nameHint, parentUuid, allowReparent)
		self.listType = msg.args["listType"]
		self.objects = []
		self.allowListChange = allowListChange
		makeSyncCollection(uuid, self.parentUuid, nameHint)

		for child in msg.args["children"]:
			childMsg = SyncMessage.fromJson(child)
			syncObj = SyncedObject.fromType(childMsg)
			self.objects.append(syncObj)
			syncedObjects[syncObj.uuid] = syncObj
	
	def update(self, msg: SyncMessage):
		updateType = SyncUpdateType.fromInt(msg.args["type"])
		if updateType == SyncUpdateType.add:
			self.updateAdd(msg)
		elif updateType == SyncUpdateType.remove:
			self.updateRemove(msg)
		else:
			raise Exception(f"Unknown update type {updateType}")
	
	def updateAdd(self, msg: SyncMessage):
		startSyncMsg = SyncMessage.fromJson(msg.args["syncObj"])
		syncObj = SyncedObject.fromType(startSyncMsg)
		self.objects.append(syncObj)
		objUuid = msg.args["uuid"]
		syncedObjects[objUuid] = syncObj
	
	def updateRemove(self, msg: SyncMessage):
		uuid = msg.args["uuid"]
		removedObj = next(obj for obj in self.objects if obj.uuid == uuid)
		self.objects.remove(removedObj)
		removedObj.endSync(False)
	
	def endSync(self, sendMsg: bool = True):
		if sendMsg:
			sendMsgToServer(SyncMessage("endSync", self.uuid, {}))
		collection = getSyncCollection(self.uuid)
		if collection is not None:
			deleteRecursively(collection)
		if self.uuid in syncedObjects:
			del syncedObjects[self.uuid]
		for obj in self.objects:
			obj.endSync(sendMsg)
	
	def hasChanged(self) -> bool:
		coll = getSyncCollection(self.uuid)
		if coll is None:
			raise Exception(f"Collection {self.uuid} not found")
		
		blenderObjects: list[bpy.types.Object|bpy.types.Collection] = [
			*coll.objects, *coll.children
		]
		blenderObjects = [obj for obj in blenderObjects if "uuid" in obj]
		if len(blenderObjects) != len(self.objects):
			return True
		blenderObjUuids = [obj["uuid"] for obj in blenderObjects]
		syncObjUuids = [obj.uuid for obj in self.objects]
		blenderObjUuids.sort()
		syncObjUuids.sort()
		return blenderObjUuids != syncObjUuids
	
	def onChanged(self):
		coll = getSyncCollection(self.uuid)
		if coll is None:
			raise Exception(f"Collection {self.uuid} not found")
		
		blenderObjects: list[bpy.types.Object|bpy.types.Collection] = [
			*coll.objects, *coll.children
		]
		blenderObjects = [obj for obj in blenderObjects if "uuid" in obj]
		blenderObjUuids = [obj["uuid"] for obj in blenderObjects]
		syncObjUuids = [obj.uuid for obj in self.objects]

		# removed objects
		removedUuids = [uuid for uuid in syncObjUuids if uuid not in blenderObjUuids]
		for removedUuid in removedUuids:
			if findObject(removedUuid) is not None:
				reparentedObj = findObject(removedUuid)
				repObjCollUuid = reparentedObj.users_collection[0].get("uuid")
				if repObjCollUuid is None or not syncedObjects[removedUuid].allowReparent:
					print(f"moving {removedUuid} back to {self.uuid}")
					reparentedObj.users_collection[0].objects.unlink(reparentedObj)
					coll.objects.link(reparentedObj)
					continue
				self.handleObjectReparent(removedUuid)
				continue
			if getSyncCollection(removedUuid) is not None:
				if not syncedObjects[removedUuid].allowReparent:
					print(f"moving {removedUuid} back to {self.uuid}")
					wrongParentColl = findParentCollection(removedUuid)
					wrongParentColl.children.unlink(getSyncCollection(removedUuid))
					coll.children.link(getSyncCollection(removedUuid))
					continue
				self.handleObjectReparent(removedUuid)
				continue
			
			if not self.allowListChange:
				raise Exception(f"Object {removedUuid} was removed from {self.uuid} but list changes are not allowed")
			removeSyncObj = next(obj for obj in self.objects if obj.uuid == removedUuid)
			self.objects.remove(removeSyncObj)
			removeSyncObj.endSync(False)
			if removedUuid in syncedObjects:
				del syncedObjects[removedUuid]
			sendMsgToServer(SyncMessage("update", self.uuid, {
				"type": SyncUpdateType.remove.value,
				"uuid": removedUuid
			}))
		
		# duplicate objects
		duplicateUuids = [uuid for uuid in set(blenderObjUuids) if blenderObjUuids.count(uuid) > 1]
		if len(duplicateUuids) > 0 and not self.allowListChange:
			raise Exception(f"Duplicate objects found in {self.uuid} but list changes are not allowed")
		duplicateBlenderObjects: dict[str, list[bpy.types.Object]] = {
			uuid: [obj for obj in blenderObjects if obj["uuid"] == uuid][1:]
			for uuid in duplicateUuids
		}
		for duplicateUuid in duplicateUuids:
			srcSyncObj = [obj for obj in self.objects if obj.uuid == duplicateUuid]
			if len(srcSyncObj) == 0:
				print("duplicate object not found in sync list")
				continue
			srcSyncObj = srcSyncObj[0]
			for obj in duplicateBlenderObjects[duplicateUuid]:
				newUuid = str(uuid4())
				obj["uuid"] = newUuid
				newSyncObj = deepcopy(srcSyncObj)
				newSyncObj.uuid = newUuid
				self.objects.append(newSyncObj)
				syncedObjects[newUuid] = newSyncObj
				sendMsgToServer(SyncMessage("update", self.uuid, {
					"type": SyncUpdateType.duplicate.value,
					"srcObjUuid": duplicateUuid,
					"newObjUuid": newUuid,
				}))

		# added objects
		addedUuids = [uuid for uuid in blenderObjUuids if uuid not in syncObjUuids]
		for addedUuid in addedUuids:
			addedObj = findObject(addedUuid) or getSyncCollection(addedUuid)
			addedObjUuid = addedObj["uuid"]
			if addedObjUuid not in syncedObjects:
				print("added object not found in synced objects")
				continue
			if not syncedObjects[addedObjUuid].allowReparent:
				print(f"moving {addedObjUuid} back to {self.uuid}")
				originalCollUuid = syncedObjects[addedObjUuid].parentUuid
				originalColl = getSyncCollection(originalCollUuid)
				if originalColl is None:
					print("original collection not found")
					continue
				if isinstance(addedObj, bpy.types.Object):
					coll.objects.unlink(addedObj)
					originalColl.objects.link(addedObj)
				else:
					coll.children.unlink(addedObj)
					originalColl.children.link(addedObj)
				continue
			self.handleObjectReparent(addedObjUuid)

	@staticmethod
	def handleObjectReparent(objUuid: str):
		syncObj = syncedObjects[objUuid]
		srcList = syncedObjects[syncObj.parentUuid]
		blenderObj = findObject(objUuid)
		if blenderObj is not None:
			objCollUuid = blenderObj.users_collection[0].get("uuid")
		else:
			parentColl = findParentCollection(objUuid)
			if parentColl is None:
				raise Exception(f"Parent collection of {objUuid} not found")
			objCollUuid = parentColl.get("uuid")
		if objCollUuid is None:
			raise Exception(f"Object {objUuid} not in collection")
		destList = syncedObjects[objCollUuid]
		srcList.objects.remove(syncObj)
		destList.objects.append(syncObj)
		syncObj.parentUuid = objCollUuid
		sendMsgToServer(SyncMessage("reparent", objUuid, {
			"srcListUuid": srcList.uuid,
			"destListUuid": destList.uuid,
		}))

class SyncedEntityObject(SyncedXmlObject):
	# syncable props: location{ position, rotation?, }, scale?, objId

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parentUuid: str|None, allowReparent: bool):
		objId = xml.find("objId").text
		super().__init__(uuid, xml, objId, parentUuid, allowReparent)
		self.newObjFromType(SyncObjectsType.entity, objId + " Entity", modelName=self.xml.find("objId").text)
		self.updateWithXml(self.xml)

	def updateWithXml(self, xmlRoot: Element):
		prevObjId = self.xml.find("objId").text
		objId = xmlRoot.find("objId").text
		self.xml = xmlRoot
		obj = findObject(self.uuid)
		if not obj:
			obj = self.newObjFromType(SyncObjectsType.entity, objId + " Entity", modelName=objId)
		elif objId != prevObjId:
			# update model
			updateVisualizationObject(obj, objId, False)
			# update name
			obj.name = objId + " Entity"

		pos = xmlVecToVec3(xmlRoot.find("location/position").text)
		obj.location = pos

		rotEl = xmlRoot.find("location/rotation")
		if rotEl is not None:
			rot = xmlVecToVec3(rotEl.text)
			obj.rotation_euler = rot
		
		scaleEl = xmlRoot.find("scale")
		if scaleEl is not None:
			scale = xmlVecToVec3Scale(scaleEl.text)
			obj.scale = scale
	
	def selfToXml(self) -> Element:
		root = deepcopy(self.xml)
		obj = findObject(self.uuid)
		
		location = root.find("location")
		updateXmlChildWithStr(location, "position", vecToXmlVec3(obj.location))
		updateXmlChildWithStr(
			location, "rotation",
			vecToXmlVec3(obj.rotation_euler) if obj.rotation_euler != Euler((0, 0, 0)) else None
		)
		updateXmlChildWithStr(
			root,
			"scale",
			vecToXmlVec3Scale(obj.scale) if obj.scale != Vector((1, 1, 1)) else None
		)
		
		objId = obj.name.split(" ")[0]
		if not re.match(r"[a-z]{2}[a-f0-9]{4}", objId):
			objId = self.xml.find("objId").text
		updateXmlChildWithStr(root, "objId", objId)

		return root

	def onChanged(self):
		obj = findObject(self.uuid)
		if obj is not None and self.objIdFromName(obj.name) != self.objIdFromXml():
			# name was changed
			updateVisualizationObject(obj, obj.name.split(" ")[0], False)
		super().onChanged()
	
	def newObjFromType(self, type: SyncObjectsType, name: str, modelName: str) -> bpy.types.Object:
		obj = bpy.data.objects.new(name, None)
		obj["uuid"] = self.uuid
		getSyncCollection(self.parentUuid).objects.link(obj)

		if type == SyncObjectsType.entity:
			updateVisualizationObject(obj, modelName, False)
		else:
			raise NotImplementedError(f"Object type {type} not implemented")
		
		return obj
	
	@staticmethod
	def objIdFromName(name: str) -> str:
		return name.split(" ")[0]
	
	def objIdFromXml(self) -> str:
		return self.xml.find("objId").text

class SyncedAreaObject(SyncedXmlObject):
	_typeBoxArea = "app::area::BoxArea"
	_typeCylinderArea = "app::area::CylinderArea"
	_typeSphereArea = "app::area::SphereArea"
	# syncable props: position, rotation, scale, points, height
	_typeBoxAreaHash = crc32(_typeBoxArea)
	# syncable props: position, rotation, scale, radius, height
	_typeCylinderAreaHash = crc32(_typeCylinderArea)
	# syncable props: position, radius
	_typeSphereAreaHash = crc32(_typeSphereArea)

	_objColor = (0.25, 0.25, 1, 0.333)

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parentUuid: str|None, allowReparent: bool):
		super().__init__(uuid, xml, nameHint, parentUuid, allowReparent)
		self.newAreaObjectFromType(int(xml.find("code").text, 16))
		self.updateWithXml(self.xml)
	
	def selfToXml(self) -> Element:
		root = Element("value")
		obj = findObject(self.uuid)
		
		code = self.xml.find("code").text
		codeInt = int(code, 16)
		SubElement(root, "code").text = code
		
		SubElement(root, "position").text = vecToXmlVec3(obj.location)
		if codeInt != self._typeSphereAreaHash:
			SubElement(root, "rotation").text = vecToXmlVec3(obj.rotation_euler)
			SubElement(root, "scale").text = vecToXmlVec3Scale(obj.scale)

			if codeInt == self._typeBoxAreaHash:
				vertPoints = [v.co[:2] for v in obj.data.vertices]
				points =  " ".join([floatToStr(v) for c in vertPoints for v in c])
				SubElement(root, "points").text = points
			elif codeInt == self._typeCylinderAreaHash:
				geometryNodeTree = obj.modifiers[0].node_group
				radiusIdentifier = geometryNodeTree.inputs[1].identifier
				radius = obj.modifiers[0][radiusIdentifier]
				SubElement(root, "radius").text = floatToStr(radius)

			height = obj.modifiers["Solidify"].thickness
			SubElement(root, "height").text = floatToStr(height)
		else:
			scale = obj.scale[0]
			SubElement(root, "radius").text = floatToStr(scale)

		return root
	
	def updateWithXml(self, xmlRoot: Element):
		obj = findObject(self.uuid)
		if obj is None:
			return

		code = xmlRoot.find("code").text
		codeInt = int(code, 16)
		
		# pos
		pos = xmlVecToVec3(xmlRoot.find("position").text)
		obj.location = pos

		# rot, scale, height
		if codeInt != self._typeSphereAreaHash:
			rot = xmlVecToVec3(xmlRoot.find("rotation").text)
			scale = xmlVecToVec3Scale(xmlRoot.find("scale").text)
			obj.rotation_euler = rot
			obj.scale = scale

			height = strToFloat(xmlRoot.find("height").text)
			obj.modifiers["Solidify"].thickness = height
		
		# points
		if codeInt == self._typeBoxAreaHash:
			points = self.xml.find("points").text.split(" ")
			points = map(lambda x: strToFloat(x), points)
			points = list(zip(*(iter(points),) * 2))
			for i in range(4):
				obj.data.vertices[i].co[0] = points[i][0]
				obj.data.vertices[i].co[1] = points[i][1]
		
		# radius
		if codeInt == self._typeCylinderAreaHash:
			radius = strToFloat(xmlRoot.find("radius").text)
			nodeTree = obj.modifiers[0].node_group
			radiusIdentifier = nodeTree.inputs[1].identifier
			obj.modifiers[0][radiusIdentifier] = radius
			nodeTree.inputs[1].default_value = radius
		elif codeInt == self._typeSphereAreaHash:
			radius = strToFloat(xmlRoot.find("radius").text)
			obj.scale = (radius, radius, radius)

	def newAreaObjectFromType(self, type: int) -> bpy.types.Object:
		name: str = "area"
		if type == self._typeBoxAreaHash:
			name = self._typeBoxArea
		elif type == self._typeCylinderAreaHash:
			name = self._typeCylinderArea
		elif type == self._typeSphereAreaHash:
			name = self._typeSphereArea
		else:
			raise NotImplementedError(f"Object type {type} not implemented")
		
		name += " " + self.uuid
		mesh = bpy.data.meshes.new(name)
		obj = bpy.data.objects.new(name, mesh)
		obj["uuid"] = self.uuid
		obj.color = self._objColor
		obj.data.materials.append(getTransparentMat())
		obj.show_wire = True
		getSyncCollection(self.parentUuid).objects.link(obj)

		# transforms
		pos = xmlVecToVec3(self.xml.find("position").text)
		obj.location = pos
		if (type != self._typeSphereAreaHash):
			rot = xmlVecToVec3(self.xml.find("rotation").text)
			scale = xmlVecToVec3Scale(self.xml.find("scale").text)
			obj.rotation_euler = rot
			obj.scale = scale

		if type == self._typeBoxAreaHash:
			# base face
			points = self.xml.find("points").text.split(" ")
			points = map(lambda x: strToFloat(x), points)
			points = list(zip(*(iter(points),) * 2))

			vertices = [ point + (0,) for point in points ]
			faces = [list(range(len(vertices)))]
			mesh.from_pydata(vertices, [], faces)
			mesh.update()
		elif type == self._typeCylinderAreaHash or type == self._typeSphereAreaHash:
			# use geometry nodes
				# cylinder: first create a circle curve and then fill it
				# sphere: just create a uv sphere
			geometryNodesMod: bpy.types.NodesModifier = newGeometryNodesModifier(obj)
			nodeTree = geometryNodesMod.node_group

			inputNode = nodeTree.nodes["Group Input"]
			outputNode = nodeTree.nodes["Group Output"]
			if type == self._typeCylinderAreaHash:
				circleNode = nodeTree.nodes.new("GeometryNodeCurvePrimitiveCircle")
				fillNode = nodeTree.nodes.new("GeometryNodeFillCurve")
				fillNode.mode = "NGONS"
				circleNode.location = (-170, 0)
				nodeTree.links.new(circleNode.outputs["Curve"], fillNode.inputs["Curve"])
				nodeTree.links.new(fillNode.outputs["Mesh"], outputNode.inputs["Geometry"])
			else:
				sphereNode = nodeTree.nodes.new("GeometryNodeMeshUVSphere")
				nodeTree.links.new(sphereNode.outputs["Mesh"], outputNode.inputs["Geometry"])

			inputNode.outputs.new("VALUE", "Radius")
			if type == self._typeCylinderAreaHash:
				nodeTree.links.new(inputNode.outputs["Radius"], circleNode.inputs["Radius"])
			else:
				nodeTree.links.new(inputNode.outputs["Radius"], sphereNode.inputs["Radius"])
			
			nodeTree.inputs[1].hide_value = False
			radiusIdentifier = nodeTree.inputs[1].identifier
			radius = strToFloat(self.xml.find("radius").text) if type == self._typeCylinderAreaHash else 1
			geometryNodesMod[radiusIdentifier] = radius
			nodeTree.inputs[1].default_value = radius 
			nodeTree.inputs[1].hide_value = type == self._typeSphereAreaHash
		if type == self._typeSphereAreaHash:
			radius = strToFloat(self.xml.find("radius").text)
			obj.scale = (radius, radius, radius)

		# height modifier
		if (type != self._typeSphereAreaHash):
			height = strToFloat(self.xml.find("height").text)
			solidifyMod = obj.modifiers.new("Solidify", "SOLIDIFY")
			solidifyMod.thickness = height
			solidifyMod.offset = 1
		
		return obj

class SyncedBezierObject(SyncedXmlObject):
	# syncable props: attribute, parent?, controls, nodes

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parent: SyncedXmlObject|None, allowReparent: bool):
		super().__init__(uuid, xml, nameHint, parent, allowReparent)
		self.makeBezierObject()
		self.updateWithXml(self.xml)

	def updateWithXml(self, xmlRoot: Element):
		self.xml = xmlRoot

		newPoints = xmlRoot.find("nodes").findall("value")
		newPoints = [xmlVecToVec3(point.find("point").text) for point in newPoints]

		newHandles = xmlRoot.find("controls").findall("value")
		newHandles = [val.find("cp").text.split(" ") for val in newHandles]
		newLeftHandles = [xmlVecToVec3(" ".join(handle[:3])) for handle in newHandles]
		newRightHandles = [xmlVecToVec3(" ".join(handle[3:])) for handle in newHandles]
		for i, invHandle in enumerate(newLeftHandles):
			vecToPoint = Vector(newPoints[i]) - Vector(invHandle)
			newLeftHandles[i] = Vector(newPoints[i]) + vecToPoint
		
		curve: bpy.types.Curve = findObject(self.uuid).data
		bezierPoints = curve.splines[0].bezier_points

		minLen = min(len(bezierPoints), len(newPoints))
		for i in range(minLen):
			bezierPoints[i].co = newPoints[i]
			bezierPoints[i].handle_left = newLeftHandles[i]
			bezierPoints[i].handle_right = newRightHandles[i]
		if len(bezierPoints) < len(newPoints):
			bezierPoints.add(len(newPoints) - len(bezierPoints))
			for i in range(minLen, len(newPoints)):
				bezierPoints[i].co = newPoints[i]
				bezierPoints[i].handle_left = newLeftHandles[i]
				bezierPoints[i].handle_right = newRightHandles[i]
		elif len(bezierPoints) > len(newPoints):
			for i in range(len(newPoints), len(bezierPoints)):
				del bezierPoints[i]
	
	def selfToXml(self) -> Element:
		rootCopy = deepcopy(self.xml)
		
		curve: bpy.types.Curve = findObject(self.uuid).data
		bezierCurvePoints = curve.splines[0].bezier_points
		bezierPoints = [bp.co for bp in bezierCurvePoints]
		bezierRightHandles = [bp.handle_right for bp in bezierCurvePoints]
		bezierLeftHandles = [bp.handle_left for bp in bezierCurvePoints]
		for i, invHandle in enumerate(bezierLeftHandles):
			vecToPoint = Vector(bezierPoints[i]) - Vector(invHandle)
			bezierLeftHandles[i] = Vector(bezierPoints[i]) + vecToPoint
		curLen = len(bezierPoints)
		bezierPointsStrs = [vecToXmlVec3(point) for point in bezierPoints]
		bezierHandlesStrs = [
			vecToXmlVec3(leftHandle) + " " + vecToXmlVec3(rightHandle)
			for leftHandle, rightHandle in zip(bezierLeftHandles, bezierRightHandles)
		]

		nodes = rootCopy.find("nodes")
		SyncedBezierObject.updateXmlChildren(nodes, curLen, "point", bezierPointsStrs)

		controls = rootCopy.find("controls")
		SyncedBezierObject.updateXmlChildren(controls, curLen, "cp", bezierHandlesStrs)

		return rootCopy
	
	@staticmethod
	def updateXmlChildren(root: Element, curLen: int, childTagName: str, newChildStrings: list[str]):
		root.find("size").text = str(curLen)
		newLen = len(root.findall("value"))
		minLen = min(curLen, newLen)
		for i in range(minLen):
			point = root.findall("value")[i].find(childTagName)
			point.text = newChildStrings[i]
		if curLen < len(root.findall("value")):
			for i in range(minLen, newLen):
				root.remove(root[-1])
		elif curLen > len(root.findall("value")):
			for i in range(len(root.findall("value")), curLen):
				newNode = deepcopy(root[-1])
				newNode.find(childTagName).text = newChildStrings[i]
				root.append(newNode)

	def makeBezierObject(self):
		curve: bpy.types.Curve = bpy.data.curves.new(self.nameHint or "bezier", "CURVE")
		curveObj = bpy.data.objects.new(self.nameHint or "bezier", curve)
		curveObj["uuid"] = self.uuid
		getSyncCollection(self.parentUuid).objects.link(curveObj)

		curve.dimensions = "3D"
		curve.splines.new(type="BEZIER")

		curve.bevel_mode = "ROUND"
		curve.bevel_depth = 0.1
		curve.bevel_resolution = 8

class SyncedEMGeneratorNodeObject(SyncedXmlObject):
	# syncable props: point, radius

	_objColor = (1, 0, 1, 0.333)

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parent: SyncedXmlObject|None, allowReparent: bool):
		super().__init__(uuid, xml, nameHint, parent, allowReparent)
		self.makeSphere()
		self.updateWithXml(self.xml)
	
	def updateWithXml(self, xmlRoot: Element):
		point = xmlRoot.find("point").text
		radius = xmlRoot.find("radius").text
		sphere: bpy.types.Object = findObject(self.uuid)
		sphere.location = xmlVecToVec3(point)
		sphere.scale = (float(radius), float(radius), float(radius))
	
	def selfToXml(self) -> Element:
		rootCopy = deepcopy(self.xml)
		sphere: bpy.types.Object = findObject(self.uuid)
		rootCopy.find("point").text = vecToXmlVec3(sphere.location)
		rootCopy.find("radius").text = str(sphere.scale[0])
		return rootCopy

	def makeSphere(self):
		sphere: bpy.types.Mesh = bpy.data.meshes.new(self.nameHint or "node")
		sphereObj = bpy.data.objects.new(self.nameHint or "sphere", sphere)
		sphereObj["uuid"] = self.uuid
		getSyncCollection(self.parentUuid).objects.link(sphereObj)
		sphereObj.color = self._objColor
		sphereObj.data.materials.append(getTransparentMat())

		geometryNodesMod: bpy.types.NodesModifier = newGeometryNodesModifier(sphereObj)
		nodeTree = geometryNodesMod.node_group

		inputNode = nodeTree.nodes["Group Input"]
		outputNode = nodeTree.nodes["Group Output"]
		sphereNode = nodeTree.nodes.new("GeometryNodeMeshUVSphere")
		nodeTree.links.new(sphereNode.outputs["Mesh"], outputNode.inputs["Geometry"])

		inputNode.outputs.new("VALUE", "Radius")
		nodeTree.links.new(inputNode.outputs["Radius"], sphereNode.inputs["Radius"])
		
		nodeTree.inputs[1].hide_value = False
		radiusIdentifier = nodeTree.inputs[1].identifier
		radius = 1
		geometryNodesMod[radiusIdentifier] = radius
		nodeTree.inputs[1].default_value = radius 
		nodeTree.inputs[1].hide_value = True

class SyncedEMGeneratorDistObject(SyncedXmlObject):
	# syncable props: dist { position, areaDist?, resetDist?, searchDist?, guardSDist?, guardLDist?, escapeDist? }

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parent: SyncedXmlObject|None, allowReparent: bool):
		super().__init__(uuid, xml, nameHint, parent, allowReparent)
		self.makeEmptyRoot()
		self.updateWithXml(self.xml)
	
	def updateWithXml(self, xmlRoot: Element):
		position = xmlRoot.find("position").text
		posRoot: bpy.types.Object = findObject(self.uuid)
		posRoot.location = xmlVecToVec3(position)

		children = { self.getDistName(child.name): child for child in posRoot.children } 
		for distE in xmlRoot:
			if distE.tag == "position":
				continue

			if distE.tag in children:
				distObj = children[distE.tag]
			else:
				distObj = self.makeEmptyDist(distE.tag, posRoot)
			dist = strToFloat(distE.text)
			distObj.scale = (dist, dist, dist)
		
	def selfToXml(self) -> Element:
		rootCopy = deepcopy(self.xml)
		posRoot: bpy.types.Object = findObject(self.uuid)
		rootCopy.find("position").text = vecToXmlVec3(posRoot.location)

		children = { self.getDistName(child.name): child for child in posRoot.children }
		curXmlDistNames = [ distE.tag for distE in rootCopy if distE.tag != "position" ]
		for distName, distObj in children.items():
			dist = distObj.scale[0]
			if distName not in curXmlDistNames:
				rootCopy.append(Element(distName))
			rootCopy.find(distName).text = floatToStr(dist)
		return rootCopy
	
	def getDistName(self, name: str) -> str:
		return name.split(".")[0]
	
	def makeEmptyRoot(self):
		empty: bpy.types.Object = bpy.data.objects.new(self.nameHint or "dist", None)
		empty["uuid"] = self.uuid
		makeSyncCollection(self.uuid, self.parentUuid, "dist").objects.link(empty)
		empty.empty_display_type = "PLAIN_AXES"
		empty.lock_rotation = (True, True, True)
		empty.lock_scale = (True, True, True)

	def makeEmptyDist(self, distName: str, parent: bpy.types.Object) -> bpy.types.Object:
		empty: bpy.types.Object = bpy.data.objects.new(distName, None)
		empty["uuid"] = self.uuid
		getSyncCollection(self.uuid).objects.link(empty)
		empty.empty_display_type = "CIRCLE"
		empty.empty_display_size = 0.5
		empty.parent = parent
		empty.rotation_euler[0] = radians(90)
		empty.lock_location = (True, True, True)
		empty.lock_rotation = (True, True, True)

		return empty
	
class SyncedCameraTargetLocationObject(SyncedXmlObject):
	# syncable props: position?, rotation?

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parent: SyncedXmlObject|None, allowReparent: bool):
		super().__init__(uuid, xml, nameHint, parent, allowReparent)
		self.makeEmptyObject()
		self.updateWithXml(self.xml)
	
	def updateWithXml(self, xmlRoot: Element):
		posRoot: bpy.types.Object = findObject(self.uuid)
		positionE = xmlRoot.find("position")
		rotationE = xmlRoot.find("rotation")
		if positionE is not None:
			position = xmlVecToVec3(positionE.text)
		else:
			position = (0, 0, 0)
		if rotationE is not None:
			rotation = xmlVecToVec3(rotationE.text)
		else:
			rotation = (0, 0, 0)
		posRoot.location = position
		posRoot.rotation_euler = rotation

	def selfToXml(self) -> Element:
		rootCopy = deepcopy(self.xml)
		posRoot: bpy.types.Object = findObject(self.uuid)
		position = vecToXmlVec3(posRoot.location) if posRoot.location != Vector((0, 0, 0)) else None
		rotation = vecToXmlVec3(posRoot.rotation_euler) if posRoot.rotation_euler != Euler((0, 0, 0)) else None
		updateXmlChildWithStr(rootCopy, "position", position)
		updateXmlChildWithStr(rootCopy, "rotation", rotation)

		return rootCopy
	
	def makeEmptyObject(self):
		empty: bpy.types.Object = bpy.data.objects.new(self.nameHint or "cameraTarget", None)
		empty["uuid"] = self.uuid
		getSyncCollection(self.parentUuid).objects.link(empty)
		empty.empty_display_type = "PLAIN_AXES"

class SyncedCameraObject(SyncedXmlObject):
	# syncable props: pos.position?, tar.position?, Rotation_X/Y/Z, Fovy
	assumedAspectRatio = 16/9

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parent: SyncedXmlObject|None, allowReparent: bool):
		super().__init__(uuid, xml, nameHint, parent, allowReparent)
		self.makeCameraObject()
		self.updateWithXml(self.xml)
	
	def updateWithXml(self, xmlRoot: Element):
		camRoot: bpy.types.Object = findObject(self.uuid)
		camTarget: bpy.types.Object = camRoot.children[0]
		
		posE = xmlRoot.find("pos").find("position")
		tarE = xmlRoot.find("tar").find("position")
		rotXE = xmlRoot.find("Rotation_X")
		rotYE = xmlRoot.find("Rotation_Y")
		rotZE = xmlRoot.find("Rotation_Z")
		fovyE = xmlRoot.find("Fovy")

		if posE is not None:
			position = xmlVecToVec3(posE.text)
		else:
			position = (0, 0, 0)
		if tarE is not None:
			target = xmlVecToVec3(tarE.text)
		else:
			target = (0, 0, 0)
		rotX = strToFloat(rotXE.text)
		rotY = radians(-strToFloat(rotZE.text))
		rotZ = strToFloat(rotYE.text)
		fovy = strToFloat(fovyE.text)

		camRoot.location = position
		camRoot.rotation_euler = Euler((rotX, rotY, rotZ))
		camRoot.data.angle = radians(fovy) * self.assumedAspectRatio
		# global location to local location
		bpy.context.view_layer.update()
		camTarget.location = camRoot.matrix_world.inverted() @ Vector(target)

	def selfToXml(self) -> Element:
		rootCopy = deepcopy(self.xml)
		camRoot: bpy.types.Object = findObject(self.uuid)
		camTarget: bpy.types.Object = camRoot.children[0]
		posE = rootCopy.find("pos")
		tarE = rootCopy.find("tar")
		rotXE = rootCopy.find("Rotation_X")
		rotYE = rootCopy.find("Rotation_Y")
		rotZE = rootCopy.find("Rotation_Z")
		fovyE = rootCopy.find("Fovy")

		position = vecToXmlVec3(camRoot.location)
		target = vecToXmlVec3(camRoot.matrix_world @ camTarget.location)
		rotX = camRoot.rotation_euler[0]
		rotY = camRoot.rotation_euler[1]
		rotZ = camRoot.rotation_euler[2]
		fovy = degrees(camRoot.data.angle / self.assumedAspectRatio)

		updateXmlChildWithStr(posE, "position", position)
		updateXmlChildWithStr(tarE, "position", target)
		rotXE.text = floatToStr(rotX)
		rotYE.text = floatToStr(rotZ)
		rotZE.text = floatToStr(degrees(-rotY))
		fovyE.text = floatToStr(fovy)

		return rootCopy

	def makeCameraObject(self):
		cam: bpy.types.Object = bpy.data.objects.new(self.nameHint or "camera", bpy.data.cameras.new(self.nameHint or "camera"))
		cam["uuid"] = self.uuid
		coll = makeSyncCollection(self.uuid, self.parentUuid, self.nameHint or "camera")
		coll.objects.link(cam)
		camTarget: bpy.types.Object = bpy.data.objects.new("cameraTarget", None)
		camTarget["uuid"] = self.uuid
		coll.objects.link(camTarget)
		camTarget.empty_display_type = "PLAIN_AXES"
		camTarget.parent = cam
		camTarget.location = (0, 0, 0)

_isInited = False
def initSyncedObjects():
	global _isInited
	if _isInited:
		return
	_isInited = True
	addOnMessageListener(onWsMsg)
	addOnWsEndListener(onWsEnd)
	bpy.app.handlers.depsgraph_update_post.append(onDepsgraphUpdate)

def unregisterSyncedObjects():
	bpy.app.handlers.depsgraph_update_post.remove(onDepsgraphUpdate)
	disconnectFromWebsocket()
