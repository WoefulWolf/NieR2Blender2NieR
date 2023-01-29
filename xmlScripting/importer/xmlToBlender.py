from typing import List
import bpy
import xml.etree.ElementTree as ET

from mathutils import Vector

from ...utils.xmlIntegrationUtils import makeBezier, makeCircleMesh, makeCube, makeEmptyObj, makeMeshObj, makeSphereObj, randomRgb, setCurrentCollection, strToFloat, tryAddCollection, xmlVecToVec3, getCurrentCollection
from ...lay.importer.lay_importer import updateVisualizationObject

yaxColl: bpy.types.Collection

def getNameOfThing(thing: ET.Element, prefix: str) -> str:
	nameEl = thing.find("name")
	if nameEl is not None:
		name = nameEl.attrib["eng"] if "eng" in nameEl.attrib else nameEl.text
		name = f"{prefix}-{name}"
	else:
		name = prefix
	return name

def importAreas(areasParent: ET.Element, color: List[float]):
	for i, areaObj in enumerate(areasParent.findall("value")):
		areaType = areaObj.find("code").text
		if areaType == "0x18cffd98":		# app::area::BoxArea
			loc = xmlVecToVec3(areaObj.find("position").text)
			rot = xmlVecToVec3(areaObj.find("rotation").text) if areaObj.find("rotation") is not None else (0, 0, 0)
			scale = xmlVecToVec3(areaObj.find("scale").text) if areaObj.find("scale") is not None else (1, 1, 1)
			scale[2] = abs(scale[2])
			points = areaObj.find("points").text.split(" ")
			points = map(lambda x: strToFloat(x), points)
			points = list(zip(*(iter(points),) * 2))
			height = strToFloat(areaObj.find("height").text)

			vertices = [ point + (0,) for point in points ]
			faces = [list(range(len(vertices)))]
			polyObj = makeMeshObj(f"{i}-BoxArea", vertices, [], faces, None, color)

			polyObj.location = loc
			polyObj.rotation_euler = rot
			polyObj.scale = scale
			
			solidifyMod = polyObj.modifiers.new("Solidify", "SOLIDIFY")
			solidifyMod.thickness = height
			solidifyMod.offset = 1
		elif areaType == "0x4238cc7f":		# app::area::CylinderArea
			loc = xmlVecToVec3(areaObj.find("position").text)
			rot = xmlVecToVec3(areaObj.find("rotation").text) if areaObj.find("rotation") is not None else (0, 0, 0)
			scale = xmlVecToVec3(areaObj.find("scale").text) if areaObj.find("scale") is not None else (1, 1, 1)
			radius = strToFloat(areaObj.find("radius").text)
			height = strToFloat(areaObj.find("height").text)

			cylinderObj = makeCircleMesh(f"{i}-CylinderArea", radius, None)

			cylinderObj.location = loc
			cylinderObj.rotation_euler = rot
			cylinderObj.scale = Vector(scale) * 2

			solidifyMod = cylinderObj.modifiers.new("Solidify", "SOLIDIFY")
			solidifyMod.thickness = height
			solidifyMod.offset = 1
		else:
			raise Exception(f"Unknown area type: {areaType}")

def importAreaCommand(action: ET.Element, color: List[float], prefix: str):
	return
	importAreas(action.find("area"), color)

def importSandstormAction(action: ET.Element, prefix: str):
	setCurrentCollection(tryAddCollection(getNameOfThing(action, f"{prefix}-Action"), yaxColl))
	area = action.find("hitArea")
	importAreas(area, (252/255, 186/255, 3/255, 0.5))

def importEnemyGenerator(action: ET.Element, color: List[float], prefix: str):
	setCurrentCollection(tryAddCollection(getNameOfThing(action, f"{prefix}-Action"), yaxColl))
	points = action.find("points")
	for i, point in enumerate(points.find("nodes").findall("value")):
		loc = xmlVecToVec3(point.find("point").text)
		radius = strToFloat(point.find("radius").text)
		sphere = makeSphereObj(f"{i}-EnemyGenerator-Sphere", radius, None, color)
		sphere.location = loc
	
	# if action.find("area") is not None:
	# 	importArea(action.find("area"), color)
	# if action.find("resetArea") is not None:
	# 	importArea(action.find("resetArea"), color)
	# if action.find("escapeArea") is not None:
	# 	importArea(action.find("escapeArea"), color)

