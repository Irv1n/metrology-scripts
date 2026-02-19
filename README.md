# Keithley 6430 / Remote PreAmp — Verification (Manual Section 18)

Проект разделён на:
- `drivers/` — драйвера приборов (K6430, HP3458A, Fluke 5720A)
- `procedures/` — процедуры верификации по разделу 18 (включая все таблицы 18-1 … 18-16)
- `config/` — YAML-конфиг адресов GPIB и параметров
- `run_verification.py` — основной запуск

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_verification.py --config config/instruments.yaml
```

## Важно
- 5156 и наборы резисторов подключаются вручную — скрипт будет выдавать подсказки (что куда подключить).
- В местах, где мануал говорит "closest value" (если нельзя установить точное значение), скрипт:
  1) пытается установить целевое значение,
  2) читает фактический setpoint у 6430 (или использует округление по шагу),
  3) пересчитывает лимиты симметричным сдвигом относительно номинала.
