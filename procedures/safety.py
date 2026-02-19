from __future__ import annotations

def safe_shutdown(k=None, dmm=None, src=None) -> None:
    """Best-effort safe shutdown.
    Ensures outputs are disabled and VISA sessions are closed even if exceptions happen.
    """
    print("\n--- SAFE SHUTDOWN START ---")

    # Keithley 6430: output OFF
    try:
        if k is not None:
            print("6430 -> OUTPUT OFF")
            try:
                k.output(False)
            except Exception:
                # fallback direct command if needed
                try:
                    k.visa.write(":OUTP OFF")
                except Exception:
                    pass
    except Exception as e:
        print("6430 shutdown error:", e)

    # Fluke 5720A: STBY
    try:
        if src is not None:
            print("5720A -> STBY")
            try:
                src.standby()
            except Exception:
                try:
                    src.visa.write("STBY")
                except Exception:
                    pass
    except Exception as e:
        print("5720A shutdown error:", e)

    # Close instruments (order doesn't matter)
    for name, inst in (("3458A", dmm), ("5720A", src), ("6430", k)):
        try:
            if inst is not None:
                print(f"{name} -> CLOSE")
                inst.close()
        except Exception:
            pass

    print("--- SAFE SHUTDOWN DONE ---\n")
