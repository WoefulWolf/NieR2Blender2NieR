from __future__ import annotations
from enum import Enum
from typing import Callable, List, Tuple


dependencies_installed = False

class SyncObjectsType(Enum):
	list = 0
	area = 1
	entity = 2
	bezier = 3
	enemyGeneratorNode = 4
	enemyGeneratorDist = 5
	camTargetLocation = 6
	camera = 7

	@staticmethod
	def fromInt(i: int) -> SyncObjectsType:
		return SyncObjectsType(i)

class SyncUpdateType(Enum):
	prop = 0
	add = 1
	remove = 2
	duplicate = 3

	@staticmethod
	def fromInt(i: int) -> SyncUpdateType:
		return SyncUpdateType(i)

_disableDepsgraphUpdates = False
def getDisableDepsgraphUpdates():
	return _disableDepsgraphUpdates
def setDisableDepsgraphUpdates(val):
	global _disableDepsgraphUpdates
	_disableDepsgraphUpdates = val

def noDropDownDefault():
	return None
dropDownOperatorAndIcon: Callable[[], Tuple[str, str]|None] = noDropDownDefault
def setDropDownOperatorAndIcon(op: Callable[[], Tuple[str, str]|None]):
	global dropDownOperatorAndIcon
	dropDownOperatorAndIcon = op
def removeDropDownOperatorAndIcon(op: Callable[[], Tuple[str, str]|None]):
	global dropDownOperatorAndIcon
	if dropDownOperatorAndIcon == op:
		dropDownOperatorAndIcon = noDropDownDefault
def getDropDownOperatorAndIcon() -> Tuple[str, str]|None:
	return dropDownOperatorAndIcon()
