from __future__ import annotations

"""drivers.fluke5720a

Драйвер Fluke 5720A (калибратор/источник).

В проекте используется как источник напряжения (когда use_5720a_as_voltage_source=true):
- reset(), idn()
- standby()
- set_dcv(volts), oper() (если реализовано в файле)

Команды соответствуют справочнику Remote Programming Reference Guide.
"""

from dataclasses import dataclass
from typing import Optional
from .visa_base import VisaInstrument, VisaConfig

@dataclass
class Fluke5720A:
    """Минимальный драйвер Fluke 5720A (серия 5700A/5720A).

В 57xx команды НЕ SCPI. Типовые:
- *RST, *CLS
- STBY / OPER (standby/operate)
- OUT <value> [unit]  (например: OUT 10 V, OUT 100 mV, OUT 10 mA)
- RANG <value> [unit] (по необходимости) или AUTO
- Функции часто задаются самим OUT с единицами.

Т.к. у разных прошивок/настроек синтаксис может отличаться, в методах ниже
команды собраны в одном месте и легко правятся.
"""
    visa: VisaInstrument

    @classmethod
    def open(cls, resource: str, cfg: VisaConfig) -> "Fluke5720A":
        return cls(VisaInstrument(resource, cfg))

    def reset(self) -> None:
        try:
            self.visa.write("*RST")
        except Exception:
            pass
        try:
            self.visa.write("*CLS")
        except Exception:
            pass
        # best-effort standby
        try:
            self.visa.write("STBY")
        except Exception:
            pass

    def idn(self) -> str:
        for cmd in ("*IDN?", "IDN?", "ID?"):
            try:
                s=self.visa.query(cmd).strip()
                if s:
                    return s
            except Exception:
                continue
        return ""

    def standby(self) -> None:
        self.visa.write("STBY")

    def operate(self) -> None:
        self.visa.write("OPER")

    def out_dcv(self, value_v: float) -> None:
        # Use explicit unit V
        self.visa.write(f"OUT {value_v} V")

    def out_dci(self, value_a: float) -> None:
        # Use explicit unit A
        self.visa.write(f"OUT {value_a} A")

    def out_ohms(self, value_ohm: float) -> None:
        self.visa.write(f"OUT {value_ohm} OHM")

    def close(self) -> None:
        self.visa.close()
