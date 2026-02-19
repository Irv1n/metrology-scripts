from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Все таблицы раздела 18 (18-1 ... 18-16) забиты здесь как данные.
# Значения извлечены из Keithley 6430 Reference Manual (Jan 2021) раздел 18.

@dataclass(frozen=True)
class LimitRow:
    range_name: str
    set_value: float
    low: float
    high: float
    unit: str

def shift_limits(nominal: float, low: float, high: float, actual: float) -> tuple[float,float]:
    """'Closest value' пересчёт лимитов:
    сохраняем расстояния до нижнего/верхнего лимита относительно номинала,
    и переносим их на фактическое установленное значение.
    """
    d_lo = nominal - low
    d_hi = high - nominal
    return actual - d_lo, actual + d_hi

# --- Table 18-2 (Maximum compliance values) ---
TABLE_18_2_COMPLIANCE = {
    # measurement range -> max compliance
    "200mV": ("V", 0.210),
    "2V": ("V", 2.1),
    "20V": ("V", 21.0),
    "200V": ("V", 210.0),
    "1pA": ("A", 1.05e-12),
    "10pA": ("A", 10.5e-12),
    "100pA": ("A", 105e-12),
    "1nA": ("A", 1.05e-9),
    "10nA": ("A", 10.5e-9),
    "100nA": ("A", 105e-9),
    "1uA": ("A", 1.05e-6),
    "10uA": ("A", 10.5e-6),
    "100uA": ("A", 105e-6),
    "1mA": ("A", 1.05e-3),
    "10mA": ("A", 10.5e-3),
    "100mA": ("A", 0.105),
}

# --- Table 18-3 Mainframe output voltage accuracy limits ---
TABLE_18_3_MAINFRAME_OUT_V = [
    LimitRow("200mV", 0.200000, 0.199360, 0.200640, "V"),
    LimitRow("2V",    2.00000,  1.99900,  2.00100,  "V"),
    LimitRow("20V",   20.0000,  19.9936,  20.0064,  "V"),
    LimitRow("200V",  200.000,  199.936,  200.064,  "V"),
]

# --- Table 18-4 Mainframe voltage measurement accuracy limits ---
TABLE_18_4_MAINFRAME_MEAS_V = [
    LimitRow("200mV", 0.200000, 0.199626, 0.200374, "V"),
    LimitRow("2V",    2.00000,  1.99941,  2.00059,  "V"),
    LimitRow("20V",   20.0000,  19.9955,  20.0045,  "V"),
    LimitRow("200V",  200.000,  199.960,  200.040,  "V"),
]

# --- Table 18-5 Mainframe output current accuracy limits ---
TABLE_18_5_MAINFRAME_OUT_I = [
    LimitRow("1uA",   1.00000e-6, 0.99905e-6, 1.00095e-6, "A"),
    LimitRow("10uA",  10.0000e-6, 9.9947e-6,  10.0053e-6, "A"),
    LimitRow("100uA", 100.000e-6, 99.949e-6,  100.051e-6, "A"),
    LimitRow("1mA",   1.00000e-3, 0.99946e-3, 1.00054e-3, "A"),
    LimitRow("10mA",  10.0000e-3, 9.9935e-3,  10.0065e-3, "A"),
    LimitRow("100mA", 0.100000,   0.099914,   0.100086,   "A"),
]

# --- Table 18-6 Mainframe current measurement accuracy limits ---
TABLE_18_6_MAINFRAME_MEAS_I = [
    LimitRow("1uA",   1.000000e-6, 0.99920e-6, 1.00080e-6, "A"),
    LimitRow("10uA",  10.00000e-6, 9.9930e-6,  10.0070e-6, "A"),
    LimitRow("100uA", 100.000e-6,  99.969e-6,  100.031e-6, "A"),
    LimitRow("1mA",   1.00000e-3,  0.99967e-3, 1.00033e-3, "A"),
    LimitRow("10mA",  10.0000e-3,  9.9959e-3,  10.0041e-3, "A"),
    LimitRow("100mA", 0.100000,    0.099939,   0.100061,   "A"),
]

# --- Table 18-7 Mainframe resistance measurement accuracy limits ---
# NOTE: эти лимиты рассчитаны с учетом 5450A в мануале; у тебя 5156+ручные резисторы.
# Мы используем сами лимиты как "проверочные границы" (как в мануале). Если хочешь учесть
# другие эталоны/неопределенности — можно пересчитать (скрипт умеет shift_limits).
TABLE_18_7_MAINFRAME_MEAS_R = [
    LimitRow("20Ω",   19.0,    18.920,   19.080,   "OHM"),
    LimitRow("200Ω",  190.0,   189.950,  190.050,  "OHM"),
    LimitRow("2kΩ",   1900.0,  1899.70,  1900.30,  "OHM"),
    LimitRow("20kΩ",  19000.0, 18997.0,  19003.0,  "OHM"),
    LimitRow("200kΩ", 190000.0,189960.0, 190040.0, "OHM"),
    LimitRow("2MΩ",   1.9e6,   1.89950e6,1.90050e6,"OHM"),
    LimitRow("20MΩ",  19e6,    18.9950e6,19.0050e6,"OHM"),
]

