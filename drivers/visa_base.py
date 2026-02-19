from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import pyvisa

@dataclass
class VisaConfig:
    backend: str = "@py"
    timeout_ms: int = 15000

class VisaInstrument:
    def __init__(self, resource: str, cfg: VisaConfig):
        rm = pyvisa.ResourceManager(cfg.backend) if cfg.backend else pyvisa.ResourceManager()
        self.inst = rm.open_resource(resource)
        self.inst.timeout = cfg.timeout_ms
        # good defaults
        try:
            self.inst.write_termination = "\n"
            self.inst.read_termination = "\n"
        except Exception:
            pass

    def write(self, cmd: str) -> None:
        self.inst.write(cmd)

    def query(self, cmd: str) -> str:
        return self.inst.query(cmd)

    def close(self) -> None:
        try:
            self.inst.close()
        except Exception:
            pass
