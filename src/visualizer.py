"""
visualizer.py - Visualización de Árboles de Expresión y Autómatas
Universidad del Valle de Guatemala - CC3071

Genera imágenes PNG y archivos DOT usando Graphviz.
"""

import os
from regex_ast import RegexNode, char_label, EOF_CHAR


# ═══════════════════════════════════════════════════════════════
#                 Árbol de Expresión
# ═══════════════════════════════════════════════════════════════

def _node_color(node):
    """Asigna color por tipo de nodo."""
    from regex_ast import (LiteralNode, CharSetNode, AnyCharNode, EpsilonNode,
                           ConcatNode, UnionNode, StarNode, PlusNode, OptionalNode)
    if isinstance(node, (LiteralNode, CharSetNode, AnyCharNode, EpsilonNode)):
        return '#A8D8A8'   # verde claro - hojas
    elif isinstance(node, UnionNode):
        return '#F4A460'   # naranja - unión
    elif isinstance(node, ConcatNode):
        return '#87CEEB'   # azul - concatenación
    elif isinstance(node, (StarNode, PlusNode, OptionalNode)):
        return '#DDA0DD'   # violeta - cuantificadores
    return '#FFFFFF'


def _dot_escape(s):
    """Escapa una cadena para usarla como etiqueta DOT."""
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    return s


def _tree_to_dot(node, dot_lines, counter):
    """Recorre el árbol y genera líneas DOT."""
    if node is None:
        return None
    nid = f"n{counter[0]}"
    counter[0] += 1
    label = _dot_escape(node.label())
    color = _node_color(node)
    dot_lines.append(
        f'  {nid} [label="{label}" style=filled fillcolor="{color}" '
        f'shape=circle fontname="Courier" fontsize=11];'
    )
    for child in node.children():
        child_id = _tree_to_dot(child, dot_lines, counter)
        if child_id:
            dot_lines.append(f'  {nid} -> {child_id};')
    return nid


def visualize_expression_tree(rules_info, output_path):
    """
    Genera el árbol de expresión combinado para todas las reglas.

    Args:
        rules_info: lista de (ast, action, regexp_str)
        output_path: ruta base de salida (sin extensión)
    """
    try:
        import graphviz
    except ImportError:
        print("  [!] graphviz no instalado. Generando solo DOT.")
        graphviz = None

    dot_lines = [
        'digraph ExpressionTree {',
        '  graph [rankdir=TB bgcolor="#FAFAFA" label="Árbol de Expresión Combinado" '
        '         fontsize=14 fontname="Helvetica"];',
        '  node  [shape=circle fontname="Courier" fontsize=10];',
        '  edge  [arrowsize=0.7];',
    ]

    counter = [0]
    rule_roots = []

    for i, (ast, action, regexp_str) in enumerate(rules_info):
        # Nodo raíz de la regla
        rid = f"rule{i}"
        short_re = regexp_str[:40] + ('...' if len(regexp_str) > 40 else '')
        short_re = _dot_escape(short_re)
        dot_lines.append(
            f'  {rid} [label="Regla {i+1}\\n{short_re}" shape=box '
            f'style=filled fillcolor="#FFD700" fontname="Helvetica" fontsize=9];'
        )

        root_id = _tree_to_dot(ast, dot_lines, counter)
        if root_id:
            dot_lines.append(f'  {rid} -> {root_id} [style=dashed color=gray];')
        rule_roots.append(rid)

    dot_lines.append('}')
    dot_source = '\n'.join(dot_lines)

    # Guardar .dot
    dot_file = output_path + '.dot'
    with open(dot_file, 'w', encoding='utf-8') as f:
        f.write(dot_source)

    # Renderizar con graphviz
    if graphviz is not None:
        try:
            src = graphviz.Source(dot_source)
            src.render(output_path, format='png', cleanup=True)
        except Exception as e:
            print(f"  [!] Error al renderizar árbol: {e}")
            # Intentar con subprocess
            _render_dot(dot_file, output_path + '.png')
    else:
        _render_dot(dot_file, output_path + '.png')


# ═══════════════════════════════════════════════════════════════
#                     DFA
# ═══════════════════════════════════════════════════════════════

