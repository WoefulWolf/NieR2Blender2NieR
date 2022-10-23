import math
import random
import re
from typing import Tuple, List, Dict
import bpy
from mathutils import Color
import xml.etree.ElementTree as ET


currentCollection: bpy.types.Collection = None
def setCurrentCollection(col: bpy.types.Collection):
    global currentCollection
    currentCollection = col
def getCurrentCollection() -> bpy.types.Collection:
    return currentCollection


def tryAddCollection(collName: str, parent: bpy.types.Collection) -> bpy.types.Collection:
    if collName in bpy.data.collections:
        return bpy.data.collections[collName]
    else:
        newColl = bpy.data.collections.new(collName)
        parent.children.link(newColl)
        return newColl


def tryAddEmpty(name: str, parentObj: bpy.types.Object = None) -> bpy.types.Object:
    if name in bpy.data.objects and (
            bpy.data.objects[name].parent == parentObj and bpy.data.objects[name].users_collection[
        0] == currentCollection):
        for child in list(bpy.data.objects[name].children):
            bpy.data.objects.remove(child, do_unlink=True)
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    newObj = bpy.data.objects.new(name, None)
    currentCollection.objects.link(newObj)
    if parentObj is not None:
        newObj.parent = parentObj
    return newObj


def prepareObject(obj: bpy.types.Object, name: str, parent: bpy.types.Object, color: List[float] = None) -> None:
    obj.name = name
    obj.parent = parent
    if color:
        obj.color = color
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    currentCollection.objects.link(obj)

def makeMeshObj(name: str, vertices: List[List[float]], edges: List[List[float]], faces: List[List[float]],
                parent: bpy.types.Object, color: List[float] = None) -> bpy.types.Object:
    cube = bpy.data.meshes.new(name)
    cubeObj = bpy.data.objects.new(name, cube)
    prepareObject(cubeObj, name, parent, color)
    cubeObj.show_wire = True
    cube.from_pydata(vertices, edges, faces)

    # entering & exiting edit mode fixes some crashes
    bpy.context.view_layer.objects.active = cubeObj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = None

    return cubeObj

def makeEmptyObj(name: str, parent: bpy.types.Object) -> bpy.types.Object:
    emptyObj = bpy.data.objects.new(name, None)
    prepareObject(emptyObj, name, parent)
    return emptyObj

def makeCube(name, parent: bpy.types.Object, color: List[float], originAtCorner=True) -> bpy.types.Object:
    vertices = [
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 1],
        [1, 1, 1],
        [0, 1, 1]
    ]
    if not originAtCorner:
        for i in range(len(vertices)):
            for j in range(3):
                vertices[i][j] -= 0.5
    faces = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [2, 3, 7, 6],
        [0, 3, 7, 4],
        [1, 2, 6, 5]
    ]
    cubeObj = makeMeshObj(name, vertices, [], faces, parent, color)

    return cubeObj


