"""
regex_ast.py - Nodos del Árbol Sintáctico para Expresiones Regulares
Universidad del Valle de Guatemala - CC3071
"""

EOF_CHAR = 256   # Símbolo especial para fin de archivo
ALL_ASCII = set(range(128))  # Todos los caracteres ASCII


def char_label(code):
    """Convierte un código entero a una etiqueta legible."""
    if code == EOF_CHAR:
        return 'EOF'
    c = chr(code)
    special = {'\n': '\\n', '\t': '\\t', '\r': '\\r', ' ': 'SP', '\\': '\\\\'}
    return special.get(c, c)


# ─────────────────────────── Nodos Base ───────────────────────────

class RegexNode:
    """Clase base para todos los nodos del AST."""
    _id_counter = 0

    def __init__(self):
        RegexNode._id_counter += 1
        self._node_id = RegexNode._id_counter

    def label(self):
        raise NotImplementedError

    def children(self):
        return []


class EpsilonNode(RegexNode):
    """Cadena vacía ε."""
    def label(self): return 'ε'


class LiteralNode(RegexNode):
    """Símbolo individual: 'c' o secuencia de escape."""
    def __init__(self, code):
        super().__init__()
        self.code = code   # entero: ord(c) o EOF_CHAR

    def label(self):
        return char_label(self.code)


class CharSetNode(RegexNode):
    """Conjunto de caracteres: ['a'-'z'] o [^...] etc."""
    def __init__(self, codes):
        super().__init__()
        self.codes = frozenset(codes)

    def label(self):
        n = len(self.codes)
        if n == 0:
            return '∅'
        if n <= 6:
            return '[' + ''.join(char_label(c) for c in sorted(self.codes)) + ']'
        return f'[{n} chars]'


class AnyCharNode(RegexNode):
    """Comodín _ (cualquier símbolo)."""
    def label(self): return '_'


class ConcatNode(RegexNode):
    """Concatenación: r1 r2."""
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def label(self): return '·'
    def children(self): return [self.left, self.right]


class UnionNode(RegexNode):
    """Alternación: r1 | r2."""
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def label(self): return '|'
    def children(self): return [self.left, self.right]


class StarNode(RegexNode):
    """Cerradura de Kleene: r*."""
    def __init__(self, child):
        super().__init__()
        self.child = child

    def label(self): return '*'
    def children(self): return [self.child]


class PlusNode(RegexNode):
    """Cerradura Positiva: r+."""
    def __init__(self, child):
        super().__init__()
        self.child = child

    def label(self): return '+'
    def children(self): return [self.child]


class OptionalNode(RegexNode):
    """Opcional: r?."""
    def __init__(self, child):
        super().__init__()
        self.child = child

    def label(self): return '?'
    def children(self): return [self.child]
