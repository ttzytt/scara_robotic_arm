import asyncio
import json
from typing import Dict, Tuple, Type, Any, AsyncGenerator, TypeVar
from fastapi import WebSocket, WebSocketDisconnect
from web.events import RequestEvent, ResponseEvent


class ResponseManager:
    """
    Manages RequestEvent → ResponseEvent round-trips without backlog.
    Server must send RequestEvent before client can respond.
    """

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket
        # eid → (Future, ResponseEvent subclass)
        self.pending: Dict[int, Tuple[asyncio.Future[Any], Type[ResponseEvent]]] = {}

    R = TypeVar('R', bound=ResponseEvent)
    async def send_request(self, request: RequestEvent, response_cls: Type['R']) -> None:
        """
        Register a Future[R] for request.eid, then send the request JSON.
        """
        eid = request.eid
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[ResponseManager.R] = loop.create_future()
        self.pending[eid] = (fut, response_cls)
        
        await self.websocket.send_text(request.to_json())

    async def wait_for_response(self, request: RequestEvent) -> ResponseEvent:
        """
        Await the ResponseEvent matching request.eid.
        """
        eid = request.eid
        fut, resp_cls = self.pending[eid]
        resp = await fut
        # cleanup after receipt
        self.pending.pop(eid, None)
        return resp

    async def receive_loop(self) -> AsyncGenerator[str, None]:
        """
        Continuously read from websocket.
        Dispatch ResponseEvent into pending,
        yield other raw JSON messages.
        """

        try:
            while True:
                raw = await self.websocket.receive_text()
                # peek for respond_to_eid
                try:
                    data = json.loads(raw)
                    rid = data.get("respond_to_eid")
                except Exception:
                    rid = None

                if isinstance(rid, int) and rid in self.pending:
                    fut, resp_cls = self.pending[rid]
                    # will raise if invalid respond_to_eid
                    resp = resp_cls.deserialize(raw)
                    fut.set_result(resp)
                    continue

                # forward non-response or unexpected-response messages
                yield raw

        except WebSocketDisconnect:
            # cancel all pending on disconnect
            for fut, _ in self.pending.values():
                if not fut.done():
                    fut.set_exception(WebSocketDisconnect())
            return