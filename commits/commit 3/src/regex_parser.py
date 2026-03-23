"""
Nicolás Concuá - 23197
Esteban Cárcamo - 23016
Kevin Villagrán - 23584
Carlos Alburez - 231311
Universidad del Valle de Guatemala - CC3071
Fases de Compilación: Generador de Analizadores Léxicos

Gramática (prioridad mayor a menor):
  regexp   ::= union
  union    ::= concat ('|' concat)*
  concat   ::= postfix postfix*
  postfix  ::= diff ('*' | '+' | '?')?
  diff     ::= primary ('#' primary)?
  primary  ::= CHAR_LIT | STRING_LIT | '[' charset ']' | '(' regexp ')' | '_' | 'eof' | IDENT
  charset  ::= '^'? charset_item+
  item     ::= CHAR_LIT ('-' CHAR_LIT)? | STRING_LIT
"""

from regex_ast import (
    EOF_CHAR, ALL_ASCII,
    EpsilonNode, LeafNode,
    ConcatNode, UnionNode, StarNode, PlusNode, OptionalNode,
)

ESCAPE_MAP = {
    'n': '\n', 't': '\t', 'r': '\r',
    '\\': '\\', "'": "'", '"': '"',
    '0': '\0', 'b': '\b', 'f': '\f',
}

def _skip_ws(s, i):
    while i < len(s) and s[i] in ' \t\n\r':
        i += 1
    return i


def _parse_escape(s, i):
    """Parsea secuencia de escape después de '\\'. Retorna (char, nueva_i)."""
    if i >= len(s):
        raise SyntaxError("Secuencia de escape incompleta")
    esc = s[i]
    return ESCAPE_MAP.get(esc, s[i]), i + 1


def _parse_char_literal(s, i):
    """Parsea 'c' o '\\e'. Retorna (código_int, nueva_i)."""
    if i >= len(s) or s[i] != "'":
        raise SyntaxError(f"Se esperaba ' en posición {i}: {s[i:i+5]!r}")
    i += 1
    if i >= len(s):
        raise SyntaxError("Literal de carácter no cerrado")
    if s[i] == '\\':
        char, i = _parse_escape(s, i + 1)
    else:
        char = s[i]
        i += 1
    if i >= len(s) or s[i] != "'":
        raise SyntaxError(f"Se esperaba ' de cierre en posición {i}")
    return ord(char), i + 1


def _parse_string_literal(s, i):
    """Parsea \"...\". Retorna (lista_de_códigos, nueva_i)."""
    if i >= len(s) or s[i] != '"':
        raise SyntaxError(f"Se esperaba \" en posición {i}")
    i += 1
    codes = []
    while i < len(s) and s[i] != '"':
        if s[i] == '\\':
            char, i = _parse_escape(s, i + 1)
        else:
            char = s[i]
            i += 1
        codes.append(ord(char))
    if i >= len(s):
        raise SyntaxError("Literal de cadena no cerrada")
    return codes, i + 1

class RegexParser:
    """Parser de Expresiones Regulares YALex."""

    def __init__(self, lets=None):
        self.lets = lets or {}
        self._cache = {}
        self.s = ''
        self.pos = 0

    def parse(self, s):
        """Parsea una cadena de regexp y retorna el AST raíz."""
        self.s = s.strip()
        self.pos = 0
        if not self.s:
            return EpsilonNode()
        node = self._union()
        self.pos = _skip_ws(self.s, self.pos)
        if self.pos < len(self.s):
            raise SyntaxError(
                f"Carácter inesperado en posición {self.pos}: "
                f"{self.s[self.pos]!r}  (contexto: {self.s[max(0,self.pos-5):self.pos+5]!r})"
            )
        return node

    # Union
    def _union(self):
        left = self._concat()
        while True:
            self.pos = _skip_ws(self.s, self.pos)
            if self.pos < len(self.s) and self.s[self.pos] == '|':
                self.pos += 1
                right = self._concat()
                left = UnionNode(left, right)
            else:
                break
        return left

    # Concatenacion
    def _concat(self):
        nodes = []
        while True:
            self.pos = _skip_ws(self.s, self.pos)
            if self.pos >= len(self.s):
                break
            c = self.s[self.pos]
            if c in ('|', ')'):
                break
            node = self._postfix()
            if node is None:
                break
            nodes.append(node)

        if not nodes:
            raise SyntaxError(
                f"Expresión vacía en posición {self.pos}: "
                f"{self.s[self.pos:self.pos+10]!r}"
            )
        result = nodes[0]
        for n in nodes[1:]:
            result = ConcatNode(result, n)
        return result
