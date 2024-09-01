import os
import bpy

from ..common.bxm import *
from ...utils.xmlIntegrationUtils import xmlVecToVec3, makeSphereObj, strToFloat, setObjPosFromXmlPos, makeCurve, \
	xmlVecToVec4, makeMeshObj, makeCube, makeCircle, setXmlAttributesOnObj, tryAddEmpty, randomRgb, tryAddCollection, \
	setCurrentCollection
from ...utils.util import newGeometryNodesModifier, setViewportColorTypeToObject
from ..common.approxMapOffsets import approxMapOffsets

class HandleShapeParams:
	shape: ET.Element
	parentObj: bpy.types.Object
	parentId: str
	color: List[float]

	def __init__(self, shape: ET.Element, parentObj: bpy.types.Object, parentId: str, color: List[float]):
		self.shape = shape
		self.parentObj = parentObj
		self.parentId = parentId
		self.color = color

# <Shape ShapeType="0" WorkType="0" Pos="933.734 34.0273 -351.43 -1" EdgeRadius="50" CoreRadius="0" />
def handleSphere(params: HandleShapeParams) -> None:
	shape = params.shape
	parentObj = params.parentObj
	parentId = params.parentId
	color = params.color

	parentObj.hide_set(True)
	coreSphere = makeSphereObj(
		f"Core-Sphere-{parentId}",
		strToFloat(shape.attrib["CoreRadius"]),
		parentObj,
		color
	)
	setObjPosFromXmlPos(coreSphere, shape.attrib["Pos"])
	edgeSphere = makeSphereObj(
		f"Edge-Sphere-{parentId}",
		strToFloat(shape.attrib["EdgeRadius"]),
		parentObj,
		color[:3] + [0.1]
	)
	setObjPosFromXmlPos(edgeSphere, shape.attrib["Pos"])

# <Shape ShapeType="1" WorkType="0" EdgeRadius="30" CoreRadius="0" IsLoop="0">
# 	<Point Pos="209.823 13.4794 -289.055 1" />
# 	<Point Pos="210.713 10.9276 -293.882 2" />
# 	<Point Pos="227.58 6.93472 -304.964 8" />
# </Shape>
def handleCurve(params: HandleShapeParams) -> None:
	shape = params.shape
	parentObj = params.parentObj
	parentId = params.parentId
	color = params.color

	parentObj.hide_set(True)

	makeCurve(
		f"Core-Curve-{parentId}",
		[xmlVecToVec4(point.attrib["Pos"]) for point in shape],
		strToFloat(shape.attrib["CoreRadius"]),
		shape.attrib["IsLoop"] == "1",
		parentObj,
		color
	)
	makeCurve(
		f"Edge-Curve-{parentId}",
		[xmlVecToVec4(point.attrib["Pos"]) for point in shape],
		strToFloat(shape.attrib["EdgeRadius"]),
		shape.attrib["IsLoop"] == "1",
		parentObj,
		color[:3] + [0.1]
	)

# <Shape ShapeType="2" WorkType="0" Origin="-455.743 15.9309 -420.493 3" Rot="-0.174905 -2.27877 0 1" EdgeRadius="50" CoreRadius="1" IsLoop="0">
# 	<Point Pos="0 0 0 1" Height="19.0856" />
# 	<Point Pos="4.99757 0.407875 -2.30815 0" Height="19.092" />
# 	<Point Pos="11.0426 0.175317 -0.992114 0" Height="20.123" />
# </Shape>
def handleShapeTallCurve(params: HandleShapeParams) -> None:
	shape = params.shape
	parentObj = params.parentObj
	parentId = params.parentId
	color = params.color

	setObjPosFromXmlPos(parentObj, shape.attrib["Origin"])
	parentObj.rotation_euler = xmlVecToVec3(shape.attrib["Rot"])

	points = shape.findall("Point")
	locations = [xmlVecToVec4(point.attrib["Pos"]) for point in points]
	parentObj["allPosW"] = [loc[3] for loc in locations]
	locations = [loc[:3] for loc in locations]

	# initialize first edge vertices
	topLoc = locations[0][:]
	topLoc[2] += strToFloat(points[0].attrib["Height"])
	vertices = [locations[0], topLoc]
	reverseOrder = True
	# add edge vertices
	for i, point in enumerate(points):
		if i == 0:
			continue
		topLoc = locations[i][:]
		topLoc[2] += strToFloat(point.attrib["Height"])
		if reverseOrder:
			vertices.extend([topLoc, locations[i]])
		else:
			vertices.extend([locations[i], topLoc])
		reverseOrder = not reverseOrder
	# make faces
	faces: List[List[float]] = []
	reverseOrder = False
	for i in range(int(len(vertices) / 2 - 1)):
		if reverseOrder:
			faces.append([i * 2 + 3, i * 2 + 2, i * 2 + 1, i * 2])
		else:
			faces.append([i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 3])
		reverseOrder = not reverseOrder

	curveLike = makeMeshObj(
		f"Core-Tall-Curve-{parentId}",
		vertices,
		[],
		faces,
		parentObj,
		color
	)

	# add solidify and bevel modifiers to display radius
	curveLike.modifiers.new("Solidify", type="SOLIDIFY")
	curveLike.modifiers["Solidify"].thickness = strToFloat(shape.attrib["CoreRadius"]) * 2
	curveLike.modifiers["Solidify"].offset = 0

	curveLike.modifiers.new("Bevel", type="BEVEL")
	curveLike.modifiers["Bevel"].width = strToFloat(shape.attrib["CoreRadius"])
	curveLike.modifiers["Bevel"].segments = 4


