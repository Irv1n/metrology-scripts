from __future__ import annotations

"""procedures.safety

Безопасное завершение работы приборов (best-effort).

Зачем:
- Во время верификации оператор может нажать Ctrl+C.
- Может произойти исключение (GPIB timeout, неверная команда, разрыв связи).
- НЕЛЬЗЯ оставлять приборы с включенным выходом (6430 source ON, 5720A в OPER и т.п.).

Политика:
- Всегда пытаться выключить выходы/перевести в standby.
- Всегда пытаться закрыть VISA-сессии.
- Любые ошибки при shutdown подавляются (best-effort), чтобы shutdown не ломал завершение.
"""


def safe_shutdown(k=None, dmm=None, src=None) -> None:
    """Best-effort safe shutdown.

    Parameters
    ----------
    k:
        Экземпляр K6430 или None.
    dmm:
        Экземпляр HP3458A или None.
    src:
        Экземпляр Fluke5720A или None.

    Логика:
    - Если объект существует, вызываем "безопасные" методы:
        - 6430: output(False)
        - 5720A: standby()
    - Затем закрываем VISA-сессии (close()).
    """
    print("\n--- SAFE SHUTDOWN START ---")
    try:
        if k is not None:
            try:
                k.output(False)
                print("6430 -> OUTPUT OFF")
            except Exception:
                pass
        if src is not None:
            try:
                src.standby()
                print("5720A -> STBY")
            except Exception:
                pass
    finally:
        for name, inst in (("3458A", dmm), ("5720A", src), ("6430", k)):
            if inst is None:
                continue
            try:
                inst.close()
                print(f"{name} -> CLOSE")
            except Exception:
                pass
    print("--- SAFE SHUTDOWN DONE ---")
