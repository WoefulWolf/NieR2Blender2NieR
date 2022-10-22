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

def removeOnMessageListener(listener: callable):
	_onMsgListeners.remove(listener)

def _onMessage(ws: WebSocketApp, message: str):
	msgData = SyncMessage.fromJson(json.loads(message))
	for listener in _onMsgListeners:
		listener(msgData)

def sendMsgToServer(msg: SyncMessage):
	if not _isConnectedToWs:
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
	
	_ws = WebSocketApp(f"ws://localhost:{_wsPort}", on_message=_onMessage)
	_wsThread = WsThread()
	
	_isConnectedToWs = True
	
	return True

def disconnectFromWebsocket():
	global _isConnectedToWs
	if not _isConnectedToWs:
		return
	
	_ws.close()
	_isConnectedToWs = False
