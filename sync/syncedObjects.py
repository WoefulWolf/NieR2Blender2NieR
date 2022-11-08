
from copy import deepcopy
import re
import time
from xml.etree import ElementTree

import bpy
from mathutils import Euler, Vector
from ..utils.util import throttle
from ..lay.importer.lay_importer import updateVisualizationObject
from .syncClient import SyncMessage, addOnWsEndListener, disconnectFromWebsocket, sendMsgToServer, addOnMessageListener
from .shared import SyncObjectsType, getDisableDepsgraphUpdates, setDisableDepsgraphUpdates
from .utils import findObject, getSyncCollection
from ..utils.xmlIntegrationUtils import floatToStr, makeSphereMesh, strToFloat, vecToXmlVec3, vecToXmlVec3Scale, xmlVecToVec3, xmlVecToVec3Scale
from ..dat_dtt.exporter.datHashGenerator import crc32
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
		elif type == "area":
			return SyncedAreaObject(uuid, xml, nameHint)
		elif type == "bezier":
			return SyncedBezierObject(uuid, xml, nameHint)
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
		xmlStr  = msg.args["propXml"]
		xmlRoot = ElementTree.fromstring(xmlStr)
		if not self.xmlCmp(self.xml, xmlRoot):
			print(f"updating {self.uuid}")
			self.updateWithXml(xmlRoot)
	
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
		del syncedObjects[self.uuid]

class SyncedEntityObject(SyncedObject):
	# syncable props: location{ position, rotation?, }, scale?, objId

	def __init__(self, uuid: str, xml: Element, nameHint: str|None):
		objId = xml.find("objId").text
		super().__init__(uuid, xml, objId)
		self.newObjFromType(SyncObjectsType["entity"], self.objName, modelName=self.xml.find("objId").text)
		self.updateWithXml(self.xml)

	def updateWithXml(self, xmlRoot: Element):
		prevObjId = self.xml.find("objId").text
		objId = xmlRoot.find("objId").text
		self.xml = xmlRoot
		obj = findObject(self.objName, self.uuid)
		if not obj:
			obj = self.newObjFromType(SyncObjectsType["entity"], self.objName, modelName=objId)
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
	
	@classmethod
	def newObjFromType(cls, type: int, name: str, modelName: str) -> bpy.types.Object:
		obj = bpy.data.objects.new(name, None)
		getSyncCollection().objects.link(obj)

		if type == SyncObjectsType["entity"]:
			updateVisualizationObject(obj, modelName, False)
		else:
			raise NotImplementedError(f"Object type {type} not implemented")
		
		return obj

class SyncedAreaObject(SyncedObject):
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

	def __init__(self, uuid: str, xml: Element, nameHint: str|None):
		super().__init__(uuid, xml, None)
		self.newAreaObjectFromType(int(xml.find("code").text, 16))
		self.updateWithXml(self.xml)
	
	def selfToXml(self) -> Element:
		root = Element("value")
		obj = findObject(self.objName, self.uuid)
		
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
		obj = findObject(self.objName, self.uuid)
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
		obj.color = self._objColor
		obj.show_wire = True
		getSyncCollection().objects.link(obj)

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

class SyncedBezierObject(SyncedObject):
	# syncable props: attribute, parent?, controls, nodes

	def __init__(self, uuid: str, xml: Element, nameHint: str|None):
		super().__init__(uuid, xml, nameHint)
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
		
		curve: bpy.types.Curve = findObject(self.objName, self.uuid).data
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
		obj = findObject(self.objName, self.uuid)
		
		curve: bpy.types.Curve = findObject(self.objName, self.uuid).data
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

	# def onChanged(self):
	# 	super().onChanged()
	
	def makeBezierObject(self):
		curve: bpy.types.Curve = bpy.data.curves.new(self.objName, "CURVE")
		curveObj = bpy.data.objects.new(self.objName, curve)
		getSyncCollection().objects.link(curveObj)

		curve.dimensions = "3D"
		curve.splines.new(type="BEZIER")

		curve.bevel_mode = "ROUND"
		curve.bevel_depth = 0.1
		curve.bevel_resolution = 8

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

	setDisableDepsgraphUpdates(False)

def onWsEnd():
	global syncedObjects
	for syncObj in list(syncedObjects.values()):
		syncObj.endSync()
	syncedObjects.clear()

@throttle(10)
def onDepsgraphUpdate(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
	global syncedObjects
	if getDisableDepsgraphUpdates():
		return
	for syncObj in list(syncedObjects.values()):
		if findObject(syncObj.objName, syncObj.uuid) is None:
			syncObj.endSync()
		elif syncObj.hasChanged():
			syncObj.onChanged()

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
