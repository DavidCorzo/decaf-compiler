from functools import lru_cache
from typing import OrderedDict
from yaml import safe_load
import re
from dataclasses import dataclass
from copy import deepcopy

def is_nonterminal(string):
    if string == None: return False
    return ((string[0] == '<') and (string[-1] == '>')) # bool(re.match("<(.*)>", string))

def is_terminal(string):
    return not is_nonterminal(string)
# def none_to_epsilon(element):
#     if (element == None): return 'ε'
#     else: return element

LHS, RHS = 0, 1
class lr_0:
    def __init__(self, start_production, productions_filename):
        self.start_production = start_production
        self.productions_filename = productions_filename
        self.grammar_rules = self.items = self.reverse_item = self.closed_indexes = self.closed_rules = None
        self.load_grammar()
        # class attributes
        self.states = {}
        self.item_closures = {}
        self.accept_items = set()
        self.closure_table = {}
        self.closures_to_states = dict()
        self.state = self.productions_processed = None
        self.closures()
        self.create_states()
    
    def load_grammar(self):
        with open(self.productions_filename) as file:
            self.grammar_rules = safe_load(file)
            self.items = {}
            index = 0
            for lhs, rhs_l in self.grammar_rules.items():
                offset = int(bool(lhs != self.start_production))
                for rhs in rhs_l:
                    for index_marker in range(len(rhs) + offset):
                        rhs_item = rhs.copy()
                        rhs_item.insert(index_marker, '•')
                        self.items.update({index : tuple([lhs] + rhs_item)})
                        index += 1
            self.reverse_item = {v:k for k,v in self.items.items()}
            self.closed_rules = deepcopy(self.grammar_rules)
            for r1 in self.closed_rules.values():
                for r2 in r1:
                    r2.insert(0, '•')
            for r1, r2 in self.closed_rules.items():
                self.closed_rules[r1] = [tuple([r1] + x) for x in self.closed_rules[r1]]
            self.closed_indexes = {k:set([self.reverse_item[x] for x in v]) for k,v in self.closed_rules.items()}
            file.close()
    
    def closures(self):
        for item_index in self.items.keys():
            self.state = set()
            self.productions_processed = set([self.start_production])
            self.get_closure_of_an_item(set([item_index]))
            self.closure_table[item_index] = self.state

    # @lru_cache(maxsize=None)
    def get_closure_of_an_item(self, set_of_indexes):
        self.state |= set_of_indexes
        actual_items = set()
        for ai in set_of_indexes:
            actual_items.add(self.items[ai])
        pending_productions = set()
        for item in actual_items:
            lhs = item[LHS]
            rhs = item[RHS:]
            # accept = ('$' in rhs)
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
                pending_items |= self.closed_indexes[production]
                self.productions_processed.add(production)
        self.get_closure_of_an_item(pending_items)
    
    def create_states(self):
        self.create_state(set([0]))
        for state, transitions in self.states.items():
            for token, unclosed_state in transitions.items():
                self.states[state][token] = self.closures_to_states[unclosed_state]
        # for k,v in self.states.items():
        #     print(k, ':', v)
        
    def create_state(self, set_of_items):
        closure_of_items = set()
        for coi in set_of_items:
            closure_of_items |= self.closure_table[coi]
        items_tuple = tuple(sorted(set_of_items))
        state_key = tuple(sorted(closure_of_items))
        if not self.closures_to_states.get(items_tuple):
            # register that we are going to calculate this in this iteration.
            self.closures_to_states[items_tuple] = state_key
        else: 
            # this pair of items has already been calculated
            return self.closures_to_states[items_tuple]
        actual_items = set()
        for ai in closure_of_items:
            actual_items.add(self.items[ai])
        if self.states.get(state_key):
            return state_key
        transitions = dict()
        for item in actual_items:
            lhs = item[LHS]
            rhs = item[RHS:]
            dot_pos = rhs.index('•')
            if (dot_pos + 1) < len(rhs):
                after_dot = rhs[dot_pos + 1]
                if (after_dot != '$'):
                    if transitions.get(after_dot):
                        transitions[after_dot].add(self.reverse_item[item])
                    else:
                        transitions[after_dot] = set([self.reverse_item[item]])
        # advance by one all the transitions. 
        # if this is not done there is infinite recursion.
        for transition, item_set in transitions.items():
            next_items = set()
            for it in item_set:
                advanced_by_one = self.advance_dot_by_one(it)
                if advanced_by_one:
                    next_items.add(advanced_by_one)
            transitions[transition] = tuple(sorted(next_items))
        # print("", end='')
        # base case is when transitions are 0.
        if len(transitions) == 0:
            return state_key
        else:
            # if self.states.get(state_key):
            #     # print(self.states[state_key])
            #     for transition, new_state in transitions.items():
            #         if self.states[state_key].get(transition):
            #             self.states[state_key][transition] |= new_state
            # else:
            if not (self.states.get(state_key)):
                self.states[state_key] = transitions
            for transition, new_state in self.states[state_key].items():
                possible_state_key = tuple(sorted(new_state))
                if possible_state_key not in self.closures_to_states.keys():
                    # print(f"closures_to_states={self.closures_to_states}")
                    state = self.create_state(new_state)
                # else:
                #     state = self.closures_to_states[possible_state_key]
                # self.states[state_key][transition] = state
    
    def advance_dot_by_one(self, item_index):
        item = self.items[item_index]
        lhs = item[LHS]
        rhs = list(item[RHS:])
        dot_pos = rhs.index('•')
        if (dot_pos + 1) < len(rhs):
            after_dot = rhs[dot_pos + 1]
            if after_dot == '$':
                return None
            else:
                item = list(item)
                dot_pos = item.index('•')
                item.remove('•')
                item.insert(dot_pos + 1, '•')
                return self.reverse_item[tuple(item)]
        else:
            return None

