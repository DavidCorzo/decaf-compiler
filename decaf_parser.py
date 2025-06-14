from yaml import safe_load
from copy import deepcopy
import pickle
from decaf_scanner import scanner
import sys

def is_nonterminal(string):
    if string == None: return False
    return ((string[0] == '<') and (string[-1] == '>')) # bool(re.match("<(.*)>", string))

def is_terminal(string):
    return not is_nonterminal(string)

def is_terminal_with_value(string):
    return ((string[0] == '%') and (':' in string[1:-1]) and (string[-1] == '%'))

def is_pseudo_terminal(string):
    return ((string[0] == '%') and (string[-1] == '%'))

def print_dict(d):
    for k,v in d.items(): print(k,v)

def num_label_maker() -> int:
    """
    Generador para poder generar estados únicos. Usados en estados de nfa.
    """
    num = 0
    while True:
        yield num
        num += 1
    
def printable(token):
    if token == None:
        token = 'ε'
    return token

intended_print = print
intended_exit = exit

def parser_std_error(str):
    intended_print(f'Parsing error: {str}.')
    intended_print(f'In method {sys._getframe(1).f_code.co_name}.')
    intended_exit(-1)

LHS, RHS = 0, 1
class lr_0:
    def __init__(self, start_production, productions_filename, build=False, save=False):
        self.lr_0_filename                      = f'{productions_filename}.pickle'
        self.start_production                   = start_production
        self.grammar_rules                      = None
        self.items                              = None
        self.reverse_item                       = None
        self.accept_item                        = None
        # class attributes
        self.states                             = dict()
        self.start_state                        = None
        self.renamed_states                     = dict()
        self.reveresed_renamed_states           = dict()
        self.leaf_states                        = set()
        self.accept_state                       = None
        self.terminals                          = set()
        self.nonterminals                       = set()
        self.epsilon_items                      = set()
        self.epsilon_states                     = dict()
        if build:
            # attributes
            self.closed_rules                   = None
            self.closed_indexes                 = None
            self.productions_filename           = f'{productions_filename}.yaml'
            self.closure_table                  = dict()
            self.closures_to_states             = dict()
            self.closure_of_current_item        = None
            self.productions_processed          = None
            self.state_label_gen                = num_label_maker()
            self.load_grammar()
            self.closures()
            self.create_states()
        else:
            self.load_lr_0_dfa()
        if save: 
            self.save_lr_0_dfa()
    
    def load_grammar(self):
        with open(self.productions_filename) as file:
            self.grammar_rules = safe_load(file)
            # get terminals
            for rhs_list in self.grammar_rules.values():
                for rhs in rhs_list:
                    for rhs_element in rhs:
                        if is_nonterminal(rhs_element): self.nonterminals.add(rhs_element)
                        else: self.terminals.add(rhs_element)
            self.items = {}
            index = 0
            for lhs, rhs_l in self.grammar_rules.items():
                for rhs in rhs_l:
                    epsilon_present = int(rhs == [None])
                    for index_marker in range(len(rhs) + 1 - epsilon_present):
                        rhs_item = rhs.copy()
                        if rhs_item == [None]: 
                            rhs_item = ['•']
                        else:
                            rhs_item.insert(index_marker, '•')
                            if  (not self.accept_item) and (len(rhs_item) >= 2) and \
                                    (rhs_item[-2] == '$') and (rhs_item[-1] == '•'):
                                self.accept_item = index
                        self.items.update({index : tuple([lhs] + rhs_item)})
                        index += 1
            self.reverse_item = {v:k for k,v in self.items.items()}
            self.closed_rules = deepcopy(self.grammar_rules)
            for r1 in self.closed_rules.values():
                for r2 in r1:
                    if r2 == [None]:
                        r2.clear()
                    r2.insert(0, '•')
            for r1, r2 in self.closed_rules.items():
                self.closed_rules[r1] = [tuple([r1] + x) for x in self.closed_rules[r1]]
            self.closed_indexes = {k:set([self.reverse_item[x] for x in v]) for k,v in self.closed_rules.items()}
            for index, item in self.items.items():
                if (len(item) == 2) and (item[RHS] == '•'):
                    self.epsilon_items.add(index)
            file.close()
    
    def closures(self):
        for item_index in self.items.keys():
            self.closure_of_current_item = set()
            self.productions_processed = set([self.start_production])
            self.get_closure_of_an_item(set([item_index]))
            self.closure_table[item_index] = self.closure_of_current_item

    def get_closure_of_an_item(self, set_of_indexes):
        self.closure_of_current_item |= set_of_indexes
        actual_items = {self.items[ai] for ai in set_of_indexes}
        pending_productions = set()
        for item in actual_items:
            lhs = item[LHS]
            rhs = item[RHS:]
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
    
    def __repr__(self) -> str:
        s = str()
        for state, transitions in self.states.items():
            s += f"state={state}\n"
            state = self.reveresed_renamed_states[state]
            for item_i in state:
                item = self.items[item_i]
                s += f"{item[LHS]} -> "
                for i in item[RHS:]:
                    s += i + ' '
                s += '\n'
            s += f"{transitions}\n\n"
        return s
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def create_state(self, set_of_item_indexes):
        state_key = tuple(sorted(list(self.get_closure_of_a_set_of_items(set_of_item_indexes))))
        if (self.start_state == None) and (0 in state_key): 
            self.start_state = state_key
        if self.renamed_states.get(state_key):
            return self.renamed_states[state_key]
        renamed_state = self.get_or_create_renamed_state(state_key)
        self.determine_epsilon_states(state_key, renamed_state)
        transitions = self.calculate_transitions(self.get_actual_items(state_key))
        if len(transitions) == 0:
            if (self.accept_item in state_key): 
                if not self.accept_state: self.accept_state = self.renamed_states[state_key]
                elif (self.accept_state == self.renamed_states[state_key]): pass
                else: intended_print("second accept state present")
            self.leaf_states.add(renamed_state)
            return renamed_state
        self.states[renamed_state] = transitions
        for token, next_unclosed_state in self.states[renamed_state].items():
            self.states[renamed_state][token] = self.create_state(next_unclosed_state)
        return renamed_state
    
    def determine_epsilon_states(self, state_key, renamed_state):
        epsilon_state = set(state_key) & self.epsilon_items
        if len(epsilon_state) > 0:
            if len(epsilon_state) != 1:
                parser_std_error(f'reduce-reduce by two productions on epsilon, ambiguous language.')
            self.epsilon_states[renamed_state] = list(epsilon_state)[0]
            

    def get_or_create_renamed_state(self, state_key):
        if self.renamed_states.get(state_key):
            return self.renamed_states[state_key]
        else:
            state_name = next(self.state_label_gen)
            self.renamed_states[state_key] = deepcopy(state_name)
            self.reveresed_renamed_states[state_name] = state_key
            self.states[state_name] = dict()
            return state_name
    
    def calculate_transitions(self, actual_items) -> dict:
        transitions = dict()
        for item in actual_items:
            lhs = item[LHS]
            rhs = item[RHS:]
            dot_pos = rhs.index('•')
            if (dot_pos + 1) < len(rhs):
                after_dot = rhs[dot_pos + 1]
                if transitions.get(after_dot):
                    transitions[after_dot].add(self.reverse_item[item])
                else:
                    transitions[after_dot] = set([self.reverse_item[item]])
        for transition, item_set in transitions.items():
            next_items = set()
            for it in item_set:
                advanced_by_one = self.advance_dot_by_one(it)
                if advanced_by_one:
                    next_items.add(advanced_by_one)
            transitions[transition] = tuple(sorted(list(next_items)))
        return transitions
    
    def advance_dot_by_one(self, item_index):
        item = self.items[item_index]
        lhs = item[LHS]
        rhs = list(item[RHS:])
        dot_pos = rhs.index('•')
        if (dot_pos + 1) < len(rhs):
            after_dot = rhs[dot_pos + 1]
            item = list(item)
            dot_pos = item.index('•')
            item.remove('•')
            item.insert(dot_pos + 1, '•')
            return self.reverse_item[tuple(item)]
        else:
            return None
    
    def get_closure_of_a_set_of_items(self, set_of_item_indexes):
        closure_of_items = set()
        for soii in set_of_item_indexes: closure_of_items |= self.closure_table[soii]
        return closure_of_items
    
    def get_actual_items(self, item_indexes_iterable) -> set:
        return {self.items[ai] for ai in item_indexes_iterable}
    
    def load_lr_0_dfa(self):
        with open(self.lr_0_filename, mode='rb') as file:
            retrieved = pickle.load(file)
            # print(set(self.__dict__.keys()) - set(retrieved.keys()))
            for attributes in self.__dict__.keys():
                if retrieved.get(attributes):
                    self.__dict__[attributes] = retrieved[attributes]
                else:
                    print(attributes)
                    self.__dict__[attributes] = None
            file.close()
    
    def save_lr_0_dfa(self):
        with open(self.lr_0_filename, mode='wb') as file:
            to_save = self.__dict__
            to_save.pop('state_label_gen', None)
            pickle.dump(to_save, file)
            file.close()
    

