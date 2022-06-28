import bpy

from ..common.bxm import xmlToBxm
from ...utils.xmlIntegrationUtils import vecToXmlVec2, setXmlAttribAsElement, vecToXmlVec3, floatToStr
import xml.etree.ElementTree as ET
from ...utils.util import getChildrenInOrder

# <PrimitiveInfo>
# 	<Trans>-37.882129 -116.717265 691.357685</Trans>
# 	<Top>13.976493</Top>
# 	<Bottom>-247.411024</Bottom>
# 	<Point0>-53.809411 722.293589</Point0>
# 	<Point1>-53.809411 660.421781</Point1>
# 	<Point2>-21.954847 660.421781</Point2>
# 	<Point3>-21.954847 722.293589</Point3>
# </PrimitiveInfo>
def cubeToXml(cube: bpy.types.Object, primitiveInfo: ET.Element) -> None:
	loc = cube.location
	vertices = [v.co + loc for v in cube.data.vertices]
	points = [vecToXmlVec2(v) for v in vertices]
	bottom = vertices[0][2]
	height = cube.modifiers["Solidify"].thickness
	top = bottom + height

	setXmlAttribAsElement(primitiveInfo, "Trans", vecToXmlVec3(loc))
	setXmlAttribAsElement(primitiveInfo, "Top", floatToStr(top))
	setXmlAttribAsElement(primitiveInfo, "Bottom", floatToStr(bottom))

	for i, point in enumerate(points):
		setXmlAttribAsElement(primitiveInfo, f"Point{i}", point)


def exportGaArea(file: str):
	print("Exporting sar")

	if "GA_ALL" not in bpy.data.objects:
		raise "No GA_ALL in scene"
	
	xmlRoot = ET.Element("GA_ALL")
	gaRoot = bpy.data.objects["GA_ALL"]

	for ga in getChildrenInOrder(gaRoot):
		gaXml = ET.SubElement(xmlRoot, "GA")
		primitiveType = ga["xml-PrimitiveType"]
		graphicAdjustInfo = ET.SubElement(gaXml, "GraphicAdjustInfo")
		for key, value in ga.items():
			if not key.startswith("xml-GAI-"):
				continue
			setXmlAttribAsElement(graphicAdjustInfo, key[8:], value)
		setXmlAttribAsElement(gaXml, "PrimitiveType", hex(primitiveType))
		
		if primitiveType == 2:
			cubeToXml(ga, ET.SubElement(gaXml, "PrimitiveInfo"))
		else:
			raise "Unknown primitive type"

	xmlToBxm(xmlRoot, file)	

	print("Done!")
