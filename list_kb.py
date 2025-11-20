import asyncio
import os
from kb_metadata import get_kb_structure

os.environ['YC_SEARCH_INDEX_ID']='fvteqptuu5ecmhc7mqfu'

async def main():
    data = await get_kb_structure(force_refresh=True)
    for cat in data:
        print(cat.name)
        for topic in cat.topics:
            print('   ', topic)

asyncio.run(main())
