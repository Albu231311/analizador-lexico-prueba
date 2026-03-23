"""
Nicolás Concuá - 23197
Esteban Cárcamo - 23016
Kevin Villagrán - 23584
Carlos Alburez - 231311
Universidad del Valle de Guatemala - CC3071
Fases de Compilación: Generador de Analizadores Léxicos 
"""
import os

def generate_lexer(dfa, rules, out_path):
    states = len(dfa.states)
    transitions = dfa.transitions
    accepting = dfa.accepts

    trans_repr = "{\n"
    for st, sym_map in transitions.items():
        trans_repr += f"        {st}: {sym_map},\n"
    trans_repr += "    }"
    
    actions_list = [rule[1] for rule in rules]
    actions_repr = "{\n"
    for idx, action in enumerate(actions_list, start=1):
        actions_repr += f"        {idx}: {repr(action)},\n"
    actions_repr += "    }"

    code = f"""# Lexer generado automaticamente
import sys

TRANSITIONS = {trans_repr}
ACCEPTING_STATES = {accepting}
ACTIONS = {actions_repr}

class LexerException(Exception):
    pass

def lex_string(input_string):
    tokens = []
    pos = 0
    length = len(input_string)
    
    while pos < length:
        current_state = 0
        last_accept_state = None
        last_accept_pos = -1
        last_accept_rule = None
        
        current_pos = pos
        while current_pos < length:
            char_code = ord(input_string[current_pos])
            
            if current_state in TRANSITIONS and char_code in TRANSITIONS[current_state]:
                current_state = TRANSITIONS[current_state][char_code]
            else:
                break
                
            current_pos += 1
            
            if current_state in ACCEPTING_STATES:
                rule_id = ACCEPTING_STATES[current_state]
                if current_pos > last_accept_pos or (current_pos == last_accept_pos and rule_id < last_accept_rule):
                    last_accept_state = current_state
                    last_accept_pos = current_pos
                    last_accept_rule = rule_id
                    
        if last_accept_state is not None:
            lexeme = input_string[pos:last_accept_pos]
            action = ACTIONS.get(last_accept_rule, '')
            tokens.append((last_accept_rule, lexeme, action))
            pos = last_accept_pos
        else:
            raise LexerException(f"Error lexico en posicion {{pos}}: {{repr(input_string[pos:pos+5])}}...")
            
    return tokens

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python lexer.py <archivo.txt>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        content = f.read()
        
    try:
        tokens = lex_string(content)
        
        final_tokens = []
        for t in tokens:
            rule_id, lexeme, action_str = t
            action_str = action_str.strip()
            if action_str.startswith("return"):
                val = action_str[6:].strip()
                if val == "lexbuf":
                    continue
                
                if "lxm" in val:
                    val = val.replace("lxm", repr(lexeme))
                
                if val.startswith("(") and val.endswith(")"):
                    val = val
                else:
                    val = repr(val)
                    
                final_tokens.append(val)
            elif action_str:
                final_tokens.append(repr(action_str))

        print(f"Se encontraron {{len(final_tokens)}} token(s):")
        for i, val in enumerate(final_tokens, 1):
            try:
                parsed_val = eval(val)
                if isinstance(parsed_val, tuple):
                    print(f"  [ {{i:>2}} ] {{parsed_val}}")
                else:
                    print(f"  [ {{i:>2}} ] {{repr(parsed_val)}}")
            except:
                print(f"  [ {{i:>2}} ] {{val}}")

    except Exception as e:
        print(e)
"""

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(code)