SHIFT, REDUCE, GOTO = 0, 1, 2
class slr:
    def __init__(self, lr_0_assembled:lr_0):
        self.grammar_rules = lr_0_assembled.grammar_rules
        self.states = lr_0_assembled.states
        self.start_production = lr_0_assembled.start_production
        self.slr_parsing_table = {}
        self.firsts_table = {}
        self.follow_table = {}
        self.first_of_current = None
        self.follow_pending_stack = list()
        self.current = None
        self.firsts()
        self.follows()
    
    def firsts(self):
        for lhs in self.grammar_rules.keys():
            self.calculate_feasable_first(lhs)
        pending_firsts = set(self.grammar_rules.keys()) - set(self.firsts_table.keys())
        for lhs in pending_firsts:
            first = self.calculate_firsts(lhs)
        # for lhs in pending_firsts:
        #     first_of_current = set()
        #     for rhs_tokens in self.grammar_rules[lhs]:
        #         ft = self.firsts_table
        #         first_of_current |= self.calculate_first(lhs, rhs_tokens)
        #     if self.firsts_table.get(lhs):
        #         self.firsts_table[lhs] |= deepcopy(first_of_current)
        #     else:
        #         self.firsts_table[lhs] = deepcopy(first_of_current)
        print("FIRST")
        # print(self.firsts_table)
        for k,v in self.firsts_table.items():
            print(k, v)
    
    def get_first_of_non_terminal(self, lhs):
        return {x[0] for x in self.grammar_rules[lhs]}
    
    # def calculate_first(self, lhs, rhs_tokens):
    #     first = set()
    #     rhs_index = 0
    #     for rhs in rhs_tokens:
    #         f:set = self.get_first(rhs) - {'$'}
    #         # returns all terminals
    #         if (None in f) and (rhs_index != len(rhs_tokens) - 1):
    #             # if epsilon is in first and this element is not the last one then remove it. 
    #             # It will get added on later in the next production if there is any.
    #             first |= deepcopy(f - {None})
    #         else:
    #             first |= f
    #         rhs_index += 1
    #         if (None not in f):
    #             break
    #     return first
    
    # def get_first(self, rhs_element):
    #     ft = self.firsts_table
    #     if is_nonterminal(rhs_element):
    #         # we know its a nonterminal
    #         if self.firsts_table.get(rhs_element):
    #             return self.firsts_table[rhs_element]
    #         first = self.get_first_of_non_terminal(rhs_element)
    #         terminal = {x for x in first if is_terminal(x)}
    #         non_terminals = first - terminal
    #         for nt in non_terminals:
    #             for rhs in self.grammar_rules[nt]:
    #                 terminal |= self.calculate_first(nt, rhs)
    #         return terminal
    #     else:
    #         # we know it is a terminal
    #         return set([rhs_element])
        
    def calculate_firsts(self, lhs):
        # lhs is a non terminal
        if self.firsts_table.get(lhs):
            return self.firsts_table[lhs]
        ft = self.firsts_table
        rhs_list = deepcopy(self.grammar_rules[lhs])
        first = set()
        for rhs in rhs_list:
            rhs_element_index = 0
            for rhs_element in rhs:
                f = set()
                if is_nonterminal(rhs_element):
                    if self.firsts_table.get(rhs_element): 
                        f |= self.firsts_table[rhs_element]
                    else: 
                        f |= self.calculate_firsts(rhs_element)
                    if (None in f) and (rhs_element_index != len(rhs) - 1):
                        first |= f - {None}
                    else: 
                        first |= f
                    if (None not in f):
                        break
                else:
                    first |= {rhs_element}
                    break
                rhs_element_index += 1
        first -= {'$'}
        if self.firsts_table.get(lhs):
            self.firsts_table[lhs] |= first
        else:
            self.firsts_table[lhs] = first
        return first
    
    # def calculate_first(self, lhs):
    #     dummy1 = self.first_of_current
    #     dummy2 = self.firsts_table
    #     if self.firsts_table.get(lhs): 
    #         return deepcopy(self.firsts_table[lhs])
    #     firsts = self.get_first_of_non_terminal(lhs)
    #     terminals = {x for x in firsts if is_terminal(x)}
    #     non_terminals = firsts - terminals
    #     if len(non_terminals) == 0:
    #         return terminals 
    #     for pnt in non_terminals:
    #         firsts |= self.calculate_first(pnt)
    #     if self.current == lhs:
    #         rhs_list = deepcopy(self.grammar_rules[lhs])
    #         for rhs in rhs_list:
    #             if is_terminal(rhs[0]):
    #                 continue
    #             else:
    #                 if None in self.firsts_table[rhs[0]]:
    #                     token_index = 0
    #                     if (token_index + 1) < len(rhs):
    #                         pass
                        
                            
                        
            
    # def calculate_first(self, lhs, rhs_i):
    #     dummy = self.first_of_current
    #     dummy2 = self.firsts_table
    #     first = deepcopy(self.grammar_rules[lhs][rhs_i][0])
    #     if not is_nonterminal(first):
    #         self.first_of_current.add(first)
    #         return
    #     rhs_list = deepcopy(self.grammar_rules[first])
    #     for rhs_next in range(len(rhs_list)):
    #         if self.firsts_table.get(first):
    #             self.first_of_current |= deepcopy(self.firsts_table[first])
    #         else:
    #             self.calculate_first(first, rhs_next)
        # if None in self.first_of_current:
        #     if (index_of_token + 1) < len(self.grammar_rules[lhs][rhs_i]):
        #         if (self.grammar_rules[lhs][rhs_i][index_of_token + 1] == '$'):
        #             return
        #         self.first_of_current.remove(None)
        #         self.calculate_first(lhs, rhs_i, index_of_token + 1)
        #     else: 
        #         return
    
    def calculate_feasable_first(self, lhs):
        non_terminals = set()
        for rhs_list in self.grammar_rules[lhs]:
            if is_nonterminal(rhs_list[0]):
                return 
            else: 
                non_terminals.add(rhs_list[0])
        self.firsts_table[lhs] = non_terminals

    def follows(self):
        # follow operation can only be done on non-terminals
        self.follow_table = {lhs:set() for lhs in self.grammar_rules.keys()}
        self.follow_table[self.start_production].add('$')
        for lhs, rhs_list in self.grammar_rules.items():
            for rhs in rhs_list:
                for rhs_element in range(len(rhs)):
                    self.calculate_follow(lhs, rhs, rhs_element)
        self.make_pending_follows()
        print("FOLLOWS")
        for k,v in self.follow_table.items():
            print(k, v)
    
    def is_nullable(self, production):
        if not is_nonterminal(production): return False
        return None in self.firsts_table[production]
    
    def first_sequence(self, b,  beta):
        for beta_production in beta:
            if is_nonterminal(beta_production):
                self.follow_table[b] |= (deepcopy(self.firsts_table[beta_production]) - {None})
                if not self.is_nullable(beta_production):
                    break
            else:
                self.follow_table[b].add(beta_production)
    
    def beta_contains_epsilon(self, beta):
        # <A> -> <B> <BETA> where beta contains epsilon 
        # then follow(<B>) <- follow(<A>) - {e}
        if (beta == None): return False
        nullable = [self.is_nullable(beta_production) for beta_production in beta]
        a = all(nullable)
        return a
        # if all(nullable):
        #     self.follow_pending_stack.add((b, lhs))
            

    def calculate_follow(self, lhs, rhs, rhs_index):
        b = rhs[rhs_index]
        if not is_nonterminal(b): return
        beta = None
        if (rhs_index + 1) < len(rhs):
            beta = rhs[rhs_index + 1:]

        if beta:
            dummy = self.follow_table[b]
            self.first_sequence(b, beta)
            dummy = self.follow_table[b]
        if (beta == None) or (self.beta_contains_epsilon(beta)): # 1 production, is the last one
            if b != lhs:
                self.follow_pending_stack.append((b, lhs))
        # print(self.follow_table)
        # print(self.follow_pending_stack)
        # print('*'*100)
        # contains_epsilon = None in self.follow_table[b]
        # if contains_epsilon or (beta == None):
            

    def make_pending_follows(self):
        for pf in self.follow_pending_stack:
            self.follow_table[pf[0]] |= deepcopy(self.follow_table[pf[1]])
    
    # def calculate_follow_of_production(self, lhs, rhs, index=None):
    #     pass
        # if len(rhs) == 1:
        #     if is_nonterminal(rhs[0]):
        #         self.follow_pending_stack.add((rhs[0], lhs))
        #     else:
        #         pass
        # for rhs_element in range(len(rhs)):
        #     if is_nonterminal(rhs[rhs_element]):
        #         if (rhs_element + 1) < len(rhs): # first element, or penultimate element
        #             next_one = rhs[rhs_element + 1]
        #             first_next_one = self.firsts_table[next_one]
        #             if None in first_next_one:
        #                 print(first_next_one)
        #                 # first_next_one |= self.calculate_follow_of_production(lhs, rhs)
        #         else: # just one element or is the last element
                    
        #     else:
        #         continue    
    
    # def calculate_follow(self):
    #     # rule 1: follow(start) = {$}
    #     self.follow_table[self.start_production].add('$')
    #     # rule 2: <B> <BETA> where <BETA> exists then follow(<B>) = first(<BETA>) - {None}
    #     for lhs, rhs_list in self.grammar_rules.items():
    #         for rhs in range(len(rhs_list)):
    #             for rhs_element in range(len(rhs_list[rhs])):
    #                 current = rhs_list[rhs][rhs_element]
    #                 if not is_nonterminal(current):
    #                     continue
    #                 else:
    #                     if (rhs_element + 1) < len(rhs_list[rhs]):
    #                         next_one = rhs_list[rhs][rhs_element + 1]
    #                         if is_nonterminal(next_one):
    #                             # current and next_one are non terminals
    #                             first_next_one = deepcopy(self.firsts_table[next_one])
    #                             if None in first_next_one:
    #                                 if (rhs_element + 2) < len(rhs_list[rhs]):
    #                                     for prod in rhs_list[rhs][(rhs_element + 2):]:
    #                                         f = deepcopy(self.firsts_table[prod])
    #                                         first_next_one |= f
    #                                         if None not in self.firsts_table[prod]:
    #                                             break
    #                                 else:
    #                                     self.follow_pending_stack.add((current, lhs))
    #                             first_next_one.remove(None)
    #                             self.follow_table[current] |= first_next_one
    #                         else:
    #                             # current is non terminal and next_one is terminal: first(terminal) = {terminal}
    #                             self.follow_table[current].add(next_one)
    #                     else:
    #                         # non terminal last one: follow(<last>) = follow(lhs)
    #                         if (lhs != current):
    #                             self.follow_pending_stack.add((current, lhs))
    #                             # print(f"follow_pending_stack={self.follow_pending_stack}") # follow(current) = follow(lhs)
    #                 # print(self.follow_table)
    #     # print(f"follow_pending_stack={self.follow_pending_stack}") # follow(current) = follow(lhs)
    #     print(self.follow_table)

        # print(self.follow_pending_stack)
        # for pf in self.follow_pending_stack:
        #     self.follow_table[pf[0]] |= self.follow_table[pf[1]]
        # print(self.follow_table)



p = lr_0('<S´>', 'grammars/example.yaml')
s = slr(p)