# <Shape ShapeType="10" WorkType="0" Origin="945.463 10.5621 -365.603 4.50049" Rot="0 0.529685 0 1" Size="59.6161 21.8511 35.5307 1" DepthTop="0" DepthBottom="0" DepthSide="0 0 0 0" />
def handleCube(params: HandleShapeParams) -> None:
	shape = params.shape
	parentObj = params.parentObj
	parentId = params.parentId
	color = params.color

	parentObj.hide_set(True)
	cubeObj = makeCube(
		f"Cube-{parentId}",
		parentObj,
		color
	)
	cubeObj.show_wire = True
	setObjPosFromXmlPos(cubeObj, shape.attrib["Origin"])
	cubeObj.rotation_euler = xmlVecToVec3(shape.attrib["Rot"])
	cubeObj.scale = xmlVecToVec3(shape.attrib["Size"])

# <Shape ShapeType="100" WorkType="0" Origin="-8.4962 -104.472 -517.295 2.25244e+011" Rot="0 -1.19805 0 1" Size="10.8398 8 0.1 1" />
def handleSphereStretched(params: HandleShapeParams) -> None:
	shape = params.shape
	parentObj = params.parentObj
	parentId = params.parentId
	color = params.color

	parentObj.hide_set(True)
	sphereObj = makeSphereObj(
		f"Sphere-{parentId}",
		0.5,
		parentObj,
		color
	)
	setObjPosFromXmlPos(sphereObj, shape.attrib["Origin"])
	sphereObj.rotation_euler = xmlVecToVec3(shape.attrib["Rot"])
	scale = xmlVecToVec3(shape.attrib["Size"])
	sphereObj.scale = scale
	sphereObj.location[0] -= scale[1] / 2
	sphereObj.location[1] -= scale[0] / 2
	sphereObj.location[2] += scale[2] / 2
	
# <Shape ShapeType="15" WorkType="0" Origin="500.583 -44.6082 -166.047 -3.59599e+013" Rot="0 0 0 1" EdgeRadius="100" CoreRadius="10" Height="100" DepthTop="0" DepthBottom="0" />
def handleCylinder(params: HandleShapeParams) -> None:
	shape = params.shape
	parentObj = params.parentObj
	parentId = params.parentId
	color = params.color

	parentObj.hide_set(True)
	coreCylinder = makeCircle(
		f"Core-Cylinder-{parentId}",
		1,
		parentObj,
		color
	)
	setObjPosFromXmlPos(coreCylinder, shape.attrib["Origin"])
	coreCylinder.rotation_euler = xmlVecToVec3(shape.attrib["Rot"])
	radius = strToFloat(shape.attrib["CoreRadius"])
	height = strToFloat(shape.attrib["Height"])
	coreCylinder.scale = [radius, radius, 1]
	curveData: bpy.types.Curve = coreCylinder.data
	curveData.extrude = height
	coreCylinder.location[2] += height / 2
	edgeCylinder = makeCircle(
		f"Edge-Cylinder-{parentId}",
		1,
		parentObj,
		color[:3] + [0.1]
	)
	setObjPosFromXmlPos(edgeCylinder, shape.attrib["Origin"])
	edgeCylinder.rotation_euler = xmlVecToVec3(shape.attrib["Rot"])
	radius = strToFloat(shape.attrib["EdgeRadius"])
	edgeCylinder.scale = [radius, radius, 1]
	curveData: bpy.types.Curve = edgeCylinder.data
	curveData.extrude = height
	edgeCylinder.location[2] += height / 2