# --- Table 18-8 Remote PreAmp output voltage accuracy limits ---
TABLE_18_8_PREAMP_OUT_V = [
    LimitRow("200mV", 0.200000, 0.199360, 0.200640, "V"),
    LimitRow("2V",    2.00000,  1.99900,  2.00100,  "V"),
    LimitRow("20V",   20.0000,  19.9936,  20.0064,  "V"),
    LimitRow("200V",  200.000,  199.936,  200.064,  "V"),
]

# --- Table 18-9 Remote PreAmp voltage measurement accuracy limits ---
TABLE_18_9_PREAMP_MEAS_V = [
    LimitRow("200mV", 0.200000, 0.199626, 0.200374, "V"),
    LimitRow("2V",    2.00000,  1.99941,  2.00059,  "V"),
    LimitRow("20V",   20.0000,  19.9955,  20.0045,  "V"),
    LimitRow("200V",  200.000,  199.960,  200.040,  "V"),
]

# --- Table 18-10 Remote PreAmp 1uA-100mA range output current accuracy limits ---
TABLE_18_10_PREAMP_OUT_I = [
    LimitRow("1uA",   1.00000e-6, 0.99920e-6, 1.00080e-6, "A"),
    LimitRow("10uA",  10.0000e-6, 9.9930e-6,  10.0070e-6, "A"),
    LimitRow("100uA", 100.000e-6, 99.949e-6,  100.051e-6, "A"),
    LimitRow("1mA",   1.00000e-3, 0.99946e-3, 1.00054e-3, "A"),
    LimitRow("10mA",  10.0000e-3, 9.9935e-3,  10.0065e-3, "A"),
    LimitRow("100mA", 0.100000,   0.099914,   0.100086,   "A"),
]

# --- Table 18-11 Remote PreAmp 1pA-100nA range output current accuracy limits ---
# (limits include 5156 characterization accuracy)
TABLE_18_11_PREAMP_OUT_I_LOW = [
    # range, standard resistor, setpoint, limits
    ("1pA",   100e9,  1.00000e-12, 0.97950e-12, 1.02050e-12),
    ("10pA",  100e9,  10.0000e-12, 9.9150e-12,  10.0085e-12),
    ("100pA", 10e9,   100.000e-12, 99.770e-12,  100.230e-12),
    ("1nA",   1e9,    1.00000e-9,  0.99900e-9,  1.00100e-9),
    ("10nA",  1e9,    10.0000e-9,  9.9990e-9,   10.0100e-9),
    ("100nA", 100e6,  100.000e-9,  99.910e-9,   100.090e-9),
]

# --- Table 18-12 Remote PreAmp 1uA-100mA range measurement accuracy limits ---
TABLE_18_12_PREAMP_MEAS_I = TABLE_18_6_MAINFRAME_MEAS_I

# --- Table 18-13 Remote PreAmp 1pA-100nA range measurement accuracy limits ---
TABLE_18_13_PREAMP_MEAS_I_LOW = [
    ("1pA",   100e9,  1.000000e-12, 0.98300e-12, 1.01700e-12),
    ("10pA",  100e9,  10.00000e-12, 9.9430e-12,  10.0570e-12),
    ("100pA", 10e9,   100.000e-12,  99.820e-12,  100.180e-12),
    ("1nA",   1e9,    1.00000e-9,   0.99930e-9,  1.00070e-9),
    ("10nA",  1e9,    10.0000e-9,   9.9930e-9,   10.0070e-9),
    ("100nA", 100e6,  100.000e-9,   99.930e-9,   100.070e-9),
]

# --- Table 18-14 Remote PreAmp 20Ω-200MΩ range measurement accuracy limits ---
TABLE_18_14_PREAMP_MEAS_R_LOW = [
    # (range label, resistance value, low, high)
    ("20Ω",   19.0,     18.920,     19.080),
    ("200Ω",  190.0,    189.950,    190.050),
    ("2kΩ",   1900.0,   1899.70,    1900.30),
    ("20kΩ",  19000.0,  18997.0,    19003.0),
    ("200kΩ", 190000.0, 189960.0,   190040.0),
    ("2MΩ",   1.9e6,    1.89950e6,  1.90050e6),
    ("20MΩ",  19e6,     18.9950e6,  19.0050e6),
    ("200MΩ", 190e6,    189.916e6,  190.084e6),
]

# --- Table 18-15 Remote PreAmp 2GΩ-200GΩ range measurement accuracy limits ---
TABLE_18_15_PREAMP_MEAS_R_HIGH = [
    ("2GΩ",   1e9,   2.00000e9, 1.9200e9, 2.0800e9),
    ("20GΩ",  10e9,  20.0000e9, 19.503e9, 20.497e9),
    ("200GΩ", 100e9, 200.000e9, 195.03e9, 204.97e9),
]

# --- Table 18-16 Remote PreAmp 2TΩ and 20TΩ range measurement accuracy limits ---
TABLE_18_16_PREAMP_MEAS_R_T = [
    ("2TΩ",   1e12,  2.00000e12, 1.9110e12, 2.0890e12),
    ("20TΩ",  10e12, 20.0000e12, 18.890e12, 21.110e12),
]
