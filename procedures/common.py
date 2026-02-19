from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time, math
import pandas as pd

def mean(xs: List[float]) -> float:
    return sum(xs)/len(xs) if xs else float("nan")

def stdev(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m=mean(xs)
    return math.sqrt(sum((x-m)**2 for x in xs)/(len(xs)-1))

def within(x: float, lo: float, hi: float) -> bool:
    return (x >= lo) and (x <= hi)

def prompt(msg: str) -> None:
    print("\n" + msg)
    input("Нажми Enter чтобы продолжить...")

@dataclass
class PointResult:
    # --- required fields (no defaults) ---
    test: str
    range_name: str
    set_value: float
    actual_set: float
    dmm_mean: float | None
    dmm_stdev: float | None
    dut_mean: float | None
    dut_stdev: float | None
    low: float
    high: float
    unit: str
    pass_fail: str

    # --- traceability fields (defaults) ---
    r_key: str | None = None
    r_nom_ohm: float | None = None
    r_act_ohm: float | None = None

def to_dataframe(results: List[PointResult]) -> pd.DataFrame:
    return pd.DataFrame([r.__dict__ for r in results])
