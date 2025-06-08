from abc import ABC, abstractmethod
from typing import Optional

from ..app_types import HistoryData


class ITextGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        history: HistoryData,
        model: Optional[str] = None
    ) -> str:
        pass
