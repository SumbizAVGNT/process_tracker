from __future__ import annotations
import asyncio

from . import bootstrap_db

async def main():
    await bootstrap_db()

if __name__ == "__main__":
    asyncio.run(main())
