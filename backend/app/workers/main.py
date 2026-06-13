"""
Entrypoint mínimo del worker (placeholder).
La tecnología real de la cola (asyncio / Celery / ARQ) se define en ADR-003.
"""

import asyncio


async def main():
    """Loop no-op placeholder."""
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())