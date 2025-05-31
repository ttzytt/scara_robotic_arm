import asyncio
import json
from typing import Dict, Tuple, Any, Type
from fastapi import WebSocket, WebSocketDisconnect
from web.events import EventMeta, RequestEvent, ResponseEvent


class CommHelper:
    """
    Manages two concerns:
      1) Round-trip for RequestEvent -> ResponseEvent (low-frequency, FIFO)
      2) High-frequency events with use_latest=True (keep only the latest)

    Under the hood:
      - pending:    Dict[eid -> (Future, RequestEvent)] for waiting responses
      - queue:      FIFO queue for events that are not use_latest
      - latest_raw: Dict[event_class -> raw JSON] for events with use_latest=True
      - latest_waiter: Dict[event_class -> Future[str]] to notify awaiters when a new raw arrives
    """

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket

        # Store pending requests: eid -> (Future, RequestEvent)
        self.pending: Dict[int, Tuple[asyncio.Future[Any], RequestEvent]] = {}

        # FIFO queue for raw JSON that are not high-frequency
        self.queue: asyncio.Queue[str] = asyncio.Queue()

        # latest_raw[event_class] = raw JSON string, only keep last for use_latest events
        self.latest_raw: Dict[Type[EventMeta], str] = {}

        # latest_waiter[event_class] = Future[str]: used to wake up exactly one waiter
        self.latest_waiter: Dict[Type[EventMeta], asyncio.Future[str]] = {}

        # Print the registered event name-to-class mapping for debugging

    async def send_request(self, request: RequestEvent) -> None:
        """
        Send a RequestEvent to the browser and create a Future to wait for its response.
        """
        eid = request.eid
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[ResponseEvent] = loop.create_future()
        self.pending[eid] = (fut, request)
        await self.websocket.send_text(request.serialize())

    async def wait_for_response(self, request: RequestEvent) -> ResponseEvent:
        """
        Wait for the corresponding ResponseEvent of the given RequestEvent.
        """
        eid = request.eid
        fut, _ = self.pending[eid]
        resp = await fut
        assert isinstance(resp, request.response_cls), "Response type mismatch"
        self.pending.pop(eid, None)
        return resp

    async def send_and_wait(self, request: RequestEvent) -> ResponseEvent:
        """
        Convenience method: send request then await its response in one call.
        """
        await self.send_request(request)
        return await self.wait_for_response(request)

    async def receive_loop(self) -> None:
        """
        Continuously read raw JSON from WebSocket and distribute:
          1) If raw contains 'respond_to_eid' matching a pending request, treat as ResponseEvent
          2) Else, check 'name' to find the event class via EventMeta.name_to_cls
             2.1) If evt_cls.use_latest is True, store raw under latest_raw[evt_cls], then satisfy any waiter
             2.2) Otherwise push raw into FIFO queue
          3) If no valid 'name', push raw into FIFO queue
        """
        try:
            while True:
                raw_str = await self.websocket.receive_text()
                json_data = json.loads(raw_str)

                evt_name = json_data.get("name")
                # Ensure evt_name is a registered event name
                assert isinstance(
                    evt_name, str
                ), f"Event JSON missing 'name' or not a string: {raw_str}"
                assert (
                    evt_name in EventMeta.name_to_cls
                ), f"Unknown event name: {evt_name}"

                evt_cls = EventMeta.name_to_cls[evt_name]

                if issubclass(evt_cls, ResponseEvent):
                    resp_evt = evt_cls.deserialize(raw_str)
                    rid = resp_evt.respond_to_eid
                    assert isinstance(
                        rid, int
                    ), "ResponseEvent missing valid respond_to_eid"
                    assert rid in self.pending, f"No pending request for eid: {rid}"
                    fut, _ = self.pending[rid]
                    if not fut.done():
                        fut.set_result(resp_evt)
                    continue

                if evt_cls.use_latest:
                    # Overwrite the latest_raw for this event class
                    self.latest_raw[evt_cls] = raw_str

                    # Satisfy any pending pop_latest waiter
                    fut = self.latest_waiter.get(evt_cls)
                    if fut is not None and not fut.done():
                        fut.set_result(raw_str)
                        self.latest_waiter.pop(evt_cls, None)
                    continue

                await self.queue.put(raw_str)

        except WebSocketDisconnect:
            # On disconnect, cancel all pending futures
            for fut, _ in self.pending.values():
                if not fut.done():
                    fut.set_exception(WebSocketDisconnect())
            # Also cancel any waiting pop_latest futures
            for fut in self.latest_waiter.values():
                if not fut.done():
                    fut.set_exception(WebSocketDisconnect())
            return

    async def get_next_non_latest(self) -> str:
        """
        Await and return the next FIFO message (non use_latest).
        """
        return await self.queue.get()

    async def pop_latest(self, evt_cls: Type[EventMeta]) -> str:
        """
        Await and return the stored raw JSON for the given event class if it exists;
        otherwise wait until a new raw JSON arrives.

        Usage:
          raw = await helper.pop_latest(GamepadRawState)
        """
        # Ensure this method is used only on events with use_latest=True
        assert (
            evt_cls.use_latest
        ), f"pop_latest() must be called for use_latest events, got: {evt_cls.name}"

        # 1) If there is already a cached value, pop and return it immediately
        if evt_cls in self.latest_raw:
            return self.latest_raw.pop(evt_cls)

        # 2) Otherwise, create or reuse a Future to wait for the next arrival
        fut = self.latest_waiter.get(evt_cls)
        if fut is None or fut.done():
            fut = asyncio.get_event_loop().create_future()
            self.latest_waiter[evt_cls] = fut

        return await fut
