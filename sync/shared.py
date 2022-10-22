
dependencies_installed = False

SyncObjectsType = {
	0: "area",
	1: "entity",
	2: "bezier",
	"area": 0,
	"entity": 1,
	"bezier": 2,
}

_disableDepsgraphUpdates = False
def getDisableDepsgraphUpdates():
	return _disableDepsgraphUpdates
def setDisableDepsgraphUpdates(val):
	global _disableDepsgraphUpdates
	_disableDepsgraphUpdates = val
