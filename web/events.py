from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Self, ClassVar

@dataclass 
class EventMeta(ABC): 
    name : str
    generated_t : int
    eid : int = field(init=False, default=-1)
    next_eid : ClassVar[int] = 0

    def __post_init__(self):
        if self.eid == -1:
            self.eid = EventMeta.next_eid
            EventMeta.next_eid += 1

@dataclass
class BrowserEvent(EventMeta):
    received_t : int
    generated_t : int = field(init=False, default=-1)

    @classmethod
    @abstractmethod
    def deserialize(cls, json_str: str) -> Self:
        pass

    @property
    def latency(self) -> int: 
        return self.received_t - self.generated_t

@dataclass
class LocalEvent(EventMeta):
    @abstractmethod
    def serialize(self) -> str: 
        pass