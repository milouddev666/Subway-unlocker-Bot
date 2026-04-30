from __future__ import annotations


def ar(text: str) -> str:
    """Decode mojibake Arabic text into proper UTF-8 at runtime.

    The workspace shell on Windows can mangle Arabic literals while editing.
    Routing those literals through this helper keeps the source maintainable
    and ensures the bot renders Arabic correctly for users.
    """

    current = text
    for _ in range(3):
        try:
            decoded = current.encode("cp1256").decode("utf-8")
        except UnicodeError:
            break
        if decoded == current:
            break
        current = decoded
    return current
