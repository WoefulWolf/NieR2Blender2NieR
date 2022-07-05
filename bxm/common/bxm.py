from __future__ import annotations
from io import BufferedReader, BufferedWriter
from ...utils.ioUtils import *
import xml.etree.ElementTree as ET
from typing import List, Dict

class BxmHeader:
	type: str
	flags: int
	nodeCount: int
	dataCount: int
	dataSize: int

	def fromFile(self, file: BufferedReader):
		self.type = file.read(4).decode("ascii")
		self.flags = readBe_int32(file)
		self.nodeCount = readBe_int16(file)
		self.dataCount = readBe_int16(file)
		self.dataSize = readBe_int32(file)

	def writeToFile(self, file: BufferedWriter):
		for char in self.type:
			writeBe_char(file, char)
		writeBe_int32(file, self.flags)
		writeBe_int16(file, self.nodeCount)
		writeBe_int16(file, self.dataCount)
		writeBe_int32(file, self.dataSize)

class NodeInfo:
	childCount: int
	firstChildIndex: int
	attributeCount: int
	dataIndex: int

	def fromFile(self, file: BufferedReader):
		self.childCount = readBe_int16(file)
		self.firstChildIndex = readBe_int16(file)
		self.attributeCount = readBe_int16(file)
		self.dataIndex = readBe_int16(file)

	def writeToFile(self, file: BufferedWriter):
		writeBe_int16(file, self.childCount)
		writeBe_int16(file, self.firstChildIndex)
		writeBe_int16(file, self.attributeCount)
		writeBe_int16(file, self.dataIndex)

class DataOffsets:
	nameOffset: int
	valueOffset: int

	def fromFile(self, file: BufferedReader):
		self.nameOffset = readBe_int16(file)
		self.valueOffset = readBe_int16(file)
	
	def writeToFile(self, file: BufferedWriter):
		writeBe_int16(file, self.nameOffset)
		writeBe_int16(file, self.valueOffset)

class XmlNode:
	name: str
	value: str
	attributes: Dict
	children: List
	parent: XmlNode

	_index: int
	_firstChildIndex: int
	_childCount: int

	def __init__(self) -> None:
		self.name = ""
		self.value = ""
		self.attributes = {}
		self.children = []
		self._index = -1
		self._firstChildIndex = -1
		self._childCount = -1

	def __str__(self) -> str:
		if self.children or self.value:
			tagOpen = f"<{self.name}"
			tagOpenClose = ">"
			tagClose = f"</{self.name}>"
		else:
			tagOpen = f"<{self.name}"
			tagOpenClose = "/>"
			tagClose = ""
		attributes = ""
		if self.attributes:
			attributes = " " + " ".join([f"{key}=\"{value}\"" for key, value in self.attributes.items()])
		children = ""
		if self.children:
			children = "".join([str(child) for child in self.children])
		return f"{tagOpen}{attributes}{tagOpenClose}{self.value}{children}{tagClose}"

	def toXml(self) -> ET.Element:
		node = ET.Element(self.name)
		if self.value:
			node.text = self.value
		for key, value in self.attributes.items():
			node.set(key, value)
		for child in self.children:
			node.append(child.toXml())
		
		return node

def bxmToXmlFromFile(file: BufferedReader) -> ET.Element:
	header = BxmHeader()
	header.fromFile(file)

	nodesInfos: List[NodeInfo] = []
	for i in range(header.nodeCount):
		node = NodeInfo()
		node.fromFile(file)
		nodesInfos.append(node)

	dataOffsets: List[DataOffsets] = []
	for i in range(header.dataCount):
		dataOffset = DataOffsets()
		dataOffset.fromFile(file)
		dataOffsets.append(dataOffset)

	stringsOffsets = 0x10 + 8*header.nodeCount + 4*header.dataCount

	nodes: List[XmlNode] = []
	for i, nodeInfo in enumerate(nodesInfos):
		node = XmlNode()
		node._index = i
		node._firstChildIndex = nodeInfo.firstChildIndex
		node._childCount = nodeInfo.childCount

		nodeNameOffset = dataOffsets[nodeInfo.dataIndex].nameOffset
		if nodeNameOffset != -1:
			file.seek(stringsOffsets + nodeNameOffset)
			node.name = read_string(file)
		nodeValueOffset = dataOffsets[nodeInfo.dataIndex].valueOffset
		if nodeValueOffset != -1:
			file.seek(stringsOffsets + nodeValueOffset)
			node.value = read_string(file)
		
		node.attributes = {}
		for i in range(nodeInfo.attributeCount):
			attributeName = ""
			attributeValue = ""
			attributeNameOffset = dataOffsets[nodeInfo.dataIndex + 1 + i].nameOffset
			if attributeNameOffset != -1:
				file.seek(stringsOffsets + attributeNameOffset)
				attributeName = read_string(file)
			attributeValueOffset = dataOffsets[nodeInfo.dataIndex + 1 + i].valueOffset
			if attributeValueOffset != -1:
				file.seek(stringsOffsets + attributeValueOffset)
				attributeValue = read_string(file)
			node.attributes[attributeName] = attributeValue
		
		nodes.append(node)
	
	def getNodeNextSiblings(node: XmlNode) -> List[XmlNode]:
		return nodes[node._index + 1 : node._firstChildIndex]
	
	def getNodeChildren(node: XmlNode) -> List[XmlNode]:
		if node._childCount == 0:
			return []
		firstChild = nodes[node._firstChildIndex]
		otherChildren = getNodeNextSiblings(firstChild)
		return [firstChild] + otherChildren

	for node in nodes:
		node.children = getNodeChildren(node)
		for child in node.children:
			child.parent = node
	
	xmlRootNode = nodes[0].toXml()
	return xmlRootNode

