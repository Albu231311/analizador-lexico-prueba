"""
Nicolás Concuá - 23197
Esteban Cárcamo - 23016
Kevin Villagrán - 23584
Carlos Alburez - 231311
Universidad del Valle de Guatemala - CC3071
Fases de Compilación: Generador de Analizadores Léxicos 
"""

EOF_CHAR = 256
ALL_ASCII = set(range(128))

def char_label(code):
    if code == EOF_CHAR:
        return 'EOF'
    c = chr(code)
    special = {'\n': '\\n', '\t': '\\t', '\r': '\\r', ' ': 'SP', '\\': '\\\\'}
    return special.get(c, c)

class RegexNode:
    _id_counter = 0

    def __init__(self):
        RegexNode._id_counter += 1
        self._node_id = RegexNode._id_counter
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()
        self.pos = None
    
    def calculate_properties(self, followpos, pos_mapping):
        pass

    def label(self):
        raise NotImplementedError

    def children(self):
        return []

class EpsilonNode(RegexNode):
    def calculate_properties(self, followpos, pos_mapping):
        self.nullable = True
        self.firstpos = set()
        self.lastpos = set()
    def label(self): return 'e'

class LeafNode(RegexNode):
    def __init__(self, code=None, codes=None, rule_id=None):
        super().__init__()
        self.code = code
        self.codes = frozenset(codes) if codes else None
        self.rule_id = rule_id

    def calculate_properties(self, followpos, pos_mapping):
        self.nullable = False
        self.firstpos = {self.pos}
        self.lastpos = {self.pos}
        pos_mapping[self.pos] = self

    def label(self):
        if self.rule_id is not None: return f'#{self.rule_id}'
        if self.code is not None: return char_label(self.code)
        if self.codes is not None: return f'[{len(self.codes)} chars]'
        return '_'

class ConcatNode(RegexNode):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def calculate_properties(self, followpos, pos_mapping):
        self.left.calculate_properties(followpos, pos_mapping)
        self.right.calculate_properties(followpos, pos_mapping)
        self.nullable = self.left.nullable and self.right.nullable
        self.firstpos = self.left.firstpos | (self.right.firstpos if self.left.nullable else set())
        self.lastpos = self.right.lastpos | (self.left.lastpos if self.right.nullable else set())
        for i in self.left.lastpos:
            followpos.setdefault(i, set()).update(self.right.firstpos)

    def label(self): return '.'
    def children(self): return [self.left, self.right]

class UnionNode(RegexNode):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def calculate_properties(self, followpos, pos_mapping):
        self.left.calculate_properties(followpos, pos_mapping)
        self.right.calculate_properties(followpos, pos_mapping)
        self.nullable = self.left.nullable or self.right.nullable
        self.firstpos = self.left.firstpos | self.right.firstpos
        self.lastpos = self.left.lastpos | self.right.lastpos

    def label(self): return '|'
    def children(self): return [self.left, self.right]

class StarNode(RegexNode):
    def __init__(self, child):
        super().__init__()
        self.child = child

    def calculate_properties(self, followpos, pos_mapping):
        self.child.calculate_properties(followpos, pos_mapping)
        self.nullable = True
        self.firstpos = self.child.firstpos
        self.lastpos = self.child.lastpos
        for i in self.lastpos:
            followpos.setdefault(i, set()).update(self.firstpos)

    def label(self): return '*'
    def children(self): return [self.child]

class PlusNode(RegexNode):
    def __init__(self, child):
        super().__init__()
        self.child = child

    def calculate_properties(self, followpos, pos_mapping):
        self.child.calculate_properties(followpos, pos_mapping)
        self.nullable = self.child.nullable
        self.firstpos = self.child.firstpos
        self.lastpos = self.child.lastpos
        for i in self.lastpos:
            followpos.setdefault(i, set()).update(self.firstpos)

    def label(self): return '+'
    def children(self): return [self.child]

class OptionalNode(RegexNode):
    def __init__(self, child):
        super().__init__()
        self.child = child

    def calculate_properties(self, followpos, pos_mapping):
        self.child.calculate_properties(followpos, pos_mapping)
        self.nullable = True
        self.firstpos = self.child.firstpos
        self.lastpos = self.child.lastpos

    def label(self): return '?'
    def children(self): return [self.child]

