from __future__ import annotations

"""drivers.hp3458a

Драйвер HP/Agilent 3458A (эталонный DMM).

Ключевая особенность: 3458A плохо совместим с SCPI-командой READ? на части конфигураций.
Поэтому драйвер работает в стиле "как на примере":

- конфигурация: PRESET NORM, DCV/DCI, NDIG 8, RANGE, NPLC, AZERO, HIZ
- измерение: TRIG SGL -> read() -> парсинг числа

Также реализован автоподбор фиксированных диапазонов DCV/DCI (минимально достаточный).
"""


from dataclasses import dataclass
from typing import Optional
import re
import time

from .visa_base import VisaInstrument, VisaConfig

def _map_dcv_range(v_abs: float) -> float:
    """Map requested DCV range/value to one of: 0.120, 1.2, 12, 120, 1050 V."""
    v = abs(float(v_abs))
    if v <= 0.120:
        return 0.120
    if v <= 1.2:
        return 1.2
    if v <= 12.0:
        return 12.0
    if v <= 120.0:
        return 120.0
    return 1050.0

def _map_dci_range(i_abs: float) -> float:
    """Map requested DCI range/value to one of:
    120 nA, 1.2 uA, 12 uA, 120 uA, 1.2 mA, 12 mA, 120 mA, 1.05 A (returned in amperes).
    """
    i = abs(float(i_abs))
    if i <= 120e-9:
        return 120e-9
    if i <= 1.2e-6:
        return 1.2e-6
    if i <= 12e-6:
        return 12e-6
    if i <= 120e-6:
        return 120e-6
    if i <= 1.2e-3:
        return 1.2e-3
    if i <= 12e-3:
        return 12e-3
    if i <= 120e-3:
        return 120e-3
    return 1.05

_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?")

def _parse_first_float(s: str) -> float:
    s = s.strip().replace("\r", "").replace("\n", "")
    m = _NUM_RE.search(s)
    if not m:
        raise ValueError(f"3458A: cannot parse numeric from: {s!r}")
    return float(m.group(0))

@dataclass
class HP3458A:
    """HP/Agilent 3458A driver (GPIB) using the style from your example.

    Pattern:
      - configure with PRESET NORM, DCV/DCI, NDIG 8, etc.
      - trigger with TRIG SGL
      - read with instrument read() (not SCPI READ?)

    This avoids 3458A incompatibilities with READ?/FETCH? on some setups.
    """
    visa: VisaInstrument

    @classmethod
    def open(cls, resource: str, cfg: VisaConfig) -> "HP3458A":
        inst = VisaInstrument(resource, cfg)
        try:
            inst.inst.write_termination = "\n"
            inst.inst.read_termination = "\n"
        except Exception:
            pass
        return cls(inst)

    # ---- basic io ----
    def write(self, cmd: str) -> None:
        self.visa.write(cmd)

    def query(self, cmd: str) -> str:
        return self.visa.query(cmd)

    def _read_text(self) -> str:
        return self.visa.inst.read()

    # ---- identification / reset ----
    def idn(self) -> str:
        for cmd in ("ID?", "IDN?"):
            try:
                s = self.query(cmd).strip()
                if s:
                    return s
            except Exception:
                pass
        return "HP3458A"

    def reset(self) -> None:
        self.write("PRESET NORM")
        try:
            self.write("END ALWAYS")
        except Exception:
            pass
        try:
            self.write("AZERO ON")
        except Exception:
            pass

    # ---- config helpers ----
    def _set_range_and_nplc(self, mrange: Optional[float], nplc: float) -> None:
        if mrange is None:
            try:
                self.write("ARANGE ON")
            except Exception:
                pass
        else:
            self.write(f"RANGE {mrange}")
        self.write(f"NPLC {nplc}")

    def _autozero(self, on: bool) -> None:
        self.write(f"AZERO {'ON' if on else 'OFF'}")

    def _hiz(self, on: bool) -> None:
        try:
            self.write(f"FIXEDZ {'OFF' if on else 'ON'}")
        except Exception:
            pass

    # ---- configuration like your screenshots ----
    def conf_function_DCV(self, mrange: Optional[float] = None, nplc: float = 100,
                          AutoZero: bool = True, HiZ: bool = True, channel: int = 1) -> None:
        self.write("PRESET NORM")
        self.write("DCV")
        self.write("NDIG 8")
        self.write("TRIG SGL")
        self._set_range_and_nplc(mrange, nplc)
        self._autozero(AutoZero)
        self._hiz(HiZ)

    def conf_function_DCI(self, mrange: Optional[float] = None, nplc: float = 100,
                          AutoZero: bool = True, HiZ: bool = True, channel: int = 1) -> None:
        self.write("PRESET NORM")
        self.write("DCI")
        self.write("NDIG 8")
        self.write("TRIG SGL")
        self._set_range_and_nplc(mrange, nplc)
        self._autozero(AutoZero)
        self._hiz(HiZ)

    # ---- read ----
    def get_reading(self, channel: Optional[int] = None) -> float:
        self.write("TRIG SGL")
        time.sleep(0.02)
        s = self._read_text()
        return _parse_first_float(s)

    # Compatibility with project procedures:
    def config_dcv(self, rng_v: float, nplc: float = 10.0) -> None:
        self.conf_function_DCV(mrange=_map_dcv_range(rng_v), nplc=nplc, AutoZero=True, HiZ=True)

    def config_dci(self, rng_a: float, nplc: float = 10.0) -> None:
        self.conf_function_DCI(mrange=_map_dci_range(rng_a), nplc=nplc, AutoZero=True, HiZ=False)

    def read(self) -> float:
        return self.get_reading()

    def close(self) -> None:
        self.visa.close()
