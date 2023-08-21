from typing import Optional


class Config:
    __slots__ = ("token", "scylla_hosts", "scylla_port", "scylla_keyspace")

    def __init__(self, token: str, scylla_hosts: list[str], scylla_port: Optional[int] = None):
        self.token = token
        self.scylla_hosts = scylla_hosts
        self.scylla_port: int = scylla_port or 9042
        self.scylla_keyspace: str = "mmbot"
