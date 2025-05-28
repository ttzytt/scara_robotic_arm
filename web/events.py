from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Self, ClassVar
from dataclasses_json import dataclass_json, DataClassJsonMixin, config, Exclude
from src.utils import get_time_millis


@dataclass
class EventMeta(ABC):
    name: str
    generated_t: int
    eid: int = field(init=False, default=-1)
    next_eid: ClassVar[int] = 0

    def __post_init__(self):
        if self.eid == -1:
            self.eid = EventMeta.next_eid
            EventMeta.next_eid += 1


@dataclass_json
@dataclass
class BrowserEvent(EventMeta, DataClassJsonMixin, ABC):
    received_t: int
    generated_t: int = field(init=False, default=-1)

    @classmethod
    def deserialize(cls, json_str: str) -> Self:
        return cls.from_json(json_str)

    @property
    def latency(self) -> int:
        return self.received_t - self.generated_t


@dataclass
class LocalEvent(EventMeta, DataClassJsonMixin, ABC):
    @abstractmethod
    def serialize(self) -> str:
        return self.to_json()

    def __post_init__(self):
        super().__post_init__()
        self.generated_t = get_time_millis()


@dataclass
class AlertRequestEvent(LocalEvent):
    msg: str
    name: str = "alert_request"
    alert_req_eids: ClassVar[set[int]] = field(
        default=set(),
        metadata=config(
            exclude=Exclude.ALWAYS,
        ),
    )

    def __post_init__(self):
        super().__post_init__()
        if self.eid in AlertRequestEvent.alert_req_eids:
            raise ValueError(f"Duplicate eid: {self.eid} in alert requests")
        AlertRequestEvent.alert_req_eids.add(self.eid)


@dataclass
class AlertResponseEvent(BrowserEvent):
    respond_to_eid: int
    name: str = "alert_response"

    def __post_init__(self):
        super().__post_init__()
        if self.respond_to_eid not in AlertRequestEvent.alert_req_eids:
            raise ValueError(
                f"Invalid respond_to_eid: {self.respond_to_eid}. Must be in {AlertRequestEvent.alert_req_eids}"
            )
        AlertRequestEvent.alert_req_eids.remove(self.respond_to_eid)
