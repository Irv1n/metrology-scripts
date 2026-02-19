from __future__ import annotations

"""drivers.visa_base

Минимальная обёртка над PyVISA.

Зачем этот файл:
- В одном месте описать, как проект открывает GPIB/USB/LAN ресурсы через PyVISA.
- Спрятать детали ResourceManager (backend) и таймаутов.
- Дать единый объект (VisaInstrument), который остальные драйверы используют для write/query/read.

Важные термины:
- *resource* — VISA-строка ресурса, например: "GPIB0::23::INSTR".
- *backend* — какой драйвер PyVISA использовать.
    - "@py"  -> pyvisa-py (часто вместе с linux-gpib на Raspberry Pi)
    - ""/None -> системный NI-VISA (если установлен)
- *timeout_ms* — таймаут на операции чтения/запроса в миллисекундах.
"""

from dataclasses import dataclass
import pyvisa


@dataclass
class VisaConfig:
    """Параметры подключения к VISA.

    Attributes
    ----------
    backend:
        Строка backend для pyvisa.ResourceManager().
        Обычно:
        - "@py" для pyvisa-py
        - "" (пусто) чтобы PyVISA выбрал backend по умолчанию (NI-VISA).
    timeout_ms:
        Таймаут на ответ прибора для операций чтения/запроса.
    """
    backend: str = "@py"
    timeout_ms: int = 15000


class VisaInstrument:
    """Тонкая обёртка над pyvisa.resources.MessageBasedResource.

    Использование:
        inst = VisaInstrument("GPIB0::23::INSTR", VisaConfig("@py", 15000))
        inst.write("RESET")
        val = inst.query("ID?")
        inst.close()

    В проекте:
    - Каждый конкретный драйвер (K6430/HP3458A/Fluke5720A) хранит у себя поле `visa: VisaInstrument`.
    - Это упрощает тестирование и безопасное выключение в finally.
    """

    def __init__(self, resource: str, cfg: VisaConfig):
        # ResourceManager — "фабрика" для открытия ресурсов.
        rm = pyvisa.ResourceManager(cfg.backend) if cfg.backend else pyvisa.ResourceManager()

        # Открываем сам ресурс (например, GPIB адрес).
        self.inst = rm.open_resource(resource)

        # Таймауты для операций чтения/запросов.
        self.inst.timeout = cfg.timeout_ms

        # Терминаторы для текстового протокола (часто полезно).
        # Некоторые приборы лучше работают без жёсткой read_termination — тогда драйвер может переопределить.
        try:
            self.inst.write_termination = "\n"
            self.inst.read_termination = "\n"
        except Exception:
            pass

    def write(self, cmd: str) -> None:
        """Отправить команду прибору (без ожидания ответа)."""
        self.inst.write(cmd)

    def query(self, cmd: str) -> str:
        """Отправить команду и прочитать ответ одной строкой."""
        return self.inst.query(cmd)

    def close(self) -> None:
        """Закрыть VISA-сессию (best-effort)."""
        try:
            self.inst.close()
        except Exception:
            pass