SHIFT, REDUCE, GOTO, ACCEPT = 'S', 'R', 'G', 'A'
class lr_0_t:
    def __init__(self, lr_0_assembled:lr_0):
        self.lr_0                           = lr_0_assembled
        self.epsilon_states                 = lr_0_assembled.epsilon_states
        self.epsilon_items                  = lr_0_assembled.epsilon_items
        self.terminals                      = lr_0_assembled.terminals
        self.grammar_rules                  = lr_0_assembled.grammar_rules
        self.states                         = lr_0_assembled.states
        self.reveresed_renamed_states       = lr_0_assembled.reveresed_renamed_states
        self.items                          = lr_0_assembled.items
        self.accept_state                   = lr_0_assembled.accept_state
        self.leaf_states                    = lr_0_assembled.leaf_states
        self.index_to_states                = {index:k for index,k in zip(range(len(self.states.keys())), self.states.keys())}
        self.states_to_index                = {k:index for index,k in self.index_to_states.items()}
        self.start_production               = lr_0_assembled.start_production
        self.lr_0_parsing_table             = None
        self.firsts_table                   = dict()
        self.follow_table                   = dict()
        self.first_of_current               = None
        self.follow_pending_stack           = list()
        self.current                        = None
        self.lr_0_stack                     = list()
        self.lr_0_grammar_rules             = dict()
        self.reverse_lr_0_grammar_rules     = dict()
        self.ast_head                       = None
        self.index_grammar_rules()
        self.construct_lr_0_table()
    
    def unit_test(self, follow_filename, first_file):
        follow_file = open(follow_filename)
        first_file  = open(first_file)
        follow_solutions = safe_load(follow_file)
        first_solutions  = safe_load(first_file)
        follow_file.close()
        first_file.close
        if (follow_solutions == self.follow_table):
            print("PASS FOLLOW")
        else:
            for k,v in self.follow_table.items():
                print(k,v)
            print("FOLLOW SOLUTIONS")
            for k,v in follow_solutions.items():
                print(k,v)
        if (first_solutions == self.firsts_table):
            print("PASS FIRST")
        else:
            for k,v in self.firsts_table.items():
                print(k,v)
            print("FIRST SOLUTIONS")
            for k,v in first_solutions.items():
                print(k,v)

    def index_grammar_rules(self):
        index = 0
        for lhs, rhs_list in self.grammar_rules.items():
            for rhs in rhs_list:
                current_gr = tuple([lhs]+rhs)
                self.lr_0_grammar_rules[index] = current_gr
                self.reverse_lr_0_grammar_rules[current_gr] = index
                index += 1
    
    def firsts(self):
        for lhs in self.grammar_rules.keys():
            self.calculate_feasable_first(lhs)
        pending_firsts = set(self.grammar_rules.keys()) - set(self.firsts_table.keys())
        for lhs in pending_firsts:
            first = self.calculate_firsts(lhs)
    
    def calculate_firsts(self, lhs):
        # lhs is a non terminal
        if self.firsts_table.get(lhs):
            return self.firsts_table[lhs]
        ft = self.firsts_table
        rhs_list = deepcopy(self.grammar_rules[lhs])
        first = set()
        for rhs in rhs_list:
            rhs_element_index = 0
            self.detect_left_recursion(lhs, rhs_list[0])
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
    
    def detect_left_recursion(self, lhs, first_rhs):
        if (lhs == first_rhs):
            parser_std_error(f'left recursion detected at {lhs}')
    
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
                self.calculate_follow(lhs, rhs)
        self.make_pending_follows()
    
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
            
    def calculate_follow(self, lhs, rhs):
        ft = self.follow_table
        for B_i in range(len(rhs)):
            B, beta = rhs[B_i], None
            if is_nonterminal(B):
                if (B_i + 1) < len(rhs):
                    beta = rhs[(B_i + 1):]
                    firsts = self.get_first(beta)
                    self.follow_table[B] |= firsts - {None}
                    if None in firsts:
                        if lhs != B: self.follow_pending_stack.append((B, lhs))
                else:
                    if lhs != B: self.follow_pending_stack.append((B, lhs))
            else:
                continue
    
    def get_first(self, beta):
        first, index = set(), 0
        for b in beta:
            f = set()
            if is_nonterminal(b):
                f |= self.firsts_table[b]
            else:
                first.add(b)
                break
            if None not in f:
                first |= f
                break
            if index != (len(beta) - 1):
                first |= f - {None}
            else:
                first |= f
            index += 1
        return first
            
    def make_pending_follows(self):
        for pf in self.follow_pending_stack:
            self.follow_table[pf[0]] |= deepcopy(self.follow_table[pf[1]])

    def construct_lr_0_table(self):
        self.lr_0_parsing_table = {k:{} for k in self.index_to_states.keys()}
        for state, transitions in self.states.items():
            for transition_token, next_state in transitions.items():
                if is_nonterminal(transition_token): # nonterminal, therefore goto
                    self.lr_0_parsing_table[state][transition_token] = tuple([GOTO, next_state])
                else: # terminal, therefore action
                    self.lr_0_parsing_table[state][transition_token] = tuple([SHIFT, next_state])
        for leaf_state in self.leaf_states:
            state = self.reveresed_renamed_states[leaf_state]
            for item in state:
                reduce_production = list(self.items[item])
                reduce_production.remove('•')
                reduce_production_index = self.reverse_lr_0_grammar_rules[tuple(reduce_production)]
                for p in self.terminals:
                    if not self.lr_0_parsing_table[leaf_state].get(p):
                        self.lr_0_parsing_table[leaf_state][p] = tuple([REDUCE, reduce_production_index])
                    else:
                        parser_std_error(f'in lr_0_t parsing table, position already occupied')
        for state, item in self.epsilon_states.items():
            reduce_production = list(self.items[item])
            reduce_production.remove('•')
            reduce_production.append(None)
            reduce_production_index = self.reverse_lr_0_grammar_rules[tuple(reduce_production)]
            if not self.lr_0_parsing_table[state].get(None):
                self.lr_0_parsing_table[state][None] = tuple([REDUCE, reduce_production_index])
            else:
                parser_std_error(f'in lr_0_t epsilon parsing state, position already occupied')
        
