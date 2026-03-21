"""
regex_parser.py - Parser de Expresiones Regulares para YALex
Universidad del Valle de Guatemala - CC3071

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
    EpsilonNode, LiteralNode, CharSetNode, AnyCharNode,
    ConcatNode, UnionNode, StarNode, PlusNode, OptionalNode,
)

ESCAPE_MAP = {
    'n': '\n', 't': '\t', 'r': '\r',
    '\\': '\\', "'": "'", '"': '"',
    '0': '\0', 'b': '\b', 'f': '\f',
}


# ──────────────────────── Utilidades de lexing ────────────────────────

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


# ──────────────────────── Parser de Regexp ────────────────────────

class RegexParser:
    """
    Parser de Expresiones Regulares YALex.

    Uso:
        p = RegexParser(lets_dict)
        ast = p.parse("['a'-'z']+")
    """

    def __init__(self, lets=None):
        self.lets = lets or {}
        self._cache = {}   # cache de let ya parseados
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

    # ── Nivel 1: Unión ──

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

    # ── Nivel 2: Concatenación ──

    def _concat(self):
        nodes = []
        while True:
            self.pos = _skip_ws(self.s, self.pos)
            if self.pos >= len(self.s):
                break
            c = self.s[self.pos]
            # Tokens que terminan una concatenación
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

    # ── Nivel 3: Postfix (*, +, ?) ──

    def _postfix(self):
        node = self._diff()
        if node is None:
            return None
        self.pos = _skip_ws(self.s, self.pos)
        if self.pos < len(self.s):
            c = self.s[self.pos]
            if c == '*':
                self.pos += 1
                return StarNode(node)
            elif c == '+':
                self.pos += 1
                return PlusNode(node)
            elif c == '?':
                self.pos += 1
                return OptionalNode(node)
        return node

    # ── Nivel 4: Diferencia (#) ──

    def _diff(self):
        left = self._primary()
        if left is None:
            return None
        self.pos = _skip_ws(self.s, self.pos)
        if self.pos < len(self.s) and self.s[self.pos] == '#':
            self.pos += 1
            right = self._primary()
            if right is None:
                raise SyntaxError("Se esperaba expresión después de '#'")
            left_codes = self._extract_codes(left)
            right_codes = self._extract_codes(right)
            diff = left_codes - right_codes
            return CharSetNode(diff) if len(diff) != 1 else LiteralNode(next(iter(diff)))
        return left

    def _extract_codes(self, node):
        """Extrae el conjunto de códigos de un nodo tipo charset (recursivo)."""
        from regex_ast import ConcatNode, UnionNode
        if isinstance(node, CharSetNode):
            return set(node.codes)
        elif isinstance(node, LiteralNode):
            return {node.code}
        elif isinstance(node, AnyCharNode):
            return set(ALL_ASCII)
        elif isinstance(node, UnionNode):
            # ['a'-'z'] # "aeiou" puede generar un UnionNode de literales
            return self._extract_codes(node.left) | self._extract_codes(node.right)
        elif isinstance(node, ConcatNode):
            # Una cadena "aeiou" se parsea como ConcatNode de literales
            return self._extract_codes(node.left) | self._extract_codes(node.right)
        else:
            raise SyntaxError(
                f"El operador '#' solo aplica a conjuntos de caracteres, "
                f"no a {type(node).__name__}"
            )

    # ── Nivel 5: Primario ──

    def _primary(self):
        self.pos = _skip_ws(self.s, self.pos)
        if self.pos >= len(self.s):
            return None

        c = self.s[self.pos]

        # Literal de carácter 'c'
        if c == "'":
            code, self.pos = _parse_char_literal(self.s, self.pos)
            return LiteralNode(code)

        # Literal de cadena "abc"
        elif c == '"':
            codes, self.pos = _parse_string_literal(self.s, self.pos)
            if not codes:
                return EpsilonNode()
            node = LiteralNode(codes[0])
            for code in codes[1:]:
                node = ConcatNode(node, LiteralNode(code))
            return node

        # Conjunto de caracteres [...]
        elif c == '[':
            return self._charset()

        # Agrupación (...)
        elif c == '(':
            self.pos += 1
            node = self._union()
            self.pos = _skip_ws(self.s, self.pos)
            if self.pos >= len(self.s) or self.s[self.pos] != ')':
                raise SyntaxError(f"Se esperaba ')' en posición {self.pos}")
            self.pos += 1
            return node

        # Identificador o palabra clave
        elif c.isalpha() or c == '_':
            start = self.pos
            while self.pos < len(self.s) and (self.s[self.pos].isalnum() or self.s[self.pos] == '_'):
                self.pos += 1
            word = self.s[start:self.pos]

            if word == 'eof':
                return LiteralNode(EOF_CHAR)
            elif word == '_':
                return AnyCharNode()
            else:
                return self._resolve(word)

        else:
            return None   # No es un primario válido (terminador)

    def _resolve(self, ident):
        """Resuelve una referencia a una definición 'let'."""
        if ident in self._cache:
            return self._cache[ident]
        if ident not in self.lets:
            raise SyntaxError(f"Identificador no definido: '{ident}'")
        sub = RegexParser(self.lets)
        sub._cache = self._cache
        result = sub.parse(self.lets[ident])
        self._cache[ident] = result
        return result

    # ── Conjunto de caracteres ──

    def _charset(self):
        """Parsea [charset] o [^charset]."""
        assert self.s[self.pos] == '['
        self.pos += 1

        negated = False
        if self.pos < len(self.s) and self.s[self.pos] == '^':
            negated = True
            self.pos += 1

        codes = set()

        while self.pos < len(self.s):
            self.pos = _skip_ws(self.s, self.pos)
            if self.pos >= len(self.s) or self.s[self.pos] == ']':
                break

            c = self.s[self.pos]

            if c == "'":
                # Puede ser 'c' o 'c1'-'c2'
                code, self.pos = _parse_char_literal(self.s, self.pos)
                self.pos = _skip_ws(self.s, self.pos)
                if self.pos < len(self.s) and self.s[self.pos] == '-':
                    self.pos += 1
                    self.pos = _skip_ws(self.s, self.pos)
                    code2, self.pos = _parse_char_literal(self.s, self.pos)
                    if code2 < code:
                        raise SyntaxError(
                            f"Rango inválido: {chr(code)!r}-{chr(code2)!r}"
                        )
                    codes.update(range(code, code2 + 1))
                else:
                    codes.add(code)

            elif c == '"':
                char_codes, self.pos = _parse_string_literal(self.s, self.pos)
                codes.update(char_codes)

            else:
                raise SyntaxError(
                    f"Elemento de conjunto inválido en posición {self.pos}: {c!r}"
                )

        if self.pos >= len(self.s) or self.s[self.pos] != ']':
            raise SyntaxError("Conjunto de caracteres '[' no cerrado")
        self.pos += 1  # saltar ']'

        if negated:
            codes = ALL_ASCII - codes

        if not codes:
            return EpsilonNode()
        if len(codes) == 1:
            return LiteralNode(next(iter(codes)))
        return CharSetNode(codes)