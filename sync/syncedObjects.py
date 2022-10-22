
import re
from xml.etree import ElementTree

import bpy
from mathutils import Euler, Vector
from ..utils.util import throttle
from ..lay.importer.lay_importer import updateVisualizationObject
from .syncClient import SyncMessage, disconnectFromWebsocket, sendMsgToServer, addOnMessageListener
from .shared import SyncObjectsType, getDisableDepsgraphUpdates, setDisableDepsgraphUpdates
from .utils import findObject, newObjFromType
from ..utils.xmlIntegrationUtils import vecToXmlVec3, vecToXmlVec3Scale, xmlVecToVec3, xmlVecToVec3Scale
from xml.etree.ElementTree import Element, SubElement

class SyncedObject:
	uuid: str
	xml: Element
	objName: str

	def __init__(self, uuid: str, xml: Element, nameHint: str|None):
		self.uuid = uuid
		self.xml = xml
		self.objName = (nameHint or "") + " " + uuid
	
	@classmethod
	def fromType(cls, msg: SyncMessage):
		uuid = msg.uuid
		type = SyncObjectsType[msg.args["type"]]
		xml = ElementTree.fromstring(msg.args["propXml"])
		nameHint = msg.args["nameHint"]
		if type == "entity":
			return SyncedEntityObject(uuid, xml, nameHint)
		raise NotImplementedError()

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
		raise NotImplementedError()
	
	def updateWithXml(self, xmlRoot: Element):
		raise NotImplementedError()
	
	def selfToXml(self) -> Element:
		raise NotImplementedError()
	
	def hasChanged(self) -> bool:
		return not self.xmlCmp(self.xml, self.selfToXml())
	
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
	
	def endSync(self):
		sendMsgToServer(SyncMessage("endSync", self.uuid, {}))
		obj = findObject(self.objName, self.uuid)
		if obj is not None:
			bpy.data.objects.remove(obj)

class SyncedEntityObject(SyncedObject):
	# syncable props: location{ position, rotation?, }, scale?, objId

	def __init__(self, uuid: str, xml: Element, nameHint: str|None):
		objId = xml.find("objId").text
		super().__init__(uuid, xml, objId)
		newObjFromType(SyncObjectsType["entity"], self.objName, modelName=self.xml.find("objId").text)
		self.updateWithXml(self.xml)

	def update(self, msg: SyncMessage):
		xmlStr  = msg.args["propXml"]
		xmlRoot = ElementTree.fromstring(xmlStr)
		if not self.xmlCmp(self.xml, xmlRoot):
			print(f"updating {self.uuid}")
			self.updateWithXml(xmlRoot)
	
	def updateWithXml(self, xmlRoot: Element):
		prevObjId = self.xml.find("objId").text
		objId = xmlRoot.find("objId").text
		self.xml = xmlRoot
		obj = findObject(self.objName, self.uuid)
		if not obj:
			obj = newObjFromType(SyncObjectsType["entity"], self.objName, modelName=objId)
		elif objId != prevObjId:
			# update model
			updateVisualizationObject(obj, objId, False)
			# update name
			self.objName = objId + self.objName[len(prevObjId):]
			obj.name = self.objName

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
		root = Element("value")
		obj = findObject(self.objName, self.uuid)
		
		location = SubElement(root, "location")
		SubElement(location, "position").text = vecToXmlVec3(obj.location)
		if obj.rotation_euler != Euler((0, 0, 0)):
			SubElement(location, "rotation").text = vecToXmlVec3(obj.rotation_euler)
		if obj.scale != Vector((1, 1, 1)):
			SubElement(root, "scale").text = vecToXmlVec3Scale(obj.scale)
		
		objId = obj.name.split(" ")[0]
		if re.match(r"[a-z]{2}[a-f0-9]{4}", objId):
			SubElement(root, "objId").text = objId
		else:
			SubElement(root, "objId").text = self.xml.find("objId").text

		return root

	def onChanged(self):
		obj = findObject(self.objName, self.uuid)
		if obj is not None and bpy.data.objects.get(self.objName) is None:
			# name was changed
			self.objName = obj.name
			updateVisualizationObject(obj, obj.name.split(" ")[0], False)
		super().onChanged()
		

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
			syncedObjects[msg.uuid].endSync()
			del syncedObjects[msg.uuid]

	setDisableDepsgraphUpdates(False)

def onDepsgraphUpdate(scene: bpy.types.Scene):
	global syncedObjects
	if getDisableDepsgraphUpdates():
		return
	for syncObj in list(syncedObjects.values()):
		if findObject(syncObj.objName, syncObj.uuid) is None:
			syncObj.endSync()
			del syncedObjects[syncObj.uuid]
		elif syncObj.hasChanged():
			syncObj.onChanged()

def initSyncedObjects():
	addOnMessageListener(onWsMsg)
	bpy.app.handlers.depsgraph_update_post.append(onDepsgraphUpdate)

def unregisterSyncedObjects():
	bpy.app.handlers.depsgraph_update_post.remove(onDepsgraphUpdate)
	disconnectFromWebsocket()