def visualize_dfa(dfa, output_path, rule_labels=None):
    """
    Genera la visualización del DFA.

    Args:
        dfa: objeto DFA
        output_path: ruta base de salida
        rule_labels: lista de strings cortos para identificar reglas
    """
    dot_lines = [
        'digraph DFA {',
        '  graph [rankdir=LR bgcolor="#FAFAFA" label="DFA del Analizador Léxico" '
        '         fontsize=14 fontname="Helvetica"];',
        '  node  [fontname="Courier" fontsize=10];',
        '  edge  [fontname="Courier" fontsize=9 arrowsize=0.7];',
        '  __start__ [shape=none label=""];',
        f'  __start__ -> {dfa.start};',
    ]

    all_states = set(range(dfa.num_states))

    for s in sorted(all_states):
        if s in dfa.accepts:
            rule_idx = dfa.accepts[s]
            lbl = f"R{rule_idx}" if not rule_labels else f"R{rule_idx}"
            dot_lines.append(
                f'  {s} [shape=doublecircle style=filled '
                f'fillcolor="#90EE90" label="q{s}\\n({lbl})"];'
            )
        elif s == dfa.start:
            dot_lines.append(
                f'  {s} [shape=circle style=filled fillcolor="#87CEEB" label="q{s}\\n(start)"];'
            )
        else:
            dot_lines.append(f'  {s} [shape=circle label="q{s}"];')

    # Agrupar transiciones por (origen, destino) para mostrar rangos
    edge_labels = {}   # (from, to) → list of char codes
    for (frm, sym), to in dfa.transitions.items():
        edge_labels.setdefault((frm, to), []).append(sym)

    for (frm, to), syms in sorted(edge_labels.items()):
        label = _compact_label(sorted(syms))
        dot_lines.append(f'  {frm} -> {to} [label="{label}"];')
    dot_lines.append('}')
    dot_source = '\n'.join(dot_lines)

    dot_file = output_path + '.dot'
    with open(dot_file, 'w', encoding='utf-8') as f:
        f.write(dot_source)

    _render_dot(dot_file, output_path + '.png')


def _compact_label(codes):
    """Convierte lista de códigos en etiqueta compacta (rangos)."""
    if not codes:
        return ''
    if len(codes) > 12:
        return f'[{len(codes)} chars]'

    ranges = []
    i = 0
    while i < len(codes):
        j = i
        while j + 1 < len(codes) and codes[j+1] == codes[j] + 1:
            j += 1
        if j - i >= 2:
            ranges.append(f"{char_label(codes[i])}-{char_label(codes[j])}")
        else:
            for k in range(i, j + 1):
                ranges.append(char_label(codes[k]))
        i = j + 1

    label = ','.join(ranges)
    return _dot_escape(label)[:50]


def visualize_nfa(nfa, output_path):
    """Genera la visualización del NFA."""
    from regex_ast import char_label

    dot_lines = [
        'digraph NFA {',
        '  graph [rankdir=LR bgcolor="#FAFAFA" label="NFA (Thompson)" '
        '         fontsize=14 fontname="Helvetica"];',
        '  node  [shape=circle fontname="Courier" fontsize=9];',
        '  edge  [fontname="Courier" fontsize=8 arrowsize=0.6];',
        '  __s__ [shape=none label=""];',
        f'  __s__ -> {nfa.start};',
    ]

    for s in range(nfa.num_states):
        if s in nfa.accepts:
            dot_lines.append(f'  {s} [shape=doublecircle style=filled fillcolor="#90EE90"];')
        elif s == nfa.start:
            dot_lines.append(f'  {s} [style=filled fillcolor="#87CEEB"];')

    edge_labels = {}
    for frm, trans_list in nfa.transitions.items():
        for sym, to in trans_list:
            lbl = 'ε' if sym is None else char_label(sym)
            edge_labels.setdefault((frm, to), set()).add(lbl)

    for (frm, to), lbls in sorted(edge_labels.items()):
        lbl = ','.join(sorted(lbls))[:30]
        lbl = lbl.replace('"', '\\"')
        dot_lines.append(f'  {frm} -> {to} [label="{lbl}"];')

    dot_lines.append('}')
    dot_source = '\n'.join(dot_lines)

    dot_file = output_path + '.dot'
    with open(dot_file, 'w', encoding='utf-8') as f:
        f.write(dot_source)

    _render_dot(dot_file, output_path + '.png')


def _render_dot(dot_file, png_file):
    """Renderiza un archivo .dot a PNG usando el binario dot."""
    import subprocess
    try:
        result = subprocess.run(
            ['dot', '-Tpng', dot_file, '-o', png_file],
            capture_output=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  [!] dot retornó código {result.returncode}: {result.stderr.decode()}")
        else:
            print(f"  [✓] Imagen generada: {png_file}")
    except FileNotFoundError:
        print("  [!] 'dot' no encontrado. Instale graphviz: sudo apt-get install graphviz")
    except Exception as e:
        print(f"  [!] Error al renderizar: {e}")
