import bpy
import xml.etree.ElementTree as ET
from typing import List
from ..common.bxm import xmlToBxm
from ...utils.xmlIntegrationUtils import objPosToXmlVec4, floatToStr, vecToXmlVec4, transferXmlPropsToXml
from ...utils.util import getChildrenInOrder


def getChildByStr(obj: bpy.types.Object, name: str) -> bpy.types.Object:
	for child in obj.children:
		if name in child.name:
			return child
	return None

# <Shape ShapeType="0" WorkType="0" Pos="933.734 34.0273 -351.43 -1" EdgeRadius="50" CoreRadius="0" />
def handleSphere(shapeObj: bpy.types.Object, shapeElement: ET.Element) -> None:
	coreSphereObj = getChildByStr(shapeObj, "Core-Sphere")
	edgeSphereObj = getChildByStr(shapeObj, "Edge-Sphere")
	shapeElement.attrib["Pos"] = objPosToXmlVec4(coreSphereObj)
	shapeElement.attrib["CoreRadius"] = floatToStr(coreSphereObj.scale[0])
	shapeElement.attrib["EdgeRadius"] = floatToStr(edgeSphereObj.scale[0])

# <Shape ShapeType="1" WorkType="0" EdgeRadius="30" CoreRadius="0" IsLoop="0">
# 	<Point Pos="209.823 13.4794 -289.055 1" />
# 	<Point Pos="210.713 10.9276 -293.882 2" />
# 	<Point Pos="227.58 6.93472 -304.964 8" />
# </Shape>
def handleCurve(shapeObj: bpy.types.Object, shapeElement: ET.Element) -> None:
	coreCurveObj = getChildByStr(shapeObj, "Core-Curve")
	edgeCurveObj = getChildByStr(shapeObj, "Edge-Curve")
	shapeElement.attrib["EdgeRadius"] = floatToStr(edgeCurveObj.data.bevel_depth)
	shapeElement.attrib["CoreRadius"] = floatToStr(coreCurveObj.data.bevel_depth)

	allPosW: List[float] = coreCurveObj["allPosW"]
	allPointLocations = []
	for i, point in enumerate(coreCurveObj.data.splines[0].points):
		w = allPosW[i] if i < len(allPosW) else allPosW[-1]
		allPointLocations.append(point.co[:3] + (w,))
	
	if shapeElement.attrib["IsLoop"] == "1":
		del allPointLocations[-1]
	
	for point in allPointLocations:
		pointElement = ET.SubElement(shapeElement, "Point")
		pointElement.attrib["Pos"] = vecToXmlVec4(point)

# <Shape ShapeType="2" WorkType="0" Origin="-455.743 15.9309 -420.493 3" Rot="-0.174905 -2.27877 0 1" EdgeRadius="50" CoreRadius="1" IsLoop="0">
# 	<Point Pos="0 0 0 1" Height="19.0856" />
# 	<Point Pos="4.99757 0.407875 -2.30815 0" Height="19.092" />
# 	<Point Pos="11.0426 0.175317 -0.992114 0" Height="20.123" />
# </Shape>
def handleShapeTallCurve(shapeObj: bpy.types.Object, shapeElement: ET.Element) -> None:
	shapeElement.attrib["Origin"] = objPosToXmlVec4(shapeObj)
	shapeElement.attrib["Rot"] = vecToXmlVec4(shapeObj.rotation_euler[:] + (1,))

	meshObj = getChildByStr(shapeObj, "Core-Tall-Curve")
	radius = meshObj.modifiers["Solidify"].thickness
	shapeElement.attrib["CoreRadius"] = floatToStr(radius / 2)

	# pos height data is in mesh faces
	allPosW: List[float] = shapeObj["allPosW"]
	vertices = meshObj.data.vertices
	if shapeElement.attrib["IsLoop"] == "1":
		del allPosW[-1]
		del allPosW[-1]
	
	isReversed = False
	for i in range(int(len(vertices) / 2)):
		if isReversed:
			pos = meshObj.data.vertices[i * 2 + 1].co
			height = meshObj.data.vertices[i * 2].co[2] - pos[2]
		else:
			pos = meshObj.data.vertices[i * 2].co
			height = meshObj.data.vertices[i * 2 + 1].co[2] - pos[2]
		w = allPosW[i] if i < len(allPosW) else allPosW[-1]
		pos = pos[:3] + (w,)
		pointElement = ET.SubElement(shapeElement, "Point")
		pointElement.attrib["Pos"] = vecToXmlVec4(pos)
		pointElement.attrib["Height"] = floatToStr(height)
		isReversed = not isReversed


