"""
code_gen.py - Generador de Código Python para el Analizador Léxico
Universidad del Valle de Guatemala - CC3071

Genera un archivo Python que implementa el analizador léxico
usando la tabla de transiciones del DFA construido.
"""

from regex_ast import EOF_CHAR, char_label


def generate_python_lexer(dfa, rule_actions, spec):
    """
    Genera código Python para el analizador léxico.

    Args:
        dfa:          objeto DFA minimizado
        rule_actions: lista de strings de acciones (una por regla)
        spec:         diccionario con la especificación YALex

    Returns:
        String con el código Python generado.
    """
    entrypoint = spec.get('entrypoint', 'gettoken')
    header = spec.get('header') or ''
    trailer = spec.get('trailer') or ''

    lines = []

    # ── Encabezado del archivo ──────────────────────────────────────────
    lines += [
        '"""',
        f'Analizador Léxico generado por YALex Generator',
        f'Universidad del Valle de Guatemala - CC3071',
        f'',
        f'Entrypoint: {entrypoint}',
        f'Reglas:     {len(rule_actions)}',
        f'Estados DFA: {dfa.num_states}',
        '"""',
        '',
    ]

    # ── Código del header ──────────────────────────────────────────────
    if header.strip():
        lines += [
            '# ─── Header (del archivo .yal) ───',
            header.strip(),
            '',
        ]

    # ── Tabla de transiciones DFA ──────────────────────────────────────
    lines += [
        '# ─── Tabla de transiciones del DFA ───',
        '# Formato: {(estado, código_ascii): estado_destino}',
        'DFA_TRANSITIONS = {',
    ]

    for (frm, sym), to in sorted(dfa.transitions.items()):
        c_repr = repr(chr(sym)) if sym != EOF_CHAR else "'EOF'"
        lines.append(f'    ({frm}, {sym}): {to},  # {c_repr}')

    lines += ['}', '']

    # ── Estados aceptores ──────────────────────────────────────────────
    lines += [
        '# ─── Estados aceptores: estado → índice de regla ───',
        'DFA_ACCEPTS = {',
    ]
    for state, rule_idx in sorted(dfa.accepts.items()):
        lines.append(f'    {state}: {rule_idx},')
    lines += ['}', '']

    # ── Constantes ────────────────────────────────────────────────────
    lines += [
        f'DFA_START   = {dfa.start}',
        f'NUM_RULES   = {len(rule_actions)}',
        f'EOF_CHAR    = {EOF_CHAR}',
        '',
    ]

    # ── Clase LexError ────────────────────────────────────────────────
    lines += [
        'class LexError(Exception):',
        '    """Error léxico: carácter no reconocido."""',
        '    def __init__(self, char, line, col):',
        '        self.char = char',
        '        self.line = line',
        '        self.col  = col',
        '        super().__init__(',
        '            f"Error léxico en línea {line}, columna {col}: '
        'carácter inesperado {char!r}"',
        '        )',
        '',
    ]

    # ── Clase Lexer ───────────────────────────────────────────────────
    lines += [
        'class Lexer:',
        '    """',
        f'    Analizador Léxico basado en DFA.',
        f'    Generado desde especificación YALex.',
        '    """',
        '',
        '    def __init__(self, input_text):',
        '        self.input  = input_text',
        '        self.pos    = 0',
        '        self.line   = 1',
        '        self.col    = 1',
        '        self.tokens = []',
        '',
        '    def _current_char_code(self):',
        '        """Retorna el código del carácter actual o EOF_CHAR."""',
        '        if self.pos >= len(self.input):',
        '            return EOF_CHAR',
        '        return ord(self.input[self.pos])',
        '',
        '    def _advance(self):',
        '        """Avanza un carácter, actualizando línea/columna."""',
        '        if self.pos < len(self.input):',
        '            if self.input[self.pos] == \'\\n\':',
        '                self.line += 1',
        '                self.col   = 1',
        '            else:',
        '                self.col += 1',
        '            self.pos += 1',
        '',
        '    def next_token(self):',
        '        """',
        '        Obtiene el siguiente token usando la estrategia de',
        '        concordancia más larga (longest match).',
        '',
        '        Retorna el resultado de la acción correspondiente,',
        '        o None si no hay más tokens.',
        '        """',
        '        while True:',
        '            if self.pos >= len(self.input):',
        '                return self._handle_eof()',
        '',
        '            state        = DFA_START',
        '            last_accept  = None   # (regla_idx, posición, línea, col)',
        '            start_pos    = self.pos',
        '            start_line   = self.line',
        '            start_col    = self.col',
        '            scan_pos     = self.pos',
        '            scan_line    = self.line',
        '            scan_col     = self.col',
        '',
        '            # ── Longest Match ──',
        '            while True:',
        '                if state in DFA_ACCEPTS:',
        '                    last_accept = (DFA_ACCEPTS[state], scan_pos,',
        '                                   scan_line, scan_col)',
        '',
        '                code = self._current_char_code()',
        '                if code == EOF_CHAR:',
        '                    break',
        '                next_state = DFA_TRANSITIONS.get((state, code))',
        '                if next_state is None:',
        '                    break',
        '                state = next_state',
        '                self._advance()',
        '',
        '            # Estado final también puede ser aceptor',
        '            if state in DFA_ACCEPTS:',
        '                last_accept = (DFA_ACCEPTS[state], self.pos,',
        '                               self.line, self.col)',
        '',
        '            if last_accept is None:',
        '                # Sin concordancia: error léxico',
        '                bad_char = self.input[self.pos] if self.pos < len(self.input) else "EOF"',
        '                raise LexError(bad_char, self.line, self.col)',
        '',
        '            rule_idx, end_pos, end_line, end_col = last_accept',
        '            lxm = self.input[start_pos:end_pos]',
        '',
        '            # Restaurar posición al final de la concordancia',
        '            self.pos  = end_pos',
        '            self.line = end_line',
        '            self.col  = end_col',
        '',
        '            # ── Ejecutar acción ──',
        '            result = self._execute_action(rule_idx, lxm, start_line, start_col)',
        '            if result is _CONTINUE:',
        '                continue  # skip (ej. espacios)',
        '            return result',
        '',
        '    def _handle_eof(self):',
        '        """Maneja el fin de archivo."""',
        '        # Verificar si existe la regla EOF',
        '        state = DFA_START',
        '        code  = EOF_CHAR',
        '        next_state = DFA_TRANSITIONS.get((state, code))',
        '        if next_state is not None and next_state in DFA_ACCEPTS:',
        '            rule_idx = DFA_ACCEPTS[next_state]',
        '            result = self._execute_action(rule_idx, "", self.line, self.col)',
        '            if result is not _CONTINUE:',
        '                return result',
        '        return None',
        '',
        '    def tokenize(self):',
        '        """Tokeniza el texto completo y retorna lista de tokens."""',
        '        tokens = []',
        '        while True:',
        '            try:',
        '                tok = self.next_token()',
        '            except LexError:',
        '                raise',
        '            except Exception:',
        '                # Acción EOF disparó excepción (ej. "Fin de buffer") → fin normal',
        '                break',
        '            if tok is None:',
        '                break',
        '            tokens.append(tok)',
        '        return tokens',
        '',
        '    def _execute_action(self, rule_idx, lxm, line, col):',
        '        """Despacha la acción según el índice de regla."""',
        '        lexbuf = _CONTINUE  # "return lexbuf" = continuar sin emitir token',
        _generate_dispatch(rule_actions),
        '        return None',
        '',
    ]

    # ── Sentinel CONTINUE ─────────────────────────────────────────────
    lines += [
        '_CONTINUE = object()  # Centinela: acción "return lexbuf"',
        '',
    ]

    # ── Función de entrypoint ─────────────────────────────────────────
    lines += [
        f'# ─── Función de entrada: {entrypoint} ───',
        f'def {entrypoint}(text):',
        f'    """Tokeniza el texto y retorna lista de tokens."""',
        f'    lexer = Lexer(text)',
        f'    return lexer.tokenize()',
        '',
    ]

    # ── Código del trailer ────────────────────────────────────────────
    if trailer.strip():
        lines += [
            '# ─── Trailer (del archivo .yal) ───',
            trailer.strip(),
            '',
        ]

    # ── Main de prueba ────────────────────────────────────────────────
    lines += [
        '',
        'if __name__ == "__main__":',
        '    import sys',
        '    if len(sys.argv) < 2:',
        '        print("Uso: python <lexer.py> <archivo_entrada>")',
        '        sys.exit(1)',
        '    with open(sys.argv[1], "r", encoding="utf-8") as f:',
        '        source = f.read()',
        '    try:',
        f'        tokens = {entrypoint}(source)',
        '        print(f"Se encontraron {len(tokens)} token(s):")',
        '        for i, tok in enumerate(tokens, 1):',
        '            print(f"  [{i:3d}] {tok!r}")',
        '    except LexError as e:',
        '        print(f"ERROR: {e}")',
        '        sys.exit(1)',
    ]

    return '\n'.join(lines)


