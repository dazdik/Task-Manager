from fastapi.websockets import WebSocket, WebSocketState


class WebSocketManager:
    def __init__(self):
        self.active_websockets: dict[int, list[WebSocket]] = {}

    async def connect(self, task_id: int, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_websockets:
            self.active_websockets[task_id] = []
        self.active_websockets[task_id].append(websocket)

    async def disconnect(self, task_id: int, websocket: WebSocket):
        self.active_websockets.get(task_id).remove(websocket)

    async def send_message(self, task_id: int, message: dict):
        clients = self.active_websockets.get(task_id, [])
        for ws in clients:  # type: WebSocket
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")


ws_manager = WebSocketManager()
