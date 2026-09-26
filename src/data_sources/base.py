from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseDataSource(ABC):
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        pass
    
    def _format_date(self, date: datetime) -> str:
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def _log_request(self, endpoint: str, params: Dict[str, Any]) -> None:
        self.logger.info(f"Requesting {endpoint} with params: {params}")
    
    def _log_response(self, status_code: int, data_size: int) -> None:
        self.logger.info(f"Response: {status_code}, Data size: {data_size} bytes")