# <Shape ShapeType="11" WorkType="0" Origin="538.154 -28.5174 -488.861 2.5" Rot="0.0946439 0.103248 0 1" Height="14.411" DepthTop="10" DepthBottom="0">
# 	<Point Pos="0 0 0 1" Depth="0" />
# 	<Point Pos="-3.13521 0 5.45735 2" Depth="0" />
# 	<Point Pos="15.3979 0 12.4781 1" Depth="0" />
# 	<Point Pos="16.505 0 3.42961 2" Depth="0" />
# </Shape>
def handlePolygonExtruded(params: HandleShapeParams) -> None:
	shape = params.shape
	parentObj = params.parentObj
	parentId = params.parentId
	color = params.color
	setObjPosFromXmlPos(parentObj, shape.attrib["Origin"])
	parentObj.rotation_euler = xmlVecToVec3(shape.attrib["Rot"])
	
	vertices = [
		xmlVecToVec4(point.attrib["Pos"])
		for point in shape.findall("Point")
	]
	allPosW = [loc[3] for loc in vertices]
	vertices = [loc[:3] for loc in vertices]
	faces = [list(range(len(vertices)))]
	polyObj = makeMeshObj(f"PolygonExtruded-{parentId}", vertices, [], faces, parentObj, color)
	polyObj.show_wire = True
	polyObj["allPosW"] = allPosW
	polyObj["allDepth"] = [strToFloat(point.attrib["Depth"]) for point in shape.findall("Point")]

	height = strToFloat(shape.attrib["Height"])
	solidifyMod = polyObj.modifiers.new("Solidify", "SOLIDIFY")
	solidifyMod.thickness = height
	solidifyMod.offset = 1

# <Shape ShapeType="200" WorkType="0" Origin="664.479 -59.7746 -333.469 2.5" Rot="0 1.61465 0 1">
# 	<!-- List of sphares that create of volume when connected (loft) -->
# 	<Point RightPos="0 0 0 1" LeftPos="11.4518 0 0.160929 1" Height="8" Param="0" />
# 	<Point RightPos="-0.117254 0 5.11685 2" LeftPos="11.3345 0 5.27777 2" Height="8" Param="60" />
# 	<Point RightPos="-0.0804682 0 8.7414 3" LeftPos="11.3736 0 8.84134 3" Height="8" Param="60" />
# 	<Point RightPos="-0.0512033 0 10.8302 4" LeftPos="11.4029 0 10.9302 4" Height="8" Param="100" />
# 	<Point RightPos="2.08775 0 14.9255 1" LeftPos="9.49098 0 14.7633 1" Height="8" Param="100" />
# </Shape>
def handleLoftedVolume(params: HandleShapeParams) -> None:
	shape = params.shape
	parentObj = params.parentObj
	parentId = params.parentId
	color = params.color
	setObjPosFromXmlPos(parentObj, shape.attrib["Origin"])
	parentObj.rotation_euler = xmlVecToVec3(shape.attrib["Rot"])

	for i, point in enumerate(shape.findall("Point")):
		# for each point create mesh with left & right pos vertices
		leftPos = xmlVecToVec4(point.attrib["LeftPos"])
		rightPos = xmlVecToVec4(point.attrib["RightPos"])
		pointObj = makeMeshObj(
			f"{i}-Point-{parentId}",
			[leftPos[:3], rightPos[:3]],
			[[0, 1]],
			[],
			parentObj,
			color
		)
		pointObj["allPosW"] = [leftPos[3], rightPos[3]]
		pointObj["xml-Param"] = point.attrib["Param"]
		pointObj.show_wire = True
		
		# with geometry nodes extrude to height
		geometryNodesMod: bpy.types.NodesModifier = newGeometryNodesModifier(pointObj)
		nodeTree = geometryNodesMod.node_group

		inputNode = nodeTree.nodes["Group Input"]
		outputNode = nodeTree.nodes["Group Output"]
		extrudeNode = nodeTree.nodes.new("GeometryNodeExtrudeMesh")
		combineXyzNode = nodeTree.nodes.new("ShaderNodeCombineXYZ")

		extrudeNode.mode = "EDGES"
		inputNode.outputs.new("VALUE", "Height")
		combineXyzNode.location = (-170, -140)

		nodeTree.links.new(inputNode.outputs["Geometry"], extrudeNode.inputs["Mesh"])
		nodeTree.links.new(extrudeNode.outputs["Mesh"], outputNode.inputs["Geometry"])
		nodeTree.links.new(inputNode.outputs["Height"], combineXyzNode.inputs["Z"])
		nodeTree.links.new(combineXyzNode.outputs["Vector"], extrudeNode.inputs["Offset"])

		heightIdentifier = nodeTree.inputs[1].identifier
		geometryNodesMod[heightIdentifier] = strToFloat(point.attrib["Height"])

