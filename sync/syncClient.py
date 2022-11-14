from __future__ import annotations
import json
import threading
from time import time
from typing import List
from websocket import create_connection, WebSocket, WebSocketApp

_isConnectedToWs = False
_ws: WebSocketApp = None
_wsThread: WsThread = None
_wsPort = 1547
_onMsgListeners: List[callable] = []
_onEndListeners: List[callable] = []

class SyncMessage:
	method: str
	uuid: str
	args: dict

	def __init__(self, method, uuid, args):
		self.method = method
		self.uuid = uuid
		self.args = args
	
	@classmethod
	def fromJson(cls, jsonObj):
		return cls(jsonObj["method"], jsonObj["uuid"], jsonObj["args"])
	
	def toJson(self):
		return {
			"method": self.method,
			"uuid": self.uuid,
			"args": self.args
		}


def isConnectedToWs() -> bool:
	return _isConnectedToWs

def addOnMessageListener(listener: callable):
	_onMsgListeners.append(listener)

def addOnWsEndListener(listener: callable):
	_onEndListeners.append(listener)

def removeOnMessageListener(listener: callable):
	_onMsgListeners.remove(listener)

def removeOnWsEndListener(listener: callable):
	_onEndListeners.remove(listener)

def _onMessage(ws: WebSocketApp, message: str):
	global _isConnectedToWs
	msgData = SyncMessage.fromJson(json.loads(message))
	if not _isConnectedToWs and msgData.method == "connected":
		_isConnectedToWs = True
		return
	for listener in _onMsgListeners:
		listener(msgData)

def _onEnd(_=None, __=None, ___=None):
	global _isConnectedToWs, _ws, _wsThread
	_isConnectedToWs = False
	for listener in _onEndListeners:
		listener()
	if _ws is not None:
		_ws.close()
	_ws = None
	_wsThread = None

def _onError(ws: WebSocketApp, error: str):
	print(error)
	_onEnd()

def _confirmIsConnected():
	global _isConnectedToWs
	if _isConnectedToWs or _ws is None:
		return
	print("Failed to connect to websocket server")
	_onEnd()

def sendMsgToServer(msg: SyncMessage):
	if not _isConnectedToWs:
		return
	if _ws.sock is None:
		_onEnd()
		return
	_ws.send(json.dumps(msg.toJson()))

class WsThread(threading.Thread):
	def __init__(self):
		super().__init__()
		self.start()
	
	def run(self):
		_ws.run_forever()

def connectToWebsocket() -> bool:
	global _isConnectedToWs, _ws, _wsThread
	if _isConnectedToWs:
		return True
	
	_ws = WebSocketApp(f"ws://localhost:{_wsPort}", on_message=_onMessage, on_close=_onEnd, on_error=_onError)
	_wsThread = WsThread()
	confirmConnectionTimer = threading.Timer(0.2, _confirmIsConnected)
	confirmConnectionTimer.start()
	
	return True

def disconnectFromWebsocket():
	global _isConnectedToWs
	if not _isConnectedToWs:
		return
	
	_ws.close()
	_isConnectedToWs = False
