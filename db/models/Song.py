from dataclasses import dataclass
from db.models.Chart import Chart


@dataclass
class Song:
    song_id: str
    title: str
    charts: list[Chart]