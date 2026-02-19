from __future__ import annotations

"""procedures.section18

Реализация процедур верификации по разделу 18.

Содержит:
- ProcCfg: параметры измерений (NPLC, задержки, число отсчётов)
- _sample_readings(): снятие серии измерений
- shift_limits(): алгоритм "closest value" (сдвиг лимитов)
- verify_*(): функции, соответствующие таблицам раздела 18

Функции verify_* выводят оператору подсказки по подключению и выполняют измерения.
Результат каждой точки записывается как PointResult (см. procedures.common).
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import time

from drivers.k6430 import K6430
from drivers.hp3458a import HP3458A
from drivers.fluke5720a import Fluke5720A

from .tables_section18 import (
    LimitRow,
    shift_limits,
    TABLE_18_3_MAINFRAME_OUT_V,
    TABLE_18_4_MAINFRAME_MEAS_V,
    TABLE_18_5_MAINFRAME_OUT_I,
    TABLE_18_6_MAINFRAME_MEAS_I,
    TABLE_18_7_MAINFRAME_MEAS_R,
    TABLE_18_8_PREAMP_OUT_V,
    TABLE_18_9_PREAMP_MEAS_V,
    TABLE_18_10_PREAMP_OUT_I,
    TABLE_18_11_PREAMP_OUT_I_LOW,
    TABLE_18_12_PREAMP_MEAS_I,
    TABLE_18_13_PREAMP_MEAS_I_LOW,
    TABLE_18_14_PREAMP_MEAS_R_LOW,
    TABLE_18_15_PREAMP_MEAS_R_HIGH,
    TABLE_18_16_PREAMP_MEAS_R_T,
)
from .common import PointResult, mean, stdev, within, prompt

@dataclass
class ProcCfg:
    settle_s: float = 1.0
    nplc_3458: float = 10
    samples_per_point: int = 5
    sample_delay_s: float = 0.2
    use_5720a_as_voltage_source: bool = False

def _sample_readings(read_fn, n: int, delay_s: float) -> list[float]:
    xs=[]
    for _ in range(n):
        xs.append(float(read_fn()))
        time.sleep(delay_s)
    return xs

def verify_mainframe_output_voltage(k: K6430, dmm: HP3458A, cfg: ProcCfg) -> List[PointResult]:
    prompt("MAINFRAME output voltage accuracy (Table 18-3):\n"
           "Подключи 3458A к INPUT/OUTPUT HI/LO 6430 (Figure 18-2).\n"
           "На 6430: SOURCE V, OUTPUT ON. На 3458A: DCV.")
    results=[]
    k.output(True)

    # Set 3458A range per point (0.120/1.2/12/120/1050 V)

    for row in TABLE_18_3_MAINFRAME_OUT_V:
        # 3458A range: smallest that covers the point
        dmm.config_dcv(row.set_value, cfg.nplc_3458)

        # set nominal
        k.source_v(row.set_value, rng=row.set_value*1.2 if row.set_value<200 else 200)
        time.sleep(cfg.settle_s)

        # DMM reading of actual source
        xs=_sample_readings(dmm.read, cfg.samples_per_point, cfg.sample_delay_s)
        actual=mean(xs)

        # Shift limits if actual differs (closest value)
        lo, hi = shift_limits(row.set_value, row.low, row.high, actual)

        passfail = "PASS" if within(actual, lo, hi) else "FAIL"
        results.append(PointResult(
            test="MF_OUT_V",
            range_name=row.range_name,
            set_value=row.set_value,
            actual_set=actual,
            dmm_mean=actual,
            dmm_stdev=stdev(xs),
            dut_mean=float("nan"),
            dut_stdev=float("nan"),
            low=lo, high=hi, unit=row.unit, pass_fail=passfail
        ))
    k.output(False)
    return results
    

def verify_mainframe_measure_voltage(k: K6430, dmm: HP3458A, src: Optional[Fluke5720A], cfg: ProcCfg) -> List[PointResult]:
    prompt("MAINFRAME voltage measurement accuracy (Table 18-4):\n"
           "Подключи 3458A к INPUT/OUTPUT HI/LO 6430 (Figure 18-2).\n"
           "На 6430: SOURCE V + MEAS V, OUTPUT ON. На 3458A: DCV.\n"
           "Если включено use_5720a_as_voltage_source=true, то источник будет 5720A (иначе 6430 сам).")
    results=[]
    # 3458A range will be set per point
    k.output(True)
    if cfg.use_5720a_as_voltage_source and src is not None:
        src.operate()

    for row in TABLE_18_4_MAINFRAME_MEAS_V:
        if cfg.use_5720a_as_voltage_source and src is not None:
            src.out_dcv(row.set_value)
            time.sleep(cfg.settle_s)
            xs=_sample_readings(dmm.read, cfg.samples_per_point, cfg.sample_delay_s)
            actual=mean(xs)
            # 6430 in MEAS V only:
            k.sense_func("VOLT")
            # read DUT
            dut=_sample_readings(k.read, cfg.samples_per_point, cfg.sample_delay_s)
            dut_m=mean(dut)
            lo,hi=shift_limits(row.set_value,row.low,row.high,actual)
        else:
            k.source_v(row.set_value, rng=row.set_value*1.2 if row.set_value<200 else 200)
            k.sense_func("VOLT")
            time.sleep(cfg.settle_s)
            xs=_sample_readings(dmm.read, cfg.samples_per_point, cfg.sample_delay_s)
            actual=mean(xs)
            dut=_sample_readings(k.read, cfg.samples_per_point, cfg.sample_delay_s)
            dut_m=mean(dut)
            lo,hi=shift_limits(row.set_value,row.low,row.high,actual)

        passfail="PASS" if within(dut_m, lo, hi) else "FAIL"
        results.append(PointResult(
            test="MF_MEAS_V",
            range_name=row.range_name,
            set_value=row.set_value,
            actual_set=actual,
            dmm_mean=actual,
            dmm_stdev=stdev(xs),
            dut_mean=dut_m,
            dut_stdev=stdev(dut),
            low=lo, high=hi, unit=row.unit, pass_fail=passfail
        ))
    if cfg.use_5720a_as_voltage_source and src is not None:
        src.standby()
    k.output(False)
    return results
    
def verify_mainframe_output_current(k: K6430, dmm: HP3458A, cfg: ProcCfg) -> List[PointResult]:
    prompt("MAINFRAME output current accuracy (Table 18-5):\n"
           "Подключи 3458A (AMPS/INPUT LO) к INPUT/OUTPUT HI/LO 6430 (Figure 18-3).\n"
           "На 6430: SOURCE I, OUTPUT ON. На 3458A: DCI.")
    results=[]
    # range on 3458A depends; set large
    dmm.config_dci(row.set_value, cfg.nplc_3458)
    k.output(True)

    for row in TABLE_18_5_MAINFRAME_OUT_I:
        k.source_i(row.set_value, rng=abs(row.set_value)*1.2)
        time.sleep(cfg.settle_s)
        xs=_sample_readings(dmm.read, cfg.samples_per_point, cfg.sample_delay_s)
        actual=mean(xs)
        lo,hi=shift_limits(row.set_value,row.low,row.high,actual)
        passfail="PASS" if within(actual, lo, hi) else "FAIL"
        results.append(PointResult(
            test="MF_OUT_I",
            range_name=row.range_name,
            set_value=row.set_value,
            actual_set=actual,
            dmm_mean=actual, dmm_stdev=stdev(xs),
            dut_mean=float("nan"), dut_stdev=float("nan"),
            low=lo, high=hi, unit=row.unit, pass_fail=passfail
        ))
    return results

def verify_mainframe_measure_current(k: K6430, dmm: HP3458A, cfg: ProcCfg) -> List[PointResult]:
    prompt("MAINFRAME current measurement accuracy (Table 18-6):\n"
           "Подключи 3458A (AMPS/INPUT LO) к INPUT/OUTPUT HI/LO 6430 (Figure 18-3).\n"
           "На 6430: SOURCE I + MEAS I, OUTPUT ON. На 3458A: DCI.")
    results=[]
    dmm.config_dci(row.set_value, cfg.nplc_3458)
    k.output(True)
    k.sense_func("CURR")

    for row in TABLE_18_6_MAINFRAME_MEAS_I:
        k.source_i(row.set_value, rng=abs(row.set_value)*1.2)
        time.sleep(cfg.settle_s)
        xs=_sample_readings(dmm.read, cfg.samples_per_point, cfg.sample_delay_s)
        actual=mean(xs)
        dut=_sample_readings(k.read, cfg.samples_per_point, cfg.sample_delay_s)
        dut_m=mean(dut)
        lo,hi=shift_limits(row.set_value,row.low,row.high,actual)
        passfail="PASS" if within(dut_m, lo, hi) else "FAIL"
        results.append(PointResult(
            test="MF_MEAS_I",
            range_name=row.range_name,
            set_value=row.set_value,
            actual_set=actual,
            dmm_mean=actual, dmm_stdev=stdev(xs),
            dut_mean=dut_m, dut_stdev=stdev(dut),
            low=lo, high=hi, unit=row.unit, pass_fail=passfail
        ))
    k.output(False)
    return results

def verify_remote_preamp_low_current_measurement(k: K6430, dmm: HP3458A, cfg: ProcCfg, r5156_actual: Dict[str, float] | None = None) -> List[PointResult]:
    prompt("REMOTE PREAMP 1pA–100nA range MEASUREMENT accuracy (Table 18-13):\n"
           "Подключения как Figure 18-7: 3458A измеряет напряжение на выходе 5156/резистора.\n"
           "5156 и резисторы подключаются вручную. Скрипт будет просить переключать джек.\n"
           "Алгоритм: измерить V на эталонном R, вычислить I=V/R, выставить I на 6430, проверить показание.")
    results=[]
    dmm.config_dcv(20.0, cfg.nplc_3458)
    k.output(True)
    k.sense_func("CURR")

    for (rng, R_nom, I_nom, lo_nom, hi_nom) in TABLE_18_13_PREAMP_MEAS_I_LOW:
        key = _r_key_from_nominal(R_nom)
        R = float((r5156_actual or {}).get(key, R_nom))
        prompt(f"Подключи BNC shorting cap к нужному джеку 5156 для {rng} (R_nom≈{R_nom:.3g}Ω, R_act={R:.6g}Ω).")
        # Measure V across resistor via DMM
        xs=_sample_readings(dmm.read, cfg.samples_per_point, cfg.sample_delay_s)
        V=mean(xs)
        I_calc = V / R
        # Set 6430 source current to calculated
        k.source_i(I_calc, rng=abs(I_calc)*1.2)
        time.sleep(cfg.settle_s)
        # Read back source setpoint (closest value)
        try:
            I_set = k.source_i_query()
        except Exception:
            I_set = I_calc
        # shift limits from nominal current value (as in table) to actual setpoint
        lo,hi=shift_limits(I_nom, lo_nom, hi_nom, I_set)
        dut=_sample_readings(k.read, cfg.samples_per_point, cfg.sample_delay_s)
        dut_m=mean(dut)
        passfail="PASS" if within(dut_m, lo, hi) else "FAIL"
        results.append(PointResult(
            test="PA_MEAS_I_LOW",
            r_key=key, r_nom_ohm=R_nom, r_act_ohm=R,
            range_name=rng,
            set_value=I_nom,
            actual_set=I_set,
            dmm_mean=V, dmm_stdev=stdev(xs),
            dut_mean=dut_m, dut_stdev=stdev(dut),
            low=lo, high=hi, unit="A", pass_fail=passfail
        ))
    k.output(False)
    return results

def verify_remote_preamp_low_current_output(k: K6430, dmm: HP3458A, cfg: ProcCfg, r5156_actual: Dict[str, float] | None = None) -> List[PointResult]:
    prompt("REMOTE PREAMP 1pA–100nA range OUTPUT current accuracy (Table 18-11):\n"
           "Подключения как Figure 18-7: 3458A измеряет напряжение на эталонном R (5156).\n"
           "Алгоритм: задать I на 6430, измерить V, вычислить I=V/R, сравнить с лимитами.")
    results=[]
    dmm.config_dcv(20.0, cfg.nplc_3458)
    k.output(True)

    for (rng, R_nom, I_nom, lo_nom, hi_nom) in TABLE_18_11_PREAMP_OUT_I_LOW:
        key = _r_key_from_nominal(R_nom)
        R = float((r5156_actual or {}).get(key, R_nom))
        prompt(f"Подключи BNC shorting cap к нужному джеку 5156 для {rng} (R_nom≈{R_nom:.3g}Ω, R_act={R:.6g}Ω).")
        k.source_i(I_nom, rng=abs(I_nom)*1.2)
        time.sleep(cfg.settle_s)
        xs=_sample_readings(dmm.read, cfg.samples_per_point, cfg.sample_delay_s)
        V=mean(xs)
        I_calc = V / R
        # actual setpoint
        try:
            I_set = k.source_i_query()
        except Exception:
            I_set = I_nom
        lo,hi=shift_limits(I_nom, lo_nom, hi_nom, I_set)
        passfail="PASS" if within(I_calc, lo, hi) else "FAIL"
        results.append(PointResult(
            test="PA_OUT_I_LOW",
            r_key=key, r_nom_ohm=R_nom, r_act_ohm=R,
            range_name=rng,
            set_value=I_nom,
            actual_set=I_set,
            dmm_mean=I_calc, dmm_stdev=0.0,
            dut_mean=float("nan"), dut_stdev=float("nan"),
            low=lo, high=hi, unit="A", pass_fail=passfail
        ))
    k.output(False)
    return results
