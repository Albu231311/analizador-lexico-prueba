with open('src/visualizer.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("for frm, sym_map in dfa.transitions.items():\
        for sym, to in sym_map.items():", "for frm, sym_map in dfa.transitions.items():\n        for sym, to in sym_map.items():")

with open('src/visualizer.py', 'w', encoding='utf-8') as f:
    f.write(text)