# <Shape ShapeType="10" WorkType="0" Origin="945.463 10.5621 -365.603 4.50049" Rot="0 0.529685 0 1" Size="59.6161 21.8511 35.5307 1" DepthTop="0" DepthBottom="0" DepthSide="0 0 0 0" />
def handleCube(shapeObj: bpy.types.Object, shapeElement: ET.Element) -> None:
	cube = getChildByStr(shapeObj, "Cube")
	shapeElement.attrib["Origin"] = objPosToXmlVec4(cube)
	shapeElement.attrib["Rot"] = vecToXmlVec4(cube.rotation_euler[:] + (1,))
	shapeElement.attrib["Size"] = vecToXmlVec4(cube.scale[:] + (1,))

# <Shape ShapeType="100" WorkType="0" Origin="-8.4962 -104.472 -517.295 2.25244e+011" Rot="0 -1.19805 0 1" Size="10.8398 8 0.1 1" />
def handleSphereStretched(shapeObj: bpy.types.Object, shapeElement: ET.Element) -> None:
	sphere = getChildByStr(shapeObj, "Sphere")
	loc = list(sphere.location)
	scale = sphere.scale[:] + (1,)
	loc[0] += scale[1] / 2
	loc[1] += scale[0] / 2
	loc[2] -= scale[2] / 2
	loc += [sphere["posW"]]
	shapeElement.attrib["Origin"] = vecToXmlVec4(loc)
	shapeElement.attrib["Rot"] = vecToXmlVec4(sphere.rotation_euler[:] + (1,))
	shapeElement.attrib["Size"] = vecToXmlVec4(scale)

# <Shape ShapeType="15" WorkType="0" Origin="500.583 -44.6082 -166.047 -3.59599e+013" Rot="0 0 0 1" EdgeRadius="100" CoreRadius="10" Height="100" DepthTop="0" DepthBottom="0" />
def handleCylinder(shapeObj: bpy.types.Object, shapeElement: ET.Element) -> None:
	coreCylinder = getChildByStr(shapeObj, "Core-Cylinder")
	edgeCylinder = getChildByStr(shapeObj, "Edge-Cylinder")
	height = coreCylinder.data.extrude
	loc = list(coreCylinder.location)[:3]
	loc[2] -= height / 2
	loc += [coreCylinder["posW"]]
	coreRadius = coreCylinder.scale[0]
	edgeRadius = edgeCylinder.scale[0]
	shapeElement.attrib["Origin"] = vecToXmlVec4(loc)
	shapeElement.attrib["Rot"] = vecToXmlVec4(coreCylinder.rotation_euler[:] + (1,))
	shapeElement.attrib["EdgeRadius"] = floatToStr(edgeRadius)
	shapeElement.attrib["CoreRadius"] = floatToStr(coreRadius)
	shapeElement.attrib["Height"] = floatToStr(height)

# <Shape ShapeType="11" WorkType="0" Origin="538.154 -28.5174 -488.861 2.5" Rot="0.0946439 0.103248 0 1" Height="14.411" DepthTop="10" DepthBottom="0">
# 	<Point Pos="0 0 0 1" Depth="0" />
# 	<Point Pos="-3.13521 0 5.45735 2" Depth="0" />
# 	<Point Pos="15.3979 0 12.4781 1" Depth="0" />
# 	<Point Pos="16.505 0 3.42961 2" Depth="0" />
# </Shape>
def handlePolygonExtruded(shapeObj: bpy.types.Object, shapeElement: ET.Element) -> None:
	polyObj = getChildByStr(shapeObj, "PolygonExtruded")
	height = polyObj.modifiers["Solidify"].thickness

	shapeElement.attrib["Origin"] = objPosToXmlVec4(shapeObj)
	shapeElement.attrib["Rot"] = vecToXmlVec4(shapeObj.rotation_euler[:] + (1,))
	shapeElement.attrib["Height"] = floatToStr(height)

	# points in vertices
	vertices = polyObj.data.vertices
	allPosW: List[float] = polyObj["allPosW"]
	allDepth: List[float] = polyObj["allDepth"]
	for i in range(len(vertices)):
		pointElement = ET.SubElement(shapeElement, "Point")
		w = allPosW[i] if i < len(allPosW) else allPosW[-1]
		depth = allDepth[i] if i < len(allDepth) else allDepth[-1]
		pointElement.attrib["Pos"] = vecToXmlVec4(vertices[i].co[:3] + (w,))
		pointElement.attrib["Depth"] = floatToStr(depth)

