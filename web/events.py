from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Self

@dataclass 
class EventMeta(ABC): 
    eid : int
    t : int
    name : str

@dataclass
class BrowserEvent(EventMeta):
    received_t : int

    @classmethod
    @abstractmethod
    def deserialize(cls, json_str: str) -> Self:
        pass

    @property
    def latency(self) -> int: 
        return self.received_t - self.t

@dataclass
class LocalEvent(EventMeta):
    @abstractmethod
    def serialize(self) -> str: 
        pass