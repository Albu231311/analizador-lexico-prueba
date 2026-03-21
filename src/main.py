#!/usr/bin/env python3
"""
main.py - Generador de Analizadores Léxicos YALex
Universidad del Valle de Guatemala - CC3071

Uso:
    python main.py <archivo.yal> [-o nombre_salida] [--verbose] [--no-minimize] [--show-nfa]

Salidas generadas:
    <nombre_salida>.py           → Analizador Léxico Python
    <nombre_salida>_tree.png     → Árbol de Expresión
    <nombre_salida>_dfa.png      → Visualización del DFA
    <nombre_salida>_nfa.png      → Visualización del NFA (opcional)
"""

import sys
import os
import argparse
import time

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yalex_parser import parse_yalex_file
from regex_parser  import RegexParser
from automata      import build_combined_nfa, nfa_to_dfa, minimize_dfa
from visualizer    import visualize_expression_tree, visualize_dfa, visualize_nfa
from code_gen      import generate_python_lexer


# ──────────────────────────── Colores ANSI ────────────────────────────

class C:
    HEADER  = '\033[95m'
    BLUE    = '\033[94m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    RED     = '\033[91m'
    BOLD    = '\033[1m'
    END     = '\033[0m'

def info(msg):  print(f"  {C.BLUE}→{C.END} {msg}")
def ok(msg):    print(f"  {C.GREEN}✓{C.END} {msg}")
def warn(msg):  print(f"  {C.YELLOW}⚠{C.END}  {msg}")
def err(msg):   print(f"  {C.RED}✗{C.END} {msg}", file=sys.stderr)


# ──────────────────────────── Main ────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='YALex - Generador de Analizadores Léxicos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py lexer.yal
  python main.py lexer.yal -o mi_lexer
  python main.py lexer.yal -o mi_lexer --verbose --show-nfa
        """
    )
    parser.add_argument('input',         help='Archivo .yal de entrada')
    parser.add_argument('-o', '--output',default=None, help='Nombre base del archivo de salida')
    parser.add_argument('--no-minimize', action='store_true', help='No minimizar el DFA')
    parser.add_argument('--show-nfa',    action='store_true', help='Generar visualización del NFA')
    parser.add_argument('--verbose',     action='store_true', help='Modo detallado')
    args = parser.parse_args()

    # Nombre de salida por defecto
    if args.output is None:
        base = os.path.splitext(os.path.basename(args.input))[0]
        args.output = base + '_lexer'

    out = args.output
    t0 = time.time()

    print(f"\n{C.BOLD}{C.HEADER}╔══════════════════════════════════════╗{C.END}")
    print(f"{C.BOLD}{C.HEADER}║   YALex - Generador de Analizadores  ║{C.END}")
    print(f"{C.BOLD}{C.HEADER}╚══════════════════════════════════════╝{C.END}\n")

    # ── Paso 1: Parsear archivo .yal ─────────────────────────────────
    print(f"{C.BOLD}[1/5] Parseando {args.input}{C.END}")
    try:
        spec = parse_yalex_file(args.input)
    except Exception as e:
        err(f"Error al parsear el archivo: {e}")
        sys.exit(1)

    ok(f"Entrypoint: '{spec['entrypoint']}'")
    ok(f"Definiciones 'let': {len(spec['lets'])} ({', '.join(spec['let_order'])})")
    ok(f"Reglas: {len(spec['rules'])}")
    if args.verbose:
        for i, (re_str, act) in enumerate(spec['rules']):
            info(f"  Regla {i+1}: {re_str[:60]}{'...' if len(re_str)>60 else ''}")

    # ── Paso 2: Parsear expresiones regulares ────────────────────────
    print(f"\n{C.BOLD}[2/5] Parseando expresiones regulares{C.END}")
    rparser = RegexParser(spec['lets'])
    trees = []
    for i, (re_str, action) in enumerate(spec['rules']):
        try:
            ast = rparser.parse(re_str)
            trees.append((ast, action, re_str))
            ok(f"Regla {i+1}: OK")
        except Exception as e:
            err(f"Error en regla {i+1} ('{re_str[:40]}'): {e}")
            sys.exit(1)

    # ── Paso 3: Visualizar árbol de expresión ───────────────────────
    print(f"\n{C.BOLD}[3/5] Generando árbol de expresión{C.END}")
    tree_path = out + '_expression_tree'
    try:
        visualize_expression_tree(trees, tree_path)
        ok(f"Árbol guardado en {tree_path}.png y {tree_path}.dot")
    except Exception as e:
        warn(f"No se pudo generar el árbol: {e}")

    # ── Paso 4: Construir NFA y DFA ──────────────────────────────────
    print(f"\n{C.BOLD}[4/5] Construyendo autómatas{C.END}")

    # NFA (Thompson's Construction)
    info("Construcción de Thompson (Regex AST → NFA)...")
    rule_asts = [(ast, i) for i, (ast, _, __) in enumerate(trees)]
    nfa = build_combined_nfa(rule_asts)
    ok(f"NFA construido: {nfa.num_states} estados, {sum(len(v) for v in nfa.transitions.values())} transiciones")

    if args.show_nfa:
        nfa_path = out + '_nfa'
        try:
            visualize_nfa(nfa, nfa_path)
            ok(f"NFA guardado en {nfa_path}.png")
        except Exception as e:
            warn(f"No se pudo visualizar el NFA: {e}")

    # DFA (Subset Construction)
    info("Construcción de subconjuntos (NFA → DFA)...")
    dfa, state_map = nfa_to_dfa(nfa)
    ok(f"DFA construido: {dfa.num_states} estados, {len(dfa.transitions)} transiciones")
    ok(f"Alfabeto: {len(dfa.alphabet)} símbolos")

    # Minimización
    if not args.no_minimize:
        info("Minimización de Hopcroft (DFA → DFA mínimo)...")
        dfa_min = minimize_dfa(dfa)
        reduction = dfa.num_states - dfa_min.num_states
        ok(f"DFA minimizado: {dfa_min.num_states} estados (reducción: {reduction})")
        dfa = dfa_min

    # Visualizar DFA
    dfa_path = out + '_dfa'
    try:
        visualize_dfa(dfa, dfa_path)
        ok(f"DFA guardado en {dfa_path}.png")
    except Exception as e:
        warn(f"No se pudo visualizar el DFA: {e}")

    # ── Paso 5: Generar código Python ────────────────────────────────
    print(f"\n{C.BOLD}[5/5] Generando analizador léxico Python{C.END}")
    rule_actions = [action for _, action, __ in trees]

    try:
        code = generate_python_lexer(dfa, rule_actions, spec)
    except Exception as e:
        err(f"Error al generar código: {e}")
        sys.exit(1)

    output_file = out + '.py'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    ok(f"Analizador léxico generado: {output_file}")

    # ── Resumen ──────────────────────────────────────────────────────
    elapsed = time.time() - t0
    print(f"\n{C.BOLD}{C.GREEN}╔══════════════════════════════════════╗{C.END}")
    print(f"{C.BOLD}{C.GREEN}║   ¡Compilación exitosa! ({elapsed:.2f}s)      ║{C.END}")
    print(f"{C.BOLD}{C.GREEN}╚══════════════════════════════════════╝{C.END}\n")
    print(f"Archivos generados:")
    print(f"  {C.BOLD}{output_file}{C.END}           → Analizador Léxico")
    print(f"  {tree_path}.png  → Árbol de Expresión")
    print(f"  {dfa_path}.png   → Diagrama DFA\n")
    print(f"Para usar el lexer generado:")
    print(f"  {C.BOLD}python {output_file} <archivo_entrada.txt>{C.END}\n")


if __name__ == '__main__':
    main()
