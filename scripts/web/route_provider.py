from abc import ABC, abstractmethod
from flask import Flask


class IRouteProvider(ABC):
    @abstractmethod
    def register(self, app: Flask) -> None:
        pass
