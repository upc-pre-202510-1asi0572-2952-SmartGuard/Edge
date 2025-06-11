from dataclasses import dataclass
from datetime import datetime

@dataclass
class AccessEvent:
    user_id: str
    timestamp: datetime
    result: str
    method: str