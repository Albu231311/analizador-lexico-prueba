"""
Nicolás Concuá - 23197
Esteban Cárcamo - 23016
Kevin Villagrán - 23584
Carlos Alburez - 231311
Universidad del Valle de Guatemala - CC3071
Fases de Compilación: Generador de Analizadores Léxicos 
"""

import os
import sys
from yalex_parser import parse_yalex_file
from regex_parser import RegexParser
from automata import DirectDFA
from regex_ast import ConcatNode, UnionNode, LeafNode
from code_gen import generate_lexer
from visualizer import visualize_dfa, visualize_expression_tree

def main(yal_path):
    print(f"Analizando {yal_path}...")
    base_name = os.path.basename(yal_path).split('.')[0]
    yal_ast = parse_yalex_file(yal_path)

    rules = yal_ast['rules']

    print("Construyendo AST combinado...")
    combined_ast = None
    
    for idx, rule in enumerate(rules, start=1):
        parser = RegexParser(yal_ast['lets'])
        rule_ast = parser.parse(rule[0])
        
        rule_concat = ConcatNode(rule_ast, LeafNode(rule_id=idx))
        
        if combined_ast is None:
            combined_ast = rule_concat
        else:
            combined_ast = UnionNode(combined_ast, rule_concat)
            
    print("Construyendo DFA Directo desde AST...")
    dfa = DirectDFA(combined_ast)
    
    print(f"DFA generado con {len(dfa.states)} estados.")
    
    print("Generando imagenes de arbol y DFA...")
    out_dir = 'output'
    os.makedirs(out_dir, exist_ok=True)

    ast_path = os.path.join(out_dir, f"{base_name}_expression_tree")
    visualize_expression_tree(combined_ast, ast_path)
    print(f"AST visualizado en {ast_path}.dot")

    dfa_path = os.path.join(out_dir, f"{base_name}_dfa")
    visualize_dfa(dfa, dfa_path)
    print(f"DFA visualizado en {dfa_path}.dot")
    
    print("Generando codigo fuente del lexer...")
    lex_path = os.path.join(out_dir, f"{base_name}_lexer.py")
    generate_lexer(dfa, rules, lex_path)
    print(f"Lexer generado en {lex_path}")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'hello.pico'
    if not target.endswith('.yal'):
        target = target.replace('.pico', '.yal')
    main(target)
