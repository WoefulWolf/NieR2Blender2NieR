from __future__ import annotations
from enum import Enum


dependencies_installed = False

class SyncObjectsType(Enum):
	list = 0
	area = 1
	entity = 2
	bezier = 3

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
