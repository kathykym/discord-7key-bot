from dataclasses import dataclass


@dataclass
class PbInfo:
    lamp: str
    score: int
    score_attained_version: str
    rank: str
    rank_diff: str
    rate: str
    misscount: int