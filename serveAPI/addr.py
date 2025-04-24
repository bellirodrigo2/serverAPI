from dataclasses import dataclass


@dataclass
class Addr:
    ip: str
    port: int
