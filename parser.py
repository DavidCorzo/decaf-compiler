from os import close
from types import FrameType
from typing import OrderedDict
from yaml import safe_load
import re
from dataclasses import dataclass
from copy import deepcopy

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

start_production = '<P>'
productions_filename = 'G_10.yaml'
with open(productions_filename) as file:
    grammar_rules = safe_load(file)
    items = {}
    index = 0
    for lhs, rhs_l in grammar_rules.items():
        offset = int(bool(lhs != start_production))
        for rhs in rhs_l:
            for index_marker in range(len(rhs) + offset):
                rhs_item = rhs.copy()
                rhs_item.insert(index_marker, '•')
                items.update({index : tuple([lhs] + rhs_item)})
                index += 1
    reverse_item = {v:k for k,v in items.items()}
    closed_rules = grammar_rules.copy()
    for r1 in closed_rules.values():
        for r2 in r1:
            r2.insert(0, '•')
    for r1, r2 in closed_rules.items():
        closed_rules[r1] = [tuple([r1] + x) for x in closed_rules[r1]]
    closed_indexes = {k:set([reverse_item[x] for x in v]) for k,v in closed_rules.items()}
    file.close()

@dataclass(repr=True)
class p_state:
    def __init__(self, items_i, transitions):
        self.items_i = items_i
        self.transitions = transitions
    def __repr__(self) -> str:
        return f"(items={self.items_i}, trans={self.transitions})"
    def __str__(self) -> str:
        return f"(items={self.items_i}, trans={self.transitions})"

LHS, RHS = 0, 1
class parsing_automaton:
    def __init__(self):
        self.states = {}
        self.item_closures = {}
        self.accept_items = set()
        self.closure_table = {}
        self.closures()
        self.create_states()
        # functionality for closure
        self.state = None
        self.productions_processed = None
    
    def closures(self):
        for item_index in items.keys():
            self.state = set()
            self.productions_processed = set([start_production])
            self.get_closure_of_an_item(set([item_index]))
            self.closure_table[item_index] = self.state

    def get_closure_of_an_item(self, set_of_indexes):
        self.state |= set_of_indexes
        actual_items = set()
        for ai in set_of_indexes:
            actual_items.add(items[ai])
        pending_productions = set()
        for item in actual_items:
            lhs = item[LHS]
            rhs = item[RHS:]
            accept = ('$' in rhs)
            dot_pos = rhs.index('•')
            if (dot_pos + 1) < len(rhs):
                after_dot = rhs[dot_pos + 1]
                if is_nonterminal(after_dot):
                    pending_productions.add(after_dot)
        if len(pending_productions) == 0:
            return
        pending_items = set()
        for production in pending_productions:
            if production not in self.productions_processed:
                pending_items |= closed_indexes[production]
                self.productions_processed.add(production)
        self.get_closure_of_an_item(pending_items)
    
    def create_states(self):
        self.create_state(set([0]))
        
    def create_state(self, set_of_items):
        closure_of_items = set()
        for coi in set_of_items:
            closure_of_items |= self.closure_table[coi]
        state_key = sorted(tuple(closure_of_items))
        actual_items = set()
        for ai in closure_of_items:
            actual_items.add(items[ai])
        # if not self.states.get(state_key):
        #     self.states[state_key] = dict()
        transitions = dict()
        for item in actual_items:
            lhs = item[LHS]
            rhs = item[RHS:]
            dot_pos = rhs.index('•')
            if (dot_pos + 1) < len(rhs):
                after_dot = rhs[dot_pos + 1]
                if (after_dot != '$'):
                    if transitions.get(after_dot):
                        transitions[after_dot].add(reverse_item[item])
                    else:
                        transitions[after_dot] = set([reverse_item[item]])
        if len(transitions) == 0:
            return state_key
        else:
            for transition, new_state in self.states[state_key].items():
                print(new_state)
                # self.states[state_key] = self.create_state(new_state)
        
    # def get_closures(self):
    #     print(self.get_closure_of_item({3}))
    #     # for index in items.keys():
    #     #     self.item_closures[index] = self.get_closure_of_item(index)
    #     # for k,v in self.item_closures.items():
    #     #     print(k,v)                
    
    # def index_to_items(self, set_of_indexes):
    #     actual_items = set()
    #     for item in set_of_indexes:
    #         actual_items.add(items[item])
    #     return actual_items
    
    # def find_pending_add(self, set_items, already_visited) -> set():
    #     pending_add = set()
    #     for it in set_items:
    #         lhs = it[LHS]
    #         rhs = it[RHS:]
    #         dot_pos = rhs.index('•')
    #         if (dot_pos + 1) < len(rhs):
    #             after_dot = rhs[dot_pos + 1]
    #             if is_nonterminal(after_dot):
    #                 print(it)
    #                 exit()
    #                 for item in closed_rules[it]:
    #                     pending_add.add(item)
    #     print(already_visited)
    #     pending_add.difference_update(already_visited)
    #     print(pending_add)
    #     exit()
    #     return pending_add
        
    
    # def get_closure_of_item(self, set_of_indexes, state_items=None, already_visited=None):
    #     if not state_items:
    #         state_items = set()
    #     state_items |= set_of_indexes
    #     actual_items = self.index_to_items(set_of_indexes)
    #     if already_visited == None:
    #         already_visited = set()
    #     pending_add = self.find_pending_add(actual_items, already_visited)
    #     for ai in actual_items:
    #         already_visited.add(reverse_item[ai])
    #     if len(pending_add) == 0:
    #         return state_items
    #     for pa in pending_add:
    #         if pa not in already_visited:
    #             rules = closed_rules[pa]
    #             pending_recursion = set()
    #             for r in rules:
    #                 it_index = reverse_item[r]
    #                 pending_recursion.add(it_index)
    #     return self.get_closure_of_item(pending_recursion, state_items, already_visited)
        
    # def add_new_state(self, state):
    #     if not self.states.get(tuple(sorted(state))):
    #         self.states[tuple(sorted(state))] = set()
    
    # def advance_dot_by_one(self, item):
    #     lhs = item[LHS]
    #     rhs = list(item[RHS:])
    #     dot_pos = rhs.index('•')
    #     if (dot_pos != (len(rhs) - 1)):
    #         rhs.pop(dot_pos)
    #         rhs.insert(dot_pos + 1, '•')

    
    # def get_edge(self, item):
    #     lhs = item[LHS]
    #     rhs = item[RHS:]
    #     dot_pos = rhs.index('•')
    #     if (dot_pos + 1) < len(rhs):
    #         return rhs[dot_pos + 1]
    #     return None
    
    # def get_edges(self, item_set):
    #     transitions = set()
    #     for it in item_set:
    #         t = self.get_edge(it)
    #         if (t):
    #             transitions.add(t)
    #     return transitions

    # def compute_edges(self, state):
    #     # state is the key in the states dictionary
    #     actual_items = self.index_to_items(state)
    #     transitions = self.get_edges(actual_items)
    #     # for ai in actual_items:
    #     #     pass
    #     print(f"trans={transitions}")
            


        

p = parsing_automaton()