encounteredShapes = set()
def handleShape(params: HandleShapeParams) -> None:
	global encounteredShapes
	type = params.shape.attrib["ShapeType"]
	encounteredShapes.add(type)

	if type == "0":			# no points (sphere?)
		handleSphere(params)
	elif type == "1":		# List of points with Pos
		handleCurve(params)
	elif type == "2":		# List of points with Pos & height
		handleShapeTallCurve(params)
	elif type == "10":		# no points (cube?)
		handleCube(params)
	elif type == "11":		# polygon with height
		handlePolygonExtruded(params)
	elif type == "15":		# Cylinder
		handleCylinder(params)
	elif type == "100":		# no points (sphere?) (stretched)
		handleSphereStretched(params)
	elif type == "200":		# points with rightPos, leftPos, height (volume in between faces?)
		handleLoftedVolume(params)
	else:
		print(f"Unknown shape type: {type}")
		params.parentObj["unknownShape"] = ET.tostring(params.shape)

def importSar(file: str, tryApplyingOffset: bool) -> None:
	global currentCollection
	global encounteredShapes
	encounteredShapes = set()

	print(f"Importing {file}")
	xml: ET.Element = bxmToXml(file)
	# write to file
	with open(file + ".xml", "wb") as f:
		f.write(ET.tostring(xml))
	assert(xml.tag == "Field")

	baseName = os.path.basename(file)
	tryAddCollection("SAR", bpy.context.scene.collection)
	setCurrentCollection(tryAddCollection(f"SAR_{baseName}", bpy.data.collections["SAR"]))

	tileName = baseName[:6]
	rootOffsets: bpy.types.Object = None
	globalOffsets: List[float] = None
	if tileName in approxMapOffsets:
		globalOffsets = approxMapOffsets[tileName][:]
		globalOffsets[0] *= -1
		globalOffsets[1] *= -1
	if globalOffsets and tryApplyingOffset:
		rootOffsets = tryAddEmpty(f"{tileName}-offset")
		rootOffsets.location = globalOffsets
		rootOffsets.hide_set(True)
	
	fieldRoot = tryAddEmpty("Field-Root", rootOffsets)
	fieldRoot.hide_set(True)
	setXmlAttributesOnObj(fieldRoot, xml)

	for lI, layer in enumerate(xml.findall("Layer")):
		layObj = tryAddEmpty(f"{lI}-Layer-{layer.attrib['Name']}", fieldRoot)
		layObj.hide_set(True)
		setXmlAttributesOnObj(layObj, layer)
		layerColor = randomRgb(layer.attrib["Name"]) + [0.5]

		for sgI, shapeGroup in enumerate(layer.findall("ShapeGroup")):
			shapeGroupObj = tryAddEmpty(f"{sgI}-ShapeGroup-/{lI}", layObj)
			shapeGroupObj.hide_set(True)
			setXmlAttributesOnObj(shapeGroupObj, shapeGroup)

			for sI, shape in enumerate(shapeGroup.findall("Shape")):
				shapeObj = tryAddEmpty(f"{sI}-Shape-Type={shape.attrib['ShapeType']}-/{lI}/{sgI}", shapeGroupObj)
				setXmlAttributesOnObj(shapeObj, shape)
				handleShape(HandleShapeParams(shape, shapeObj, f"{lI}-{sgI}-{sI}", layerColor))
	
	bpy.ops.object.select_all(action="DESELECT")
	bpy.context.view_layer.objects.active = None
	setViewportColorTypeToObject()

	print("Encountered Shapes:", encounteredShapes)
	print("Done!")
