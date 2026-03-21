"""
Analizador Léxico generado por YALex Generator
Universidad del Valle de Guatemala - CC3071

Entrypoint: gettoken
Reglas:     4
Estados DFA: 5
"""

# ─── Tabla de transiciones del DFA ───
# Formato: {(estado, código_ascii): estado_destino}
DFA_TRANSITIONS = {
    (0, 32): 1,  # ' '
    (0, 48): 2,  # '0'
    (0, 49): 2,  # '1'
    (0, 50): 2,  # '2'
    (0, 51): 2,  # '3'
    (0, 52): 2,  # '4'
    (0, 53): 2,  # '5'
    (0, 54): 2,  # '6'
    (0, 55): 2,  # '7'
    (0, 56): 2,  # '8'
    (0, 57): 2,  # '9'
    (0, 98): 3,  # 'b'
    (0, 99): 3,  # 'c'
    (0, 100): 3,  # 'd'
    (0, 102): 3,  # 'f'
    (0, 103): 3,  # 'g'
    (0, 104): 3,  # 'h'
    (0, 106): 3,  # 'j'
    (0, 107): 3,  # 'k'
    (0, 108): 3,  # 'l'
    (0, 109): 3,  # 'm'
    (0, 110): 3,  # 'n'
    (0, 112): 3,  # 'p'
    (0, 113): 3,  # 'q'
    (0, 114): 3,  # 'r'
    (0, 115): 3,  # 's'
    (0, 116): 3,  # 't'
    (0, 118): 3,  # 'v'
    (0, 119): 3,  # 'w'
    (0, 120): 3,  # 'x'
    (0, 121): 3,  # 'y'
    (0, 122): 3,  # 'z'
    (0, 256): 4,  # 'EOF'
    (2, 48): 2,  # '0'
    (2, 49): 2,  # '1'
    (2, 50): 2,  # '2'
    (2, 51): 2,  # '3'
    (2, 52): 2,  # '4'
    (2, 53): 2,  # '5'
    (2, 54): 2,  # '6'
    (2, 55): 2,  # '7'
    (2, 56): 2,  # '8'
    (2, 57): 2,  # '9'
    (3, 98): 3,  # 'b'
    (3, 99): 3,  # 'c'
    (3, 100): 3,  # 'd'
    (3, 102): 3,  # 'f'
    (3, 103): 3,  # 'g'
    (3, 104): 3,  # 'h'
    (3, 106): 3,  # 'j'
    (3, 107): 3,  # 'k'
    (3, 108): 3,  # 'l'
    (3, 109): 3,  # 'm'
    (3, 110): 3,  # 'n'
    (3, 112): 3,  # 'p'
    (3, 113): 3,  # 'q'
    (3, 114): 3,  # 'r'
    (3, 115): 3,  # 's'
    (3, 116): 3,  # 't'
    (3, 118): 3,  # 'v'
    (3, 119): 3,  # 'w'
    (3, 120): 3,  # 'x'
    (3, 121): 3,  # 'y'
    (3, 122): 3,  # 'z'
}

# ─── Estados aceptores: estado → índice de regla ───
DFA_ACCEPTS = {
    1: 2,
    2: 1,
    3: 0,
    4: 3,
}

DFA_START   = 0
NUM_RULES   = 4
EOF_CHAR    = 256

class LexError(Exception):
    """Error léxico: carácter no reconocido."""
    def __init__(self, char, line, col):
        self.char = char
        self.line = line
        self.col  = col
        super().__init__(
            f"Error léxico en línea {line}, columna {col}: carácter inesperado {char!r}"
        )

