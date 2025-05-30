import asyncio
import json
from typing import Dict, Tuple, Any, AsyncGenerator
from fastapi import WebSocket, WebSocketDisconnect
from web.events import RequestEvent, ResponseEvent


class ResponseManager:
    """
    Manages the round-trip of sending RequestEvent and receiving ResponseEvent.
    """

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket
        # Map eid to (Future, RequestEvent)
        self.pending: Dict[int, Tuple[asyncio.Future[Any], RequestEvent]] = {}

    async def send_request(self, request: RequestEvent) -> None:
        """
        Create and store a Future for this request.eid, then send the request JSON.
        """
        eid = request.eid
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[ResponseEvent] = loop.create_future()
        # Store the future and the original RequestEvent
        self.pending[eid] = (fut, request)
        # Send the serialized request over the websocket
        await self.websocket.send_text(request.to_json())

    async def wait_for_response(self, request: RequestEvent) -> ResponseEvent:
        """
        Wait for and return the ResponseEvent corresponding to request.eid.
        """
        eid = request.eid
        fut, _ = self.pending[eid]
        resp = await fut
        assert isinstance(resp, request.response_cls),  "Response type mismatch"
        # Remove the entry once the response is received
        self.pending.pop(eid, None)
        return resp

    async def send_and_wait(self, request: RequestEvent) -> ResponseEvent:
        """
        Send a request and wait for its response in one step.
        """
        await self.send_request(request)
        return await self.wait_for_response(request)

    async def receive_loop(self) -> AsyncGenerator[str, None]:
        """
        Continuously read messages from the websocket.
        If a message is a ResponseEvent for a pending request, resolve its Future.
        Otherwise, yield the raw message upstream.
        """
        try:
            while True:
                raw = await self.websocket.receive_text()
                rid = None
                try:
                    data = json.loads(raw)
                    rid = data.get("respond_to_eid")
                except Exception:
                    # Not valid JSON or missing field
                    pass

                if isinstance(rid, int) and rid in self.pending:
                    fut, req = self.pending[rid]
                    # Deserialize using the response_cls from the original RequestEvent
                    resp = req.response_cls.deserialize(raw)
                    fut.set_result(resp)
                    continue

                # Forward non-response messages
                yield raw

        except WebSocketDisconnect:
            # On disconnect, fail all pending futures
            for fut, _ in self.pending.values():
                if not fut.done():
                    fut.set_exception(WebSocketDisconnect())
            return
