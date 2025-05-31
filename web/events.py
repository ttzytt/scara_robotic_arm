from dataclasses import dataclass, field
from abc import ABC
from typing import Self, ClassVar, Type, Literal
from dataclasses_json import DataClassJsonMixin, config, Exclude
from src.utils import get_time_millis
import json

@dataclass(kw_only=True)
class EventMeta(DataClassJsonMixin, ABC):
    name: ClassVar[str]
    generated_t: int
    eid: int = field(init=False, default=-1)
    use_latest: ClassVar[bool] = False

    name_to_cls: ClassVar[dict[str, Type["EventMeta"]]] = {}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if hasattr(cls, "name") and isinstance(getattr(cls, "name"), str):
            EventMeta.name_to_cls[cls.name] = cls


@dataclass(kw_only=True)
class BrowserEvent(EventMeta, ABC):
    received_t: int = field(default_factory=get_time_millis)

    @classmethod
    def deserialize(cls, json_str: str) -> Self:
        return cls.from_json(json_str)

    @property
    def latency(self) -> int:
        return self.received_t - self.generated_t


@dataclass(kw_only=True)
class ServerEvent(EventMeta, ABC):
    next_eid: ClassVar[int] = 0
    generated_t: int = field(default_factory=get_time_millis)

    def serialize(self) -> str:
        d = self.to_dict()
        d['name'] = self.name
        return json.dumps(d)
    def __post_init__(self):
        if self.eid == -1:
            self.eid = ServerEvent.next_eid
            ServerEvent.next_eid += 1


@dataclass(kw_only=True)
class RequestEvent(ServerEvent, DataClassJsonMixin, ABC):
    response_cls: ClassVar[Type["ResponseEvent"]] = field(
        metadata=config(
            exclude=Exclude.ALWAYS,
        ),
    )

    req_eids: ClassVar[set[int]] = field(
        default=set(),
        metadata=config(
            exclude=Exclude.ALWAYS,
        ),
    )

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.req_eids = set()

    def __post_init__(self):
        super().__post_init__()
        if self.eid in self.__class__.req_eids:
            raise ValueError(f"Duplicate eid: {self.eid} in {self.__class__.__name__}")
        self.__class__.req_eids.add(self.eid)


@dataclass(kw_only=True)
class ResponseEvent(BrowserEvent, DataClassJsonMixin, ABC):
    request_cls: ClassVar[Type[RequestEvent]] = field(
        metadata=config(
            exclude=Exclude.ALWAYS,
        ),
    )
    respond_to_eid: int

    def __post_init__(self):
        if self.respond_to_eid not in self.request_cls.req_eids:
            raise ValueError(
                f"{self.__class__.__name__} invalid respond_to_eid: "
                f"{self.respond_to_eid} not in {self.request_cls.__name__}.req_eids"
            )
        self.request_cls.req_eids.remove(self.respond_to_eid)


ConfirmType = Literal["ok", "cancel", "both"]


@dataclass(kw_only=True)
class ConfirmRequestEvent(RequestEvent):
    name: ClassVar[str] = "confirm_request"
    msg: str
    require_confirm: ConfirmType = "ok"


@dataclass(kw_only=True)
class ConfirmResponseEvent(ResponseEvent):
    name: ClassVar[str] = "confirm_response"
    respond_to_eid: int
    response: ConfirmType
    request_cls = ConfirmRequestEvent


ConfirmRequestEvent.response_cls = ConfirmResponseEvent