class Lexer:
    """
    Analizador Léxico basado en DFA.
    Generado desde especificación YALex.
    """

    def __init__(self, input_text):
        self.input  = input_text
        self.pos    = 0
        self.line   = 1
        self.col    = 1
        self.tokens = []

    def _current_char_code(self):
        """Retorna el código del carácter actual o EOF_CHAR."""
        if self.pos >= len(self.input):
            return EOF_CHAR
        return ord(self.input[self.pos])

    def _advance(self):
        """Avanza un carácter, actualizando línea/columna."""
        if self.pos < len(self.input):
            if self.input[self.pos] == '\n':
                self.line += 1
                self.col   = 1
            else:
                self.col += 1
            self.pos += 1

    def next_token(self):
        """
        Obtiene el siguiente token usando la estrategia de
        concordancia más larga (longest match).

        Retorna el resultado de la acción correspondiente,
        o None si no hay más tokens.
        """
        while True:
            if self.pos >= len(self.input):
                return self._handle_eof()

            state        = DFA_START
            last_accept  = None   # (regla_idx, posición, línea, col)
            start_pos    = self.pos
            start_line   = self.line
            start_col    = self.col
            scan_pos     = self.pos
            scan_line    = self.line
            scan_col     = self.col

            # ── Longest Match ──
            while True:
                if state in DFA_ACCEPTS:
                    last_accept = (DFA_ACCEPTS[state], scan_pos,
                                   scan_line, scan_col)

                code = self._current_char_code()
                if code == EOF_CHAR:
                    break
                next_state = DFA_TRANSITIONS.get((state, code))
                if next_state is None:
                    break
                state = next_state
                self._advance()

            # Estado final también puede ser aceptor
            if state in DFA_ACCEPTS:
                last_accept = (DFA_ACCEPTS[state], self.pos,
                               self.line, self.col)

            if last_accept is None:
                # Sin concordancia: error léxico
                bad_char = self.input[self.pos] if self.pos < len(self.input) else "EOF"
                raise LexError(bad_char, self.line, self.col)

            rule_idx, end_pos, end_line, end_col = last_accept
            lxm = self.input[start_pos:end_pos]

            # Restaurar posición al final de la concordancia
            self.pos  = end_pos
            self.line = end_line
            self.col  = end_col

            # ── Ejecutar acción ──
            result = self._execute_action(rule_idx, lxm, start_line, start_col)
            if result is _CONTINUE:
                continue  # skip (ej. espacios)
            return result

    def _handle_eof(self):
        """Maneja el fin de archivo."""
        # Verificar si existe la regla EOF
        state = DFA_START
        code  = EOF_CHAR
        next_state = DFA_TRANSITIONS.get((state, code))
        if next_state is not None and next_state in DFA_ACCEPTS:
            rule_idx = DFA_ACCEPTS[next_state]
            result = self._execute_action(rule_idx, "", self.line, self.col)
            if result is not _CONTINUE:
                return result
        return None

    def tokenize(self):
        """Tokeniza el texto completo y retorna lista de tokens."""
        tokens = []
        while True:
            try:
                tok = self.next_token()
            except LexError:
                raise
            except Exception:
                # Acción EOF disparó excepción (ej. "Fin de buffer") → fin normal
                break
            if tok is None:
                break
            tokens.append(tok)
        return tokens

    def _execute_action(self, rule_idx, lxm, line, col):
        """Despacha la acción según el índice de regla."""
        lexbuf = _CONTINUE  # "return lexbuf" = continuar sin emitir token
        if rule_idx == 0:
            return ("CONSONANTS", lxm)
        elif rule_idx == 1:
            return ("NUMBER", lxm)
        elif rule_idx == 2:
            return _CONTINUE
        elif rule_idx == 3:
            raise Exception("EOF")
        return None

_CONTINUE = object()  # Centinela: acción "return lexbuf"

# ─── Función de entrada: gettoken ───
def gettoken(text):
    """Tokeniza el texto y retorna lista de tokens."""
    lexer = Lexer(text)
    return lexer.tokenize()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python <lexer.py> <archivo_entrada>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tokens = gettoken(source)
        print(f"Se encontraron {len(tokens)} token(s):")
        for i, tok in enumerate(tokens, 1):
            print(f"  [{i:3d}] {tok!r}")
    except LexError as e:
        print(f"ERROR: {e}")
        sys.exit(1)