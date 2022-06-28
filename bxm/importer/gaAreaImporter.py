from typing import List
import bpy
import xml.etree.ElementTree as ET

from ..common.bxm import bxmToXml
from ...utils.xmlIntegrationUtils import strToFloat, xmlVecToVec3, xmlVecToVec2, makeMeshObj, randomRgb, tryAddEmpty, \
	setCurrentCollection, tryAddCollection

# <PrimitiveInfo>
# 	<Trans>-37.882129 -116.717265 691.357685</Trans>
# 	<Top>13.976493</Top>
# 	<Bottom>-247.411024</Bottom>
# 	<Point0>-53.809411 722.293589</Point0>
# 	<Point1>-53.809411 660.421781</Point1>
# 	<Point2>-21.954847 660.421781</Point2>
# 	<Point3>-21.954847 722.293589</Point3>
# </PrimitiveInfo>
def addGaCube(parent: bpy.types.Object, xml: ET.Element, color: List[float]) -> bpy.types.Object:
	bottom = strToFloat(xml.find("Bottom").text)
	height = strToFloat(xml.find("Top").text) - bottom
	loc = xmlVecToVec3(xml.find("Trans").text)
	vertices = [
		xmlVecToVec2(point.text) + [bottom]
		for point in xml if point.tag.startswith("Point")
	]
	for vert in vertices:
		for i in range(3):
			vert[i] -= loc[i]
	faces = [list(range(len(vertices)))]
	obj = makeMeshObj("obj", vertices, [], faces, parent, color)
	obj.location = loc
	obj.show_wire = True

	solidifyMod = obj.modifiers.new("Solidify", "SOLIDIFY")
	solidifyMod.thickness = height
	solidifyMod.offset = -1

	return obj
	

def importGaArea(file: str) -> None:
	print(f"Importing {file}")
	xml: ET.Element = bxmToXml(file)
	# write to file
	# with open(file + ".xml", "wb") as f:
	# 	f.write(ET.tostring(xml))
	assert xml.tag == "GA_ALL"

	setCurrentCollection(tryAddCollection(f"GaArea", bpy.context.scene.collection))

	gaRoot = tryAddEmpty("GA_ALL")
	gaRoot.hide_set(True)
	for i, ga in enumerate(xml.findall("GA")):
		primitiveType = int(ga.find("PrimitiveType").text, 16)
		
		randomColor = randomRgb(str(i)) + [0.5]
		if primitiveType == 2:
			gaObj = addGaCube(gaRoot, ga.find("PrimitiveInfo"), randomColor)
		else:
			raise Exception(f"Unknown primitive type {primitiveType}")

		filterName = ga.find("GraphicAdjustInfo").find("FilterName").text
		gaObj.name = f"{i}-GA_{filterName}"
		gaObj["xml-PrimitiveType"] = primitiveType
		for prop in ga.find("GraphicAdjustInfo"):
			gaObj[f"xml-GAI-{prop.tag}"] = prop.text

