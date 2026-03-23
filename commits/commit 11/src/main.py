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

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'hello.pico'
    if not target.endswith('.yal'):
        target = target.replace('.pico', '.yal')
    main(target)
