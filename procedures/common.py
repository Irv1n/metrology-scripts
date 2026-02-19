from __future__ import annotations

"""procedures.common

Общие утилиты и структуры данных для процедур раздела 18.

Этот файл делает две вещи:
1) Дает простые математические функции (mean/stdev) и проверки (within).
2) Описывает структуру результата измерения `PointResult`, которая потом
   конвертируется в таблицу (pandas.DataFrame) и сохраняется в CSV.

Почему PointResult важен:
- Каждая "точка" из таблиц Section 18 превращается в одну строку CSV.
- В строке есть: что мы проверяли, какой диапазон, какое было задано значение,
  что показал эталон (DMM 3458A), что показал DUT (Keithley 6430), лимиты и PASS/FAIL.
- Для трассируемости low-current точек добавлены r_key/r_nom_ohm/r_act_ohm.
"""

from dataclasses import dataclass
from typing import List
import math
import pandas as pd


def mean(xs: List[float]) -> float:
    """Среднее арифметическое.

    Parameters
    ----------
    xs:
        Список измерений (например, несколько считываний с 3458A).

    Returns
    -------
    float
        Среднее значение. Если список пустой — NaN.
    """
    return sum(xs) / len(xs) if xs else float("nan")


def stdev(xs: List[float]) -> float:
    """Выборочное стандартное отклонение (N-1).

    Зачем:
    - В CSV удобно видеть разброс значений по точке.
    - Это НЕ бюджет неопределенности, а просто статистика серии.

    Если точек меньше 2 — возвращаем 0.0.
    """
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def within(x: float, lo: float, hi: float) -> bool:
    """Проверка попадания x в интервал [lo, hi]."""
    return (x >= lo) and (x <= hi)


def prompt(msg: str) -> None:
    """Вывести оператору подсказку и ждать Enter.

    Процедура Section 18 содержит ручные шаги (переключение кабелей, подключение 5156 и т.п.).
    Этот helper делает одинаковое поведение по всему проекту.
    """
    print("\n" + msg)
    input("Нажми Enter чтобы продолжить...")


@dataclass
class PointResult:
    """Результат одной проверки (одна строка CSV).

    Поля разделены на 3 смысловые группы:

    A) Идентификация проверки
    ------------------------
    test:
        Короткий идентификатор теста/таблицы, например:
        - "MF_OUT_V"  -> Table 18-3 Mainframe output voltage accuracy
        - "MF_MEAS_V" -> Table 18-4 Mainframe voltage measurement accuracy
        - "PA_OUT_I_LOW" -> Table 18-11 Remote PreAmp low current source output
        и т.д.
    range_name:
        Человеческое имя диапазона, как в таблице (например "200V", "10mA", "1pA").

    B) Численные данные точки
    -------------------------
    set_value:
        Номинал/цель точки из таблицы (что "хотели" установить).
        Например 10.0 V или 1e-9 A.
    actual_set:
        "Фактическое" значение источника, измеренное эталоном (3458A),
        или вычисленное по V/R (для низких токов).
        Используется для алгоритма closest-value (сдвиг лимитов).
    dmm_mean, dmm_stdev:
        Среднее и СКО эталонного измерения (обычно 3458A).
        Для некоторых тестов может совпадать с actual_set.
    dut_mean, dut_stdev:
        Среднее и СКО показаний DUT (Keithley 6430), если в этом тесте DUT измеряет.
        Если в тесте DUT только "источник", эти поля могут быть NaN.

    C) Лимиты и вердикт
    -------------------
    low, high:
        Нижний/верхний предел допуска для PASS/FAIL.
        Важно: в проекте реализован "closest value" — лимиты сдвигаются относительно
        фактического значения (actual_set), если оно отличается от номинала.
    unit:
        Единицы ("V"/"A"/"Ohm" и т.д.) — удобно для Excel.
    pass_fail:
        "PASS" или "FAIL".

    Дополнительно: трассируемость 5156 (для low current)
    ----------------------------------------------------
    r_key:
        Ключ из YAML (вариант A): "100M", "1G", "10G", "100G".
    r_nom_ohm:
        Номинал сопротивления из таблицы (например 100e9).
    r_act_ohm:
        Действительное (characterized) значение из YAML, используемое в расчёте I = V/R.
    """

    # required fields (без default)
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

    # traceability fields (defaults)
    r_key: str | None = None
    r_nom_ohm: float | None = None
    r_act_ohm: float | None = None


def to_dataframe(results: List[PointResult]) -> pd.DataFrame:
    """Преобразовать список результатов в pandas.DataFrame.

    Это делает сохранение в CSV предельно простым:
        df = to_dataframe(results)
        df.to_csv(...)

    Важно: мы используем __dict__, поэтому новые поля автоматически появляются в CSV.
    """
    return pd.DataFrame([r.__dict__ for r in results])
