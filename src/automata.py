# automata.py - Direct DFA Construction from AST
# Universidad del Valle de Guatemala - CC3071
from regex_ast import LeafNode, ConcatNode, EpsilonNode

class DirectDFA:
    def __init__(self, ast_root):
        self.root = ast_root
        self.followpos = {}
        self.pos_mapping = {}
        self.states = []
        self.transitions = {}  # {state_index: {symbol: next_state_index}}
        self.accepts = {}  # {state_index: rule_id}
        self.start = 0
        self._build()

    def _assign_positions(self, node, counter):
        if isinstance(node, LeafNode):
            node.pos = counter[0]
            counter[0] += 1
        elif hasattr(node, 'children'):
            for child in node.children():
                self._assign_positions(child, counter)
        elif hasattr(node, 'left'):
            self._assign_positions(node.left, counter)
            self._assign_positions(node.right, counter)
        elif hasattr(node, 'child'):
            self._assign_positions(node.child, counter)

    def _build(self):
        # Assign positions to leaves
        counter = [1]
        self._assign_positions(self.root, counter)

        # Calculate nullable, firstpos, lastpos, followpos
        self.root.calculate_properties(self.followpos, self.pos_mapping)

        # Build DFA states
        start_set = frozenset(self.root.firstpos)
        self.states.append(start_set)
        unmarked = [0]
        state_map = {start_set: 0}

        while unmarked:
            current_idx = unmarked.pop(0)
            current_set = self.states[current_idx]
            
            
            # Group positions by symbol
            sym_positions = {}
            for pos in current_set:
                leaf = self.pos_mapping[pos]
                if leaf.rule_id is not None:
                    # Accepting position
                    if current_idx not in self.accepts or leaf.rule_id < self.accepts[current_idx]:
                        # Lower rule_id = higher priority
                        self.accepts[current_idx] = leaf.rule_id
                    continue
                
                # Normal transition
                if leaf.code is not None:
                    sym_positions.setdefault(leaf.code, set()).update(self.followpos.get(pos, set()))
                elif leaf.codes is not None:
                    for c in leaf.codes:
                        sym_positions.setdefault(c, set()).update(self.followpos.get(pos, set()))
                else: 
                    # ANY
                    for c in range(128):
                        sym_positions.setdefault(c, set()).update(self.followpos.get(pos, set()))

            for sym, pos_set in sym_positions.items():
                if not pos_set: continue
                target = frozenset(pos_set)
                if target not in state_map:
                    new_idx = len(self.states)
                    self.states.append(target)
                    state_map[target] = new_idx
                    unmarked.append(new_idx)
                self.transitions.setdefault(current_idx, {})[sym] = state_map[target]