def importEntities(action: ET.Element, color: List[float], prefix: str) -> None:
	setCurrentCollection(tryAddCollection(getNameOfThing(action, f"{prefix}-Action"), yaxColl))

	for i, entity in enumerate(action.find("layouts").find("normal").find("layouts").findall("value")):
		entityId = entity.find("id").text
		loc = xmlVecToVec3(entity.find("location").find("position").text) if entity.find("location").find("position") is not None else (0, 0, 0)
		rot = xmlVecToVec3(entity.find("location").find("rotation").text) if entity.find("location").find("rotation") is not None else (0, 0, 0)
		scale = xmlVecToVec3(entity.find("scale").text) if entity.find("scale") is not None else (1, 1, 1)
		entityObjId = entity.find("objId").text if entity.find("objId") is not None else entity.find("objID").text

		entityObj = makeEmptyObj(f"{i}-{entityObjId}-{entityId}", None)
		
		updateVisualizationObject(entityObj, entityObjId, False)
		
		entityObj.location = loc
		entityObj.rotation_euler = rot
		entityObj.scale = scale

def importBezier(action: ET.Element, color: List[float], prefix: str) -> None:
	setCurrentCollection(tryAddCollection(getNameOfThing(action, f"{prefix}-Action"), yaxColl))

	curveData = action.find("curve")
	points = curveData.find("nodes").findall("value")
	points = [xmlVecToVec3(point.find("point").text) for point in points]
	
	handles = curveData.find("controls").findall("value")
	handles = [val.find("cp").text.split(" ") for val in handles]
	leftHandles = [xmlVecToVec3(" ".join(handle[:3])) for handle in handles]
	rightHandles = [xmlVecToVec3(" ".join(handle[3:])) for handle in handles]
	for i, invHandle in enumerate(leftHandles):
		vecToPoint = Vector(points[i]) - Vector(invHandle)
		leftHandles[i] = Vector(points[i]) + vecToPoint
	
	loopFlag = int(curveData.find("attribute").text, 16) & 0xF
	if loopFlag != 4 or loopFlag != 5:
		print(f"Unknown loop flag: {loopFlag}")
	loops = loopFlag == 5
	makeBezier(f"{prefix}-Bezier", points, leftHandles, rightHandles, loops, None, 0.1, color)

def importPathCamera(action: ET.Element, color: List[float], prefix: str) -> None:
	setCurrentCollection(tryAddCollection(getNameOfThing(action, f"{prefix}-Action"), yaxColl))

	routePoints = action.find("route").find("nodes").findall("value")
	routePoints = [xmlVecToVec3(point.find("point").text) for point in routePoints]

	curve = makeBezier(f"{prefix}-CameraPath-Route", routePoints, None, None, False, None, 0.1, color)
	curveData: bpy.types.Curve = curve.data
	for point in curveData.splines[0].bezier_points:
		point.handle_left_type = "AUTO"
		point.handle_right_type = "AUTO"

	playerPathPoints = action.find("playerPath").find("nodes").findall("value")
	playerPathPoints = [xmlVecToVec3(point.find("point").text) for point in playerPathPoints]

	curve = makeBezier(f"{prefix}-CameraPath-PlayerPath", playerPathPoints, None, None, False, None, 0.1, color)
	curveData: bpy.types.Curve = curve.data
	for point in curveData.splines[0].bezier_points:
		point.handle_left_type = "AUTO"
		point.handle_right_type = "AUTO"

def importXml(root: ET.Element, prefix: str) -> None:
	global yaxColl

	yaxName = getNameOfThing(root, prefix)
	print(f"Importing {yaxName}")
	yaxRootColl = tryAddCollection("YAX", bpy.context.scene.collection)
	yaxColl = tryAddCollection(yaxName, yaxRootColl)
	setCurrentCollection(yaxColl)
	color = randomRgb(yaxName) + [0.5]

	actionsImported = False
	for action in root.findall("action"):
		actionCode = action.find("code").text
		if actionCode in ["0x58534a9e", "0x8cf2e32", "0x1571c131"]:
			# area command
			importAreaCommand(action, color, prefix)
			actionsImported = True
		elif actionCode == "0x6f0fb5bd":	# enemy generator
			importEnemyGenerator(action, color, prefix)
			actionsImported = True
		elif actionCode in {"0xda948617", "0xcf775473", "0xfb085793", "0xe8fefe4b"}:	# EntityLayoutAction, EntityLayoutArea, EnemySetAction, EnemySetArea
			importEntities(action, color, prefix)
			actionsImported = True
		elif actionCode == "0x5874fcd9":	# bezier
			importBezier(action, color, prefix)
			actionsImported = True
		elif actionCode == "0xf0213c66":
			importPathCamera(action, color, prefix)
			actionsImported = True
		elif actionCode == "0x3ff17a64":	# HapSandStormAreaAction
			importSandstormAction(action, prefix)
			actionsImported = True
		else:
			...
		
		if action.find("area") is not None:
			# area command
			importAreas(action.find("area"), color)
			actionsImported = True
	
	if not actionsImported:
		bpy.data.collections.remove(yaxColl)
