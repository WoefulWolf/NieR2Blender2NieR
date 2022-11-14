from __future__ import annotations
from copy import deepcopy
import re
import time
from xml.etree import ElementTree
from uuid import uuid4

import bpy
from mathutils import Euler, Vector
from ..utils.util import throttle
from ..lay.importer.lay_importer import updateVisualizationObject
from .syncClient import SyncMessage, addOnWsEndListener, disconnectFromWebsocket, sendMsgToServer, addOnMessageListener
from .shared import SyncObjectsType, SyncUpdateType, getDisableDepsgraphUpdates, setDisableDepsgraphUpdates
from .utils import findObject, getSyncCollection, makeSyncCollection, updateXmlChildWithStr
from ..utils.xmlIntegrationUtils import floatToStr, makeSphereMesh, strToFloat, vecToXmlVec3, vecToXmlVec3Scale, xmlVecToVec3, xmlVecToVec3Scale
from ..dat_dtt.exporter.datHashGenerator import crc32
from xml.etree.ElementTree import Element, SubElement

syncedObjects: dict[str, SyncedObject] = {}

def onWsMsg(msg: SyncMessage):
	global syncedObjects
	setDisableDepsgraphUpdates(True)

	if msg.method == "update":
		if msg.uuid in syncedObjects:
			syncObj = syncedObjects[msg.uuid]
			syncObj.update(msg)
		else:
			sendMsgToServer(SyncMessage("endSync", msg.uuid, {}))
	elif msg.method == "startSync":
		newObj = SyncedObject.fromType(msg)
		syncedObjects[msg.uuid] = newObj
	elif msg.method == "endSync":
		if msg.uuid in syncedObjects:
			syncedObjects[msg.uuid].endSync(False)

	setDisableDepsgraphUpdates(False)

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
					processedObjectsOnDepsgraphUpdate.remove(obj.uuid)
			
			processedObjectsOnDepsgraphUpdate.remove(syncObj.uuid)
	
		for uuid in processedObjectsOnDepsgraphUpdate:
			# dangling objects
			print("dangling object", uuid)
			syncedObjects[uuid].endSync()
	finally:
		setDisableDepsgraphUpdates(False)

class SyncedObject:
	uuid: str
	nameHint: str|None = None
	parentUuid: str|None = None

	def __init__(self, uuid: str, nameHint: str|None, parentUuid: str|None):
		self.uuid = uuid
		self.nameHint = nameHint
		self.parentUuid = parentUuid
	
	@classmethod
	def fromType(cls, msg: SyncMessage):
		uuid = msg.uuid
		type = SyncObjectsType.fromInt(msg.args["type"])
		nameHint = msg.args.get("nameHint", None)
		parentUuid = msg.args.get("parentUuid", None)
		if type == SyncObjectsType.list:
			return SyncedListObject(uuid, msg, nameHint, parentUuid)
		else:
			xml = ElementTree.fromstring(msg.args["propXml"])
			if type == SyncObjectsType.entity:
				return SyncedEntityObject(uuid, xml, nameHint, parentUuid)
			elif type == SyncObjectsType.area:
				return SyncedAreaObject(uuid, xml, nameHint, parentUuid)
			elif type == SyncObjectsType.bezier:
				return SyncedBezierObject(uuid, xml, nameHint, parentUuid)
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
	
	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parentUuid: str|None):
		super().__init__(uuid, nameHint, parentUuid)
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
			bpy.data.objects.remove(obj)
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
	
	def __init__(self, uuid: str, msg: SyncMessage, nameHint: str|None, parentUuid: str|None):
		super().__init__(uuid, nameHint, parentUuid)
		self.listType = msg.args["listType"]
		self.objects = []
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
		removedObj = [obj for obj in self.objects if obj.uuid == uuid][0]
		self.objects.remove(removedObj)
		removedObj.endSync(False)
	
	def endSync(self, sendMsg: bool = True):
		if sendMsg:
			sendMsgToServer(SyncMessage("endSync", self.uuid, {}))
		collection = getSyncCollection(self.uuid)
		if collection is not None:
			bpy.data.collections.remove(collection)
		del syncedObjects[self.uuid]
		for obj in self.objects:
			obj.endSync(sendMsg)
	
	def hasChanged(self) -> bool:
		coll = getSyncCollection(self.uuid)
		if coll is None:
			raise Exception(f"Collection {self.uuid} not found")
		if len(coll.objects) != len(self.objects):
			return True
		blenderObjUuids = [obj["uuid"] for obj in coll.objects if "uuid" in obj]
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
				if repObjCollUuid is not None:
					self.handleObjectReparent(removedUuid)
					continue

			removeSyncObj = [obj for obj in self.objects if obj.uuid == removedUuid][0]
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
			addedObj = findObject(addedUuid)
			addedObjUuid = addedObj["uuid"]
			if addedObjUuid not in syncedObjects:
				print("added object not found in synced objects")
				continue
			self.handleObjectReparent(addedObjUuid)

	@staticmethod
	def handleObjectReparent(objUuid: str):
		syncObj = syncedObjects[objUuid]
		srcList = syncedObjects[syncObj.parentUuid]
		blenderObj = findObject(objUuid)
		objCollUuid = blenderObj.users_collection[0].get("uuid")
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

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parentUuid: str|None):
		objId = xml.find("objId").text
		super().__init__(uuid, xml, objId, parentUuid)
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

	_objColor = (0, 0, 1, 0.333)

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parentUuid: str|None):
		super().__init__(uuid, xml, nameHint, parentUuid)
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
			geometryNodesMod: bpy.types.NodesModifier = obj.modifiers.new("GeometryNodes", "NODES")
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

	def __init__(self, uuid: str, xml: Element, nameHint: str|None, parent: SyncedXmlObject|None):
		super().__init__(uuid, xml, nameHint, parent)
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
		bezierPoints = curve.splines.active.bezier_points

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
				bezierPoints.remove(bezierPoints[-1])
	
	def selfToXml(self) -> Element:
		rootCopy = deepcopy(self.xml)
		
		curve: bpy.types.Curve = findObject(self.uuid).data
		bezierCurvePoints = curve.splines.active.bezier_points
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
		minLen = min(curLen, len(root.findall("value")))
		for i in range(minLen):
			point = root.findall("value")[i].find(childTagName)
			point.text = newChildStrings[i]
		if curLen < len(root.findall("value")):
			for i in range(minLen, curLen):
				root.remove(root[-1])
		elif curLen > len(root.findall("value")):
			for i in range(len(root.findall("value")), curLen):
				newNode = deepcopy(root[-1])
				newNode.find(childTagName).text = newChildStrings[i]

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