# <Shape ShapeType="200" WorkType="0" Origin="664.479 -59.7746 -333.469 2.5" Rot="0 1.61465 0 1">
# 	<!-- List of sphares that create of volume when connected (loft) -->
# 	<Point RightPos="0 0 0 1" LeftPos="11.4518 0 0.160929 1" Height="8" Param="0" />
# 	<Point RightPos="-0.117254 0 5.11685 2" LeftPos="11.3345 0 5.27777 2" Height="8" Param="60" />
# 	<Point RightPos="-0.0804682 0 8.7414 3" LeftPos="11.3736 0 8.84134 3" Height="8" Param="60" />
# 	<Point RightPos="-0.0512033 0 10.8302 4" LeftPos="11.4029 0 10.9302 4" Height="8" Param="100" />
# 	<Point RightPos="2.08775 0 14.9255 1" LeftPos="9.49098 0 14.7633 1" Height="8" Param="100" />
# </Shape>
def handleLoftedVolume(shapeObj: bpy.types.Object, shapeElement: ET.Element) -> None:
	shapeElement.attrib["Origin"] = objPosToXmlVec4(shapeObj)
	shapeElement.attrib["Rot"] = vecToXmlVec4(shapeObj.rotation_euler[:] + (1,))
	
	for point in getChildrenInOrder(shapeObj):
		pointXml = ET.SubElement(shapeElement, "Point")
		
		allPosW = point["allPosW"]
		leftPos = point.data.vertices[0].co[:] + (allPosW[0],)
		rightPos = point.data.vertices[1].co[:] + (allPosW[1],)
		geometryNodeTree = point.modifiers[0].node_group
		heightIdentifier = geometryNodeTree.inputs[1].identifier
		height = point.modifiers[0][heightIdentifier]

		pointXml.attrib["RightPos"] = vecToXmlVec4(rightPos)
		pointXml.attrib["LeftPos"] = vecToXmlVec4(leftPos)
		pointXml.attrib["Height"] = floatToStr(height)
		pointXml.attrib["Param"] = point["xml-Param"]


def handleShapeObj(shapeObj: bpy.types.Object, shapeElement: ET.Element):
	type = shapeObj["xml-ShapeType"]
	if type == "0":	# no points (sphere?)
		handleSphere(shapeObj, shapeElement)
	elif type == "1":		# list of points with Pos
		handleCurve(shapeObj, shapeElement)
	elif type == "2":		# list of points with Pos and Depth
		handleShapeTallCurve(shapeObj, shapeElement)
	elif type == "10":	# no points (cube?)
		handleCube(shapeObj, shapeElement)
	elif type == "11":	# polygon with height
		handlePolygonExtruded(shapeObj, shapeElement)
	elif type == "15": # cylinder
		handleCylinder(shapeObj, shapeElement)
	elif type == "100": # no points (sphere?) (stretched)
		handleSphereStretched(shapeObj, shapeElement)
	elif type == "200":	# 2 points with rightPos, leftPos, height, param
		handleLoftedVolume(shapeObj, shapeElement)
	else:
		print(f"Unknown shape type {type}")
		unknownTypeXml = ET.parse(shapeObj["unknownShape"])
		for child in unknownTypeXml.getroot():
			shapeElement.append(child)

def exportSar(file: str):
	print("Exporting sar")

	if "Field-Root" not in bpy.data.objects:
		raise "No Field-Root in scene"
	
	xmlRoot = ET.Element("Field")
	root = bpy.data.objects["Field-Root"]
	transferXmlPropsToXml(root, xmlRoot)

	layers = getChildrenInOrder(root)
	for layer in layers:
		layerXml = ET.SubElement(xmlRoot, "Layer")
		transferXmlPropsToXml(layer, layerXml)
		
		for shapeGroup in getChildrenInOrder(layer):
			shapeGroupXml = ET.SubElement(layerXml, "ShapeGroup")
			transferXmlPropsToXml(shapeGroup, shapeGroupXml)

			for shape in getChildrenInOrder(shapeGroup):
				shapeXml = ET.SubElement(shapeGroupXml, "Shape")
				transferXmlPropsToXml(shape, shapeXml)
				handleShapeObj(shape, shapeXml)

	xmlToBxm(xmlRoot, file)

	print("Done!")
