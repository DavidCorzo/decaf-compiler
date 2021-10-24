from typing import OrderedDict
from yaml import safe_load
import re

def is_nonterminal(string):
    return bool(re.match("<(.*)>", string))

def num_label_maker() -> int:
    """
    Generador para poder generar estados únicos. Usados en estados de nfa.
    """
    num = 0
    while True:
        yield num
        num += 1

label_gen = num_label_maker()

productions_filename = 'example.yaml'
with open(productions_filename) as file:
    # grammar_rules = safe_load(file)
    content = safe_load(file)
    grammar_rules = {lhs:set() for lhs in content.keys()}
    for lhs, rhs_list in content.items():
        for rhs in rhs_list:
            grammar_rules[lhs].add(tuple(rhs))
    grammar_rules = {lhs:tuple(rhs) for lhs, rhs in content.items()}
    file.close()


class parsing_state:
    def __init__(self, productions):
        self.state_name = next(label_gen)
        self.productions = productions
        self.transitions = []
        self.compute_closure()

    def compute_closure(self):
        rules_pending_add = set()
        for lhs, rhs_list in self.productions.items():
            for rhs in rhs_list:
                dot_pos = rhs.index('•')
                if (dot_pos + 1) < len(rhs):
                    after_dot = rhs[dot_pos + 1]
                    if (is_nonterminal(after_dot)):
                        rules_pending_add.add(after_dot)
        for pending_rule in rules_pending_add:
            if (self.productions.get(pending_rule) == None):
                self.productions[pending_rule] = list()
            for rule in grammar_rules[pending_rule]:
                r = rule.copy()
                r.insert(0, '•')
                self.productions[pending_rule].append(tuple(sorted(r)))
        print(self.productions)

    def compute_transitions(self):
        pass

class parsing_automaton:
    def __init__(self, start_production):
        kernel_state_0 = {start_production: list(grammar_rules[start_production])}
        kernel_state_0[start_production][0].insert(0, '•')
        kernel_state_0[start_production][0] = tuple(kernel_state_0[start_production][0])
        print(kernel_state_0)
        parsing_state(kernel_state_0)
    

        
if __name__ == '__main__':
    pa = parsing_automaton('<S>')
    