PARENT, CHILDREN, PTR = 0, 1, 1
class parser:
    def __init__(self, assembled_lr_0_table:lr_0_t, scanner_instance:scanner):
        self.start_production   = assembled_lr_0_table.start_production
        self.e_reduce           = None
        self.lr_0_parsing_table = assembled_lr_0_table.lr_0_parsing_table
        self.lr_0_grammar_rules = assembled_lr_0_table.lr_0_grammar_rules
        self.ast                = dict()
        self.state_stack        = list()
        self.productions_stack  = list()
        self.lexed_tokens       = scanner_instance.linked_list_of_tokens
        self.production_label   = num_label_maker()
        self.tree_repr          = str()
        self.parse()
    
    def debug(self, parser_debug_file='./decaf_debug/parser_debug.txt'):
        STAGE = 'PARSING'
        intended_print(f'{"-"*10}PASSED {STAGE} STAGE{"-"*10}')
        intended_print(f'\tAST IN: {parser_debug_file}')
        with open(parser_debug_file, mode='w+') as file:
            file.write(str(self))
            file.close()
    
    def __repr__(self) -> str:
        self.str_tree([self.ast_head])
        return self.tree_repr
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def str_tree(self, list_node_i, tab=0, f=True):
        for node_index in list_node_i:
            prod, edge = self.ast[node_index]
            if edge == None:
                self.tree_repr += '\t'*tab+f'level={tab} '+prod+f' ({node_index})'+'\n'
            elif is_terminal(prod):
                t = self.ast[edge][PARENT]
                self.tree_repr += '\t'*tab+f'level={tab} '+prod+'='+t+f' ({node_index})'+'\n'
            else:
                self.tree_repr += '\t'*tab+f'level={tab} '+prod+f' ({node_index})'+'\n'
                self.str_tree(edge, tab+1, False)
    
    def print_tree(self, list_node_i, tab=0, f=True):
        for node_index in list_node_i:
            prod, edge = self.ast[node_index]
            if is_nonterminal(prod) and (edge == None):
                intended_print('\t'*tab+f'level={tab} '+prod+'='+str(edge)+f' ({node_index})')
            elif edge == None: # terminal such as ('{', None)
                intended_print('\t'*tab+f'level={tab} '+prod+f' ({node_index})')
            elif is_terminal(prod): # terminal 
                t = self.ast[edge][PARENT]
                intended_print('\t'*tab+f'level={tab} '+prod+'='+t+f' ({node_index})')
            else:
                intended_print('\t'*tab+f'level={tab} '+prod+f' ({node_index})')
                self.print_tree(edge, tab+1, False)

    def error(self, symbol, val):
        parser_std_error(f'no operation for the symbol {symbol} \'{val}\'')
    
    def reduce(self, rule):
        prod = self.lr_0_grammar_rules[rule]
        lhs = prod[LHS]
        rhs = prod[RHS:]
        current_node_id = next(self.production_label)
        if rhs[0] == None:
            self.productions_stack.append((lhs, current_node_id))
            self.ast[current_node_id] = tuple([lhs, None])
        else:
            self.ast[current_node_id] = tuple([lhs, list()])
            for x in range(len(rhs)):
                ptr = self.productions_stack.pop()[PTR]
                if ptr != None: self.ast[current_node_id][CHILDREN].insert(0, ptr)
                self.state_stack.pop()
            self.productions_stack.append((lhs, current_node_id))
            if (len(self.productions_stack) == 1) and (self.productions_stack[-1][PARENT] == self.start_production):
                return
        self.goto(lhs)
    
    def goto(self, non_terminal):
        if is_nonterminal(non_terminal):
            current_state          = self.state_stack[-1]
            operation, next_state  = self.lr_0_parsing_table[current_state][non_terminal]
            if (operation == GOTO): 
                self.state_stack.append(next_state)
                pass
            else: 
                parser_std_error(f'in goto function: called goto function while not applicable.')
        else:
            parser_std_error(f'terminal \'{non_terminal}\' called on goto.')

    def shift(self, next_state, element):
        ss, ps, pt = self.state_stack, self.productions_stack, self.ast
        self.state_stack.append(next_state)
        tree_element_index = next(self.production_label)
        t, v = element
        if (t == None):
            self.ast[tree_element_index] = (v, None)
            self.productions_stack.append((v, tree_element_index))
        else:
            self.ast[tree_element_index] = (v, None)
            element = (t, tree_element_index)
            percentage_element = next(self.production_label)
            self.ast[percentage_element] = (t, tree_element_index)
            self.productions_stack.append((t, percentage_element))
    
    def parse(self):
        self.state_stack.append(0)
        index = 0
        lt = self.lexed_tokens
        while True:
            if (len(self.productions_stack) == 1) and (self.productions_stack[-1][PARENT] == self.start_production):
                self.ast_head = self.productions_stack[-1][CHILDREN]
                break
            token, value = self.lexed_tokens[index]
            if token == None: token = value
            operation = param = None
            # if it exists
            top = self.state_stack[-1]
            s = self.lr_0_parsing_table[top]
            if self.lr_0_parsing_table[top].get(token):
                operation, param = self.lr_0_parsing_table[top][token]
            elif self.lr_0_parsing_table[top].get(None):
                operation, param = self.lr_0_parsing_table[top][None]
            else:
                intended_print(self.productions_stack, '\n')
                intended_print(s)
                self.error(token, value)
            # operation found
            if  operation == SHIFT:
                self.shift(param, self.lexed_tokens[index])
                if (index + 1) < len(self.lexed_tokens):
                    index += 1
            elif operation == REDUCE:
                self.reduce(param)
            else:
                self.goto(self.productions_stack[-1][PARENT])


