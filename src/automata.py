"""
automata.py - Construcción de NFA y DFA
Universidad del Valle de Guatemala - CC3071

Algoritmos implementados:
  1. Construcción de Thompson (regex AST → NFA)
  2. Construcción de Subconjuntos (NFA → DFA)
  3. Minimización de Hopcroft (DFA → DFA mínimo)
"""

from collections import defaultdict
from regex_ast import (
    EOF_CHAR, ALL_ASCII,
    EpsilonNode, LiteralNode, CharSetNode, AnyCharNode,
    ConcatNode, UnionNode, StarNode, PlusNode, OptionalNode,
)

EPSILON = None   # Símbolo de transición epsilon

# ═══════════════════════════════════════════════════════════════
#                        NFA
# ═══════════════════════════════════════════════════════════════

class NFA:
    """Autómata Finito No Determinista."""

    def __init__(self):
        self._next_id = 0
        self.start = None
        self.accepts = {}           # estado → índice de regla (int)
        self.transitions = defaultdict(list)   # estado → [(símbolo, destino)]

    def new_state(self):
        s = self._next_id
        self._next_id += 1
        return s

    @property
    def num_states(self):
        return self._next_id

    def add_trans(self, frm, sym, to):
        self.transitions[frm].append((sym, to))

    def add_eps(self, frm, to):
        self.transitions[frm].append((EPSILON, to))


# ──────────────────────── Thompson's Construction ────────────────────────

def _build_fragment(node, nfa):
    """
    Construye un fragmento NFA para el nodo AST dado.
    Retorna (estado_inicio, estado_fin).
    """

    if isinstance(node, EpsilonNode):
        s, e = nfa.new_state(), nfa.new_state()
        nfa.add_eps(s, e)
        return s, e

    elif isinstance(node, LiteralNode):
        s, e = nfa.new_state(), nfa.new_state()
        nfa.add_trans(s, node.code, e)
        return s, e

    elif isinstance(node, CharSetNode):
        s, e = nfa.new_state(), nfa.new_state()
        for code in node.codes:
            nfa.add_trans(s, code, e)
        return s, e

    elif isinstance(node, AnyCharNode):
        s, e = nfa.new_state(), nfa.new_state()
        for code in range(128):   # ASCII completo
            nfa.add_trans(s, code, e)
        return s, e

    elif isinstance(node, ConcatNode):
        s1, e1 = _build_fragment(node.left, nfa)
        s2, e2 = _build_fragment(node.right, nfa)
        nfa.add_eps(e1, s2)
        return s1, e2

    elif isinstance(node, UnionNode):
        s, e = nfa.new_state(), nfa.new_state()
        s1, e1 = _build_fragment(node.left, nfa)
        s2, e2 = _build_fragment(node.right, nfa)
        nfa.add_eps(s, s1);  nfa.add_eps(s, s2)
        nfa.add_eps(e1, e);  nfa.add_eps(e2, e)
        return s, e

    elif isinstance(node, StarNode):
        s, e = nfa.new_state(), nfa.new_state()
        s1, e1 = _build_fragment(node.child, nfa)
        nfa.add_eps(s, s1)    # entrar al cuerpo
        nfa.add_eps(s, e)     # saltar (0 veces)
        nfa.add_eps(e1, s1)   # repetir
        nfa.add_eps(e1, e)    # salir
        return s, e

    elif isinstance(node, PlusNode):
        # r+ = r seguido de r*
        s1, e1 = _build_fragment(node.child, nfa)
        # Construir r* manualmente con los mismos fragmentos del cuerpo re-entrantes
        new_e = nfa.new_state()
        nfa.add_eps(e1, s1)    # volver para más repeticiones
        nfa.add_eps(e1, new_e) # salir
        return s1, new_e

    elif isinstance(node, OptionalNode):
        s, e = nfa.new_state(), nfa.new_state()
        s1, e1 = _build_fragment(node.child, nfa)
        nfa.add_eps(s, s1)   # entrar
        nfa.add_eps(s, e)    # saltar (0 veces)
        nfa.add_eps(e1, e)   # salir
        return s, e

    else:
        raise ValueError(f"Nodo AST desconocido: {type(node).__name__}")


def build_combined_nfa(rule_asts):
    """
    Construye un NFA combinado para todas las reglas.

    Args:
        rule_asts: lista de (ast, rule_idx)

    Returns:
        NFA con estado de inicio con ε-transiciones a cada regla.
    """
    nfa = NFA()
    start = nfa.new_state()
    nfa.start = start

    for ast, rule_idx in rule_asts:
        s, e = _build_fragment(ast, nfa)
        nfa.add_eps(start, s)
        nfa.accepts[e] = rule_idx

    return nfa


# ═══════════════════════════════════════════════════════════════
#                        DFA
# ═══════════════════════════════════════════════════════════════

class DFA:
    """Autómata Finito Determinista."""

    def __init__(self):
        self.start = 0
        self.num_states = 0
        self.accepts = {}        # estado → índice de regla
        self.transitions = {}    # (estado, código_char) → estado_destino
        self.alphabet = set()    # conjunto de símbolos usados


# ──────────────────────── Construcción de Subconjuntos ────────────────────────

