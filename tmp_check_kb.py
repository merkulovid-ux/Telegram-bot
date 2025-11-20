import asyncio
from kb_metadata import get_kb_structure

async def main():
    data = await get_kb_structure(force_refresh=True)
    for item in data:
        print(f"{item.name}: {len(item.topics)} topics")
        for topic in item.topics:
            print('  -', topic)
asyncio.run(main())
