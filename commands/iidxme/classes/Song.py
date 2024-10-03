from dataclasses import dataclass
from commands.iidxme.classes.Chart import Chart


@dataclass
class Song:
    song_id: str
    title: str
    charts: list[Chart]