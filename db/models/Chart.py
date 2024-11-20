from dataclasses import dataclass


@dataclass
class Chart:
    chart_id: str
    difficulty: str
    level: int
    notes: int