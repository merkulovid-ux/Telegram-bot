from pathlib import Path
path = Path('handlers/llm_commands.py')
data = path.read_bytes()
start = data.index(b'    yes_variants =')
end = data.index(b'    if user_input not in yes_variants')
print(data[start:end].decode('latin-1'))