def _generate_dispatch(rule_actions):
    """Genera el bloque if/elif para ejecutar acciones según el índice de regla."""
    if not rule_actions:
        return '        return None'

    dispatch = []
    for i, action in enumerate(rule_actions):
        kw = 'if' if i == 0 else 'elif'
        dispatch.append(f'        {kw} rule_idx == {i}:')
        # Adaptar la acción: reemplazar 'return lexbuf' por 'return _CONTINUE'
        adapted = _adapt_action(action)
        for ln in adapted.split('\n'):
            dispatch.append(f'            {ln}')

    return '\n'.join(dispatch)


def _adapt_action(action):
    """
    Adapta el código de acción del archivo .yal al Python generado.

    Reemplazos:
      - 'return lexbuf'  → 'return _CONTINUE'
      - 'int(lxm)'       → int(lxm)  (ya es Python)
      - 'raise(...)'     → raise ...
    """
    if not action.strip():
        return 'return None'

    # return lexbuf → return _CONTINUE (skip token)
    adapted = action.replace('return lexbuf', 'return _CONTINUE')

    # Auto-quoting: "return KW_LET" → "return 'KW_LET'"
    # Si la acción es solo "return NOMBRE_MAYUSCULAS" sin comillas, agregar comillas
    import re as _re
    def _quote_bare_token(m):
        val = m.group(1)
        # Si ya tiene comillas o paréntesis, no tocar
        if val.startswith(('"', "'", '(', '_')):
            return m.group(0)
        # Si es todo mayúsculas/guiones bajos (nombre de token), agregar comillas
        if _re.match(r'^[A-Z_][A-Z_0-9]*$', val):
            return f'return "{val}"'
        return m.group(0)
    adapted = _re.sub(r'\breturn\s+([^\s#(][^\n]*)', _quote_bare_token, adapted)

    # Si no hay 'return' explícito, agregar return None al final
    lines = [ln.strip() for ln in adapted.strip().split('\n') if ln.strip()]
    if not lines:
        return 'return None'

    has_return = any(ln.startswith('return') or ln.startswith('raise') for ln in lines)
    if not has_return:
        lines.append('return None')

    return '\n'.join(lines)