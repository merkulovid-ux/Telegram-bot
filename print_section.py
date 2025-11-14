from pathlib import Path
text = Path('handlers/llm_commands.py').read_text('cp1251')
start = text.index('async def process_digest')
print(text[start:start+400])
