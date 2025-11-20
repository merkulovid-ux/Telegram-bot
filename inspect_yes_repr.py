from pathlib import Path
text = Path('handlers/llm_commands.py').read_text('latin-1')
line = text.splitlines()[459]
print('line 460 repr:', repr(line))