def makeSphereObj(name: str, radius: float, parent: bpy.types.Object, color: List[float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1)
    sphereObj = bpy.context.active_object
    prepareObject(sphereObj, name, parent, color)
    sphereObj.scale = [radius, radius, radius]

    return sphereObj


def makeCurve(name: str, points: List[List[float]], radius: float, isLoop: bool, parent: bpy.types.Object,
              color: List[float]) -> bpy.types.Object:
    curve: bpy.types.Curve = bpy.data.curves.new(name, "CURVE")
    curveObj = bpy.data.objects.new(name, curve)
    prepareObject(curveObj, name, parent, color)

    curve.dimensions = "3D"
    curve.splines.new(type="POLY")

    locations = points
    if len(locations[0]) == 4:
        wLocs = [loc[3] for loc in locations]
        curveObj["allPosW"] = wLocs
    if isLoop:
        locations.append(locations[0])

    curve.splines.active.points.add(len(locations) - 1)
    for i, loc in enumerate(locations):
        curvePoint = curve.splines[0].points[i]
        if len(loc) == 4:
            loc[3] = 1
        else:
            loc.append(1)
        curvePoint.co = loc
    curve.splines[0].use_endpoint_u = True
    curve.splines[0].use_endpoint_v = False

    curve.bevel_mode = "ROUND"
    curve.bevel_depth = radius
    curve.bevel_resolution = 8

    return curveObj


def makeBezier(
        name: str,
        points: List[List[float]],
        leftHandles: List[List[float]], rightHandles: List[List[float]],
        loops: bool,
        parent: bpy.types.Object,
        radius: float,
        color: List[float]
) -> bpy.types.Object:
    curve: bpy.types.Curve = bpy.data.curves.new(name, "CURVE")
    curveObj = bpy.data.objects.new(name, curve)
    prepareObject(curveObj, name, parent, color)

    curve.dimensions = "3D"
    curve.splines.new(type="BEZIER")

    locations = points

    curve.splines.active.bezier_points.add(len(locations) - 1)
    for i in range(len(locations)):
        curvePoint = curve.splines[0].bezier_points[i]
        curvePoint.co = locations[i]
        curvePoint.handle_left = leftHandles[i] if leftHandles else locations[i]
        curvePoint.handle_right = rightHandles[i] if rightHandles else locations[i]

    curve.splines[0].use_cyclic_u = loops

    if radius > 0:
        curve.bevel_mode = "ROUND"
        curve.bevel_depth = radius
        curve.bevel_resolution = 8

    return curveObj


def makeCircle(name: str, radius: float, parent: bpy.types.Object, color: List[float]) -> bpy.types.Object:
    bpy.ops.curve.primitive_bezier_circle_add(radius=radius)
    circleObj = bpy.context.active_object
    prepareObject(circleObj, name, parent, color)
    return circleObj

def makeCircleMesh(name: str, radius: float, parent: bpy.types.Object, color: List[float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_circle_add(radius=radius, fill_type="NGON")
    circleObj = bpy.context.active_object
    prepareObject(circleObj, name, parent, color)
    return circleObj

def makeSphereMesh(name: str, radius: float, parent: bpy.types.Object, color: List[float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius)
    sphereObj = bpy.context.active_object
    prepareObject(sphereObj, name, parent, color)
    return sphereObj

# importing - misc

seedOffsets: Dict[str, int] = {}
def randomRgb(seed: str = "") -> List[float]:
    if seed not in seedOffsets:
        seedOffsets[seed] = 0
    random.seed(f"{seed}{seedOffsets[seed]}")
    seedOffsets[seed] += 1
    color = Color()
    color.hsv = [random.random(), 1, 1]
    return [color.r, color.g, color.b]


def setXmlAttributesOnObj(obj: bpy.types.Object, xml: ET.Element):
    for attr in xml.attrib:
        obj[f"xml-{attr}"] = xml.attrib[attr]


def strToFloat(str: str) -> float:
    if "#IND" in str:
        return float("nan")
    if str == "1.#INF":
        return float("inf")
    if str == "-1.#INF":
        return float("-inf")
    return float(str)


def xmlVecToVec2(vecStr: str) -> List[float]:
    vals = [strToFloat(s) for s in vecStr.split(" ")]
    return [vals[0], -vals[1]]


def xmlVecToVec3(vecStr: str) -> List[float]:
    vals = [strToFloat(s) for s in vecStr.split(" ")]
    return [vals[0], -vals[2], vals[1]]

def xmlVecToVec3Scale(vecStr: str) -> List[float]:
    vals = [strToFloat(s) for s in vecStr.split(" ")]
    return [vals[0], vals[2], vals[1]]


def xmlVecToVec4(vecStr: str) -> List[float]:
    vals = [strToFloat(s) for s in vecStr.split(" ")]
    return [vals[0], -vals[2], vals[1], vals[3]]


def setObjPosFromXmlPos(obj: bpy.types.Object, posStr: str) -> None:
    vals = xmlVecToVec4(posStr)
    obj.location = vals[:3]
    obj["posW"] = vals[3]


# exporting

def transferXmlPropsToXml(obj: bpy.types.Object, element: ET.Element):
    for prop in obj.keys():
        if prop.startswith("xml-"):
            element.attrib[prop[4:]] = obj[prop]


biggestFloatInt = 2 ** 24


def floatFmt(f: float):
    expFallback = str(f)
    if abs(f) > biggestFloatInt and "e" not in expFallback:
        expFallback = f"{f:e}"
    if "e" in expFallback:
        eSplitPos = expFallback.find("e") + 2
        p1 = expFallback[:eSplitPos]
        p2 = expFallback[eSplitPos:]
        p2 = (3 - len(p2)) * "0" + p2
        return p1 + p2
    fStr = f"{f:.4f}"
    fStr = re.sub(r"\.?0+$", "", fStr)
    return fStr


def floatToStr(num: float) -> str:
    if math.isnan(num):
        return "-1.#IND"
    if num == float("inf"):
        return "1.#INF"
    if num == float("-inf"):
        return "-1.#INF"
    return floatFmt(num)


def vecToXmlVec2(vec: Tuple[float, float, float]) -> str:
    return f"{floatToStr(vec[0])} {floatToStr(-vec[1])}"


def vecToXmlVec3(vec: Tuple[float, float, float]) -> str:
    return f"{floatToStr(vec[0])} {floatToStr(vec[2])} {floatToStr(-vec[1])}"

def vecToXmlVec3Scale(vec: Tuple[float, float, float]) -> str:
    return f"{floatToStr(vec[0])} {floatToStr(vec[2])} {floatToStr(vec[1])}"


def vecToXmlVec4(vec: Tuple[float, float, float, float]) -> str:
    return f"{floatToStr(vec[0])} {floatToStr(vec[2])} {floatToStr(-vec[1])} {floatToStr(vec[3])}"


def objPosToXmlVec4(obj: bpy.types.Object) -> str:
    return f"{floatToStr(obj.location[0])} {floatToStr(obj.location[2])} {floatToStr(-obj.location[1])} {floatToStr(obj['posW'])}"


def setXmlAttribAsElement(element: ET.Element, attr: str, value: str):
    subElem = ET.SubElement(element, attr)
    subElem.text = value