def bxmToXml(file: str) -> ET.Element:
	with open(file, "rb") as f:
		return bxmToXmlFromFile(f)

def xmlToBxm(root: ET.Element, outFileName: str) -> None:
	# flatten tree
	nodes: List[ET.Element] = []
	def getNodes(node: ET.Element):
		nodes.append(node)
		for child in node:
			getNodes(child)
	getNodes(root)

	# gather all unique strings in tag names, tag value, attribute names and attribute values
	uniqueStrings: List[str] = []
	def tryAddString(string: str):
		if string and  string not in uniqueStrings:
			uniqueStrings.append(string)
	for node in nodes:
		tryAddString(node.tag)
		for key, value in node.attrib.items():
			tryAddString(key)
			tryAddString(value)
		tryAddString(node.text and node.text.strip())
	
	# calculate string offsets
	stringToOffset: Dict[str, int] = {}
	curOffset = 0
	for string in uniqueStrings:
		stringToOffset[string] = curOffset
		curOffset += len(string) + 1
	
	# calculate data offsets (for strings)
	dataOffsets: List[DataOffsets] = []
	nodeToDataIndex: Dict[ET.Element, int] = {}
	for node in nodes:
		dataOffset = DataOffsets()
		dataOffset.nameOffset = stringToOffset.get(node.tag, -1)
		dataOffset.valueOffset = stringToOffset.get(node.text, -1)
		nodeToDataIndex[node] = len(dataOffsets)
		dataOffsets.append(dataOffset)
		for key, value in node.attrib.items():
			dataOffset = DataOffsets()
			dataOffset.nameOffset = stringToOffset.get(key, -1)
			dataOffset.valueOffset = stringToOffset.get(value, -1)
			dataOffsets.append(dataOffset)
	
	# make node infos
	nodeInfos: List[NodeInfo] = []
	nodeInfoToXmlNode: Dict[NodeInfo, ET.Element] = {}
	nodeCombos: List[(NodeInfo, ET.Element)] = []
	parentMap = { child: parent for parent in nodes for child in parent }
	def nodeToNodeInfo(node: ET.Element) -> NodeInfo:
		nodeInfo = NodeInfo()
		nodeInfo.childCount = len(node)
		nodeInfo.attributeCount = len(node.attrib)
		nodeInfo.dataIndex = nodeToDataIndex[node]
		nodeInfoToXmlNode[nodeInfo] = node
		nodeCombos.append((nodeInfo, node))
		return nodeInfo
	
	def addNodeChildrenToInfos(node: ET.Element):
		for child in node:
			nodeInfos.append(nodeToNodeInfo(child))
		for child in node:
			addNodeChildrenToInfos(child)
	nodeInfos.append(nodeToNodeInfo(root))
	addNodeChildrenToInfos(root)
	for nodeInfo in nodeInfos:
		nextIndex = -1
		if nodeInfo.childCount > 0:
			firstChild = nodeInfoToXmlNode[nodeInfo].find("*")
			nextIndex = next(i for i, (childInfo, child) in enumerate(nodeCombos) if child == firstChild)
		else:
			xmlNode = nodeInfoToXmlNode[nodeInfo]
			parent = parentMap[xmlNode]
			lastChild = parent[-1]
			lastChildIndex = next(i for i, (childInfo, child) in enumerate(nodeCombos) if child == lastChild)
			nextIndex = lastChildIndex + 1
		nodeInfo.firstChildIndex = nextIndex
	
	# write file
	header = BxmHeader()
	header.type = "XML\x00"
	header.flags = 0
	header.nodeCount = len(nodeInfos)
	header.dataCount = len(dataOffsets)
	header.dataSize = sum(len(string) + 1 for string in uniqueStrings)
	
	with open(outFileName, "wb") as f:
		header.writeToFile(f)
		for nodeInfo in nodeInfos:
			nodeInfo.writeToFile(f)
		for dataOffset in dataOffsets:
			dataOffset.writeToFile(f)
		for string in uniqueStrings:
			f.write(string.encode("utf-8") + b"\x00")