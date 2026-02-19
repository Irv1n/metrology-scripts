from __future__ import annotations
"""
run_verification.py

Главный исполняемый сценарий: запускает полный набор проверок раздела 18
для Keithley 6430 (SMU) с использованием эталонов:

- Agilent/HP 3458A (DMM) — измерение напряжения/тока как эталон.
- Fluke 5720A — (опционально) источник напряжения для части проверок.
- Fluke 5156A + высокоомные резисторы — ручное подключение для диапазона 1 pA … 100 nA.

Что делает скрипт по шагам:
1) Читает YAML конфиг (адреса GPIB, параметры измерения, действительные R для 5156).
2) Открывает VISA сессии приборов.
3) Делает reset() приборов.
4) Выполняет процедуры из procedures/section18.py (Table 18-3, 18-4, ...).
5) Сохраняет результаты в CSV:
   - section18_<timestamp>.csv — результаты точек (PASS/FAIL, лимиты, измерения).
   - section18_<timestamp>_standards_5156.csv — какие R_act применялись (трассируемость).
6) При любом завершении (успех / ошибка / Ctrl+C) выполняет safe_shutdown().

Примечание по "closest value":
В некоторых таблицах руководство разрешает не попадать точно в номинал.
Тогда пределы допуска сдвигаются относительно фактического значения эталона.
Эта логика реализована в procedures/section18.shift_limits().
"""
import argparse, yaml, pathlib, datetime
from drivers.visa_base import VisaConfig
from drivers.k6430 import K6430
from drivers.hp3458a import HP3458A
from drivers.fluke5720a import Fluke5720A
from procedures.section18 import (
    ProcCfg,
    verify_mainframe_output_voltage,
    verify_mainframe_measure_voltage,
    verify_mainframe_output_current,
    verify_mainframe_measure_current,
    verify_remote_preamp_low_current_output,
    verify_remote_preamp_low_current_measurement,
)
from procedures.common import to_dataframe
from procedures.safety import safe_shutdown

def main():

    ap=argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instruments.yaml")
    ap.add_argument("--out", default="results")
    args=ap.parse_args()

    cfg=yaml.safe_load(pathlib.Path(args.config).read_text(encoding="utf-8"))

    visa_cfg=VisaConfig(
        backend=str(cfg.get("visa_backend","@py")),
        timeout_ms=int(cfg.get("timeout_ms",15000))
    )

    inst=cfg["instruments"]
    meas=cfg.get("measurement",{})
    proc_cfg=ProcCfg(
        settle_s=float(meas.get("settle_s",1.0)),
        nplc_3458=float(meas.get("nplc_3458",10)),
        samples_per_point=int(meas.get("samples_per_point",5)),
        sample_delay_s=float(meas.get("sample_delay_s",0.2)),
        use_5720a_as_voltage_source=bool(cfg.get("use_5720a_as_voltage_source", False)),
    )

    r5156_actual = cfg.get("standards_5156_actual_ohm", {})

    outdir=pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # IMPORTANT: define variables before try to avoid NameError in except/finally
    k = None
    dmm = None
    src = None

    try:
        k=K6430.open(inst["k6430"]["resource"], visa_cfg)
        dmm=HP3458A.open(inst["hp3458a"]["resource"], visa_cfg)
        if "fluke5720a" in inst:
            src=Fluke5720A.open(inst["fluke5720a"]["resource"], visa_cfg)

        print("K6430:", k.idn())
        print("3458A:", dmm.idn())
        if src: print("5720A:", src.idn())

        k.reset()
        dmm.reset()
        if src: src.reset()

        results=[]
        results += verify_mainframe_output_voltage(k,dmm,proc_cfg)
        results += verify_mainframe_measure_voltage(k,dmm,src,proc_cfg)
        results += verify_mainframe_output_current(k,dmm,proc_cfg)
        results += verify_mainframe_measure_current(k,dmm,proc_cfg)
        results += verify_remote_preamp_low_current_output(k,dmm,proc_cfg, r5156_actual)
        results += verify_remote_preamp_low_current_measurement(k,dmm,proc_cfg, r5156_actual)

        df=to_dataframe(results)
        csv_path=outdir/f"section18_{stamp}.csv"
        df.to_csv(csv_path, index=False)
        print("\nГотово:", csv_path)

        # Traceability: save applied 5156 actual resistors map
        std_rows = []
        for kkey, rval in (r5156_actual or {}).items():
            std_rows.append({"standard": "Fluke5156A", "key": kkey, "R_act_ohm": float(rval)})
        if std_rows:
            import pandas as _pd
            std_df = _pd.DataFrame(std_rows).sort_values("key")
            std_csv = outdir / f"section18_{stamp}_standards_5156.csv"
            std_df.to_csv(std_csv, index=False)
            print("Standards CSV:", std_csv)

    except KeyboardInterrupt:
        print("\n❗ Остановлено пользователем (Ctrl+C).")

    except Exception as e:
        print("\n❗ Ошибка выполнения:", repr(e))
        raise

    finally:
        safe_shutdown(k, dmm, src)


if __name__=="__main__":
    main()