def _eps_closure(nfa, states):
    """Calcula la ε-cerradura de un conjunto de estados."""
    closure = set(states)
    stack = list(states)
    while stack:
        q = stack.pop()
        for sym, dest in nfa.transitions.get(q, []):
            if sym is EPSILON and dest not in closure:
                closure.add(dest)
                stack.append(dest)
    return frozenset(closure)


def _move(nfa, states, sym):
    """Calcula move(estados, símbolo)."""
    result = set()
    for q in states:
        for s, dest in nfa.transitions.get(q, []):
            if s == sym:
                result.add(dest)
    return result


def _get_alphabet(nfa):
    """Obtiene todos los símbolos no-epsilon usados en el NFA."""
    syms = set()
    for trans_list in nfa.transitions.values():
        for sym, _ in trans_list:
            if sym is not EPSILON:
                syms.add(sym)
    return syms


def nfa_to_dfa(nfa):
    """
    Convierte un NFA a DFA usando la construcción de subconjuntos.

    Returns:
        (DFA, dict: frozenset_of_nfa_states → dfa_state_id)
    """
    dfa = DFA()
    alphabet = _get_alphabet(nfa)
    dfa.alphabet = alphabet

    start_set = _eps_closure(nfa, {nfa.start})
    state_map = {}   # frozenset → dfa_state_id
    counter = [0]

    def get_or_create(nfa_states):
        if nfa_states not in state_map:
            sid = counter[0]
            counter[0] += 1
            state_map[nfa_states] = sid
            dfa.num_states = counter[0]

            # Estado aceptor: prioridad = menor índice de regla
            best = None
            for q in nfa_states:
                if q in nfa.accepts:
                    r = nfa.accepts[q]
                    if best is None or r < best:
                        best = r
            if best is not None:
                dfa.accepts[sid] = best
        return state_map[nfa_states]

    dfa.start = get_or_create(start_set)
    worklist = [start_set]
    visited = {start_set}

    while worklist:
        current = worklist.pop(0)
        cid = state_map[current]

        for sym in sorted(alphabet):
            moved = _move(nfa, current, sym)
            if not moved:
                continue
            nxt = _eps_closure(nfa, moved)
            nid = get_or_create(nxt)
            dfa.transitions[(cid, sym)] = nid
            if nxt not in visited:
                visited.add(nxt)
                worklist.append(nxt)

    return dfa, state_map


# ──────────────────────── Minimización de Hopcroft ────────────────────────

def minimize_dfa(dfa):
    """
    Minimiza el DFA usando el algoritmo de Hopcroft.
    Retorna un nuevo DFA minimizado.
    """
    states = set(range(dfa.num_states))
    alphabet = dfa.alphabet

    # Partición inicial: estados aceptores agrupados por regla + no aceptores
    groups = {}
    non_acc = set()
    for s in states:
        if s in dfa.accepts:
            r = dfa.accepts[s]
            groups.setdefault(('acc', r), set()).add(s)
        else:
            non_acc.add(s)

    P = list(groups.values())
    if non_acc:
        P.append(non_acc)

    # Verificar que todos los estados estén en alguna partición
    # (estados trampa no conectados van al grupo no_acc)

    W = list(P)  # worklist

    def find_group(s):
        for i, g in enumerate(P):
            if s in g:
                return i
        return -1

    changed = True
    while changed:
        changed = False
        new_P = []
        for group in P:
            if len(group) <= 1:
                new_P.append(group)
                continue
            # Intentar dividir el grupo
            split = False
            group_list = list(group)
            pivot = group_list[0]
            same = {pivot}
            diff = set()
            for s in group_list[1:]:
                ok = True
                for sym in alphabet:
                    t_pivot = dfa.transitions.get((pivot, sym), -1)
                    t_s = dfa.transitions.get((s, sym), -1)
                    g_pivot = find_group(t_pivot) if t_pivot != -1 else -1
                    g_s = find_group(t_s) if t_s != -1 else -1
                    if g_pivot != g_s:
                        ok = False
                        break
                if ok:
                    same.add(s)
                else:
                    diff.add(s)
            if diff:
                new_P.append(same)
                new_P.append(diff)
                changed = True
            else:
                new_P.append(group)
        P = new_P

    # Construir nuevo DFA con estados representantes
    new_dfa = DFA()
    new_dfa.alphabet = alphabet

    # Representante de cada grupo = mínimo estado
    rep = {}   # estado original → rep del grupo
    groups_final = []
    for g in P:
        r = min(g)
        for s in g:
            rep[s] = r
        groups_final.append((r, g))

    # Estado inicio del nuevo DFA
    new_dfa.start = rep[dfa.start]

    # Recopilar estados únicos
    new_states = set(rep.values())
    new_dfa.num_states = len(new_states)

    # Renombrar estados 0..n-1
    state_rename = {s: i for i, s in enumerate(sorted(new_states))}
    new_dfa.start = state_rename[new_dfa.start]

    for s in new_states:
        if s in dfa.accepts:
            new_dfa.accepts[state_rename[s]] = dfa.accepts[s]

    # Transiciones
    for (s, sym), t in dfa.transitions.items():
        rs = rep.get(s, s)
        rt = rep.get(t, t)
        ns = state_rename.get(rs)
        nt = state_rename.get(rt)
        if ns is not None and nt is not None:
            new_dfa.transitions[(ns, sym)] = nt

    return new_dfa
