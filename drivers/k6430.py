from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional
from .visa_base import VisaInstrument, VisaConfig
import time

Func = Literal["VOLT", "CURR", "RES"]

@dataclass
class K6430:
    visa: VisaInstrument

    @classmethod
    def open(cls, resource: str, cfg: VisaConfig) -> "K6430":
        return cls(VisaInstrument(resource, cfg))

    def reset(self) -> None:
        self.visa.write("*RST")
        self.visa.write("*CLS")

    def idn(self) -> str:
        return self.visa.query("*IDN?").strip()

    def output(self, on: bool) -> None:
        self.visa.write(f":OUTP {'ON' if on else 'OFF'}")

    # --- Source configuration ---
    def source_v(self, value_v: float, rng: Optional[float]=None) -> None:
        self.visa.write(":SOUR:FUNC VOLT")
        if rng is not None:
            self.visa.write(f":SOUR:VOLT:RANG {rng}")
        self.visa.write(f":SOUR:VOLT {value_v}")

    def source_i(self, value_a: float, rng: Optional[float]=None) -> None:
        self.visa.write(":SOUR:FUNC CURR")
        if rng is not None:
            self.visa.write(f":SOUR:CURR:RANG {rng}")
        self.visa.write(f":SOUR:CURR {value_a}")

    def source_v_query(self) -> float:
        return float(self.visa.query(":SOUR:VOLT?"))

    def source_i_query(self) -> float:
        return float(self.visa.query(":SOUR:CURR?"))

    # --- Measure configuration ---
    def sense_func(self, func: Func) -> None:
        if func == "VOLT":
            self.visa.write(":SENS:FUNC:ON 'VOLT'")
            time.sleep(0.5)
            self.visa.write(":FUNC:OFF 'CURR'")
        elif func == "CURR":
            self.visa.write(":SENS:FUNC:ON 'CURR'")
            time.sleep(0.5)
            self.visa.write(":FUNC:OFF 'VOLT'")
        elif func == "RES":
            self.visa.write(":SENS:FUNC:ON 'RES'")
        else:
            raise ValueError(func)

    def sense_range(self, func: Func, rng: float) -> None:
        if func == "VOLT":
            self.visa.write(f":SENS:VOLT:RANG {rng}")
        elif func == "CURR":
            self.visa.write(f":SENS:CURR:RANG {rng}")
        elif func == "RES":
            self.visa.write(f":SENS:RES:RANG {rng}")
        else:
            raise ValueError(func)

    def read(self) -> float:
        # Single reading using READ?
        s = self.visa.query(":READ?")
        return float(s.split(",")[0])

    def fetch(self) -> float:
        return float(self.visa.query(":FETC?"))

    def close(self) -> None:
        self.visa.close()
