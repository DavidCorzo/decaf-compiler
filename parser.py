from os import error
from yaml import safe_load
from copy import deepcopy
import pickle
from scanner import scanner

def is_nonterminal(string):
    if string == None: return False
    return ((string[0] == '<') and (string[-1] == '>')) # bool(re.match("<(.*)>", string))

def is_terminal(string):
    return not is_nonterminal(string)

def is_terminal_with_value(string):
    return ((string[0] == '%') and (':' in string[1:-1]) and (string[-1] == '%'))

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

LHS, RHS = 0, 1
class lr_0:
    def __init__(self, start_production, productions_filename, build=False, save=False):
        self.lr_0_filename                      = 'lr_0_dfa.pickle'
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
            self.productions_filename           = productions_filename
            self.closure_table                  = dict()
            self.closures_to_states             = dict()
            self.closure_of_current_item        = None
            self.productions_processed          = None
            self.state_label_gen                = num_label_maker()
            self.load_grammar()
            self.closures()
            self.create_states()
            # print_dict(self.items)
        else:
            self.load_lr_0_dfa()
        if save: 
            self.save_lr_0_dfa()
        # print(self)
        # print(self.accept_item)
        # print(self.accept_state)
    
    def load_grammar(self):
        """
        1. Open file and read contents: First it opens the file and imports the contets which are the 
            productions that define the grammar, this is stored in self.grammar and is represented 
            in the form of a dictionary which keys are the left hand sides and who's 
            value is the right hand side. Example: 
                {'<S´>': [['<S>', '$']], '<S>': [['<A>', '<C>', '<B>'], ...}.
        2. Calculate items: Then we grab the newly imported grammar and fabricate the items of all of 
        the productions of the grammar, these will be stored in self.items. 
            - The offset variable is because we don't want to add a '•' after the dollar 
                sign since that is the accept state, the offset stops us from iterating on 
                more time and fabricating the item with the dot as the last element after the dollar.
            - we also are sure to make a copy of the production before adding the dot, otherwise
                python will assume we mean the pointer to the actual grammar rules, and modify that 
                when we want a copy of the rule and then add the dot.
            - items are stored with an index as a key and a tuple representation of the item as 
                a value, an example: {0: ('<S´>', '•', '<S>', '$'), 1: ('<S´>', '<S>', '•', '$'), ...}.
            - the tuple representation's first element is the left hand side and the rest of the 
                elements after the first are the right hand side of the production.
        3. Calculate self.reverse_item: self.reverse_item exactly the same as self.items just that the keys are 
            the tuples and the values are index, example: 
                {('<S´>', '•', '<S>', '$'): 0, ('<S´>', '<S>', '•', '$'): 1, ...}.
            - This is merely just for convenience and efficiency, hashmaps accessing elements are constant time,
                however you want to search by value you need to take linear time, therefore it is better to have a 
                reversed version of the hash map.
        4. Calculate self.closed_rules are a copy of the self.grammar_rules but with all productions having a dot in the 
            beggining of the right hand side. This is handy when calculating the closure since if we have a dot 
            followed by a nonterminal we must add all of the productions of that non terminal with the dot at 
            the beggining, self.closed rules gets as a key the lhs as usual, and the rhs is the list of productions 
            with the added dot in the first position. The lhs is the first element of the tuple, the rhs is all 
            remaining elements after the first. Example: 
                {'<S´>': [('<S´>', '•', '<S>', '$')], '<S>': [('<S>', '•', '<A>', '<C>', '<B>'), ...}
        5. Calculate self.closed_indexes is exactly the same as the self.closed_rules only that instead of actually having the 
            rules with the dot we have the index of the items we calculated in step 2. Recall the items had an index in 
            the dictionary/hashmap we are using that index since it is just a single number not a tuple, thus occupying 
            less space, because a DFA of productions for a complex grammar can easily occupy millions of states, better
            be efficient with how much the states take in memory.
        """
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
        """
        In this function we calculate the closure of all the items indiscriminantly.
        This is done to avoid unnecessary recursion of calculated items, instead we 
        just access the closure of that specific item in the dictionary of already 
        calculated items.
        1. self.closure_of_current_item is the current state we are manufacturing, it is a set that 
            stores the current item's indexes. Example: {0, 1, 2, 3} these are item indexes.
        2. self.productions_processed keeps track of the productions that we have already 
            processed when we are recursively calculating the closure in the self.get_closure_of_an_item.
            We always start with registering the start production since we have already processed that one 
            in it's entirety because it is the starting production.
        3. call the self.get_closure_of_an_item function, this function will help us make states later on, 
            since states are nothing more than the closure of various items.
            - This method makes use of self.closure_of_current_item to add the what the self.get_closure_of_an_item finds recursively.
                the method does not return anything it calls itself recursively but returns data to the self.closure_of_current_item 
                attribute, and adds the productions it has processed to the self.productions_processed.
        4. We add the calculated closure to the self.closure_table dictionary which is the index of the item as a 
            key and its closure as a value. Example: {0: {1,2,3,4}, ...} item 0 has closure {1,2,3,4}
        5. Repeat this for all the items.
        """
        for item_index in self.items.keys():
            self.closure_of_current_item = set()
            self.productions_processed = set([self.start_production])
            self.get_closure_of_an_item(set([item_index]))
            self.closure_table[item_index] = self.closure_of_current_item

    def get_closure_of_an_item(self, set_of_indexes):
        """
        This method calculates the closure of a single item. 
        1. First it takes a set of indexes (indexes that represent items in the self.items dictionary).
            These indexes are always part of the closure of the item, therefore the first thing we do is 
            add it to the self.closure_of_current_item attribute of which this method has global access.
        2. The set of indexes of the items are useless as indexes, we need the actual items, so we get 
            the items by using the self.items dictionary and accessing via the key the actual item pointed to.
        3. Pending productions: this is a set that stores the non terminals that are pending to process recursively
            whenever we find an item that has a '•' and then a non terminal, we must add all the rhs's of that nonterminal
            with a '•' at the begining, we will do this later so it will be left pending.
        4. Base case, if the we have no pending productions we must add, we are done with the recursion and return, 
            therefore terminating the recursion.
        5. If we are not done, i.e. we have not broken the recursion with the base case we must process the pending 
            productions, with a for loop we iterate through the set of pending lhs's to be processed. There is a chance 
            we have already processed that lhs in an earlier recursive call so we must check for each lhs pending that we 
            have not added it, thus saving unnecessary recursion, if it has not been added to self.productions added then 
            we must calculate it, we already have the all the rules with the dot at the begining stored in self.closed_indexes
            we just go and retrieve them and add them (the indexes) to the pending_items set which holds the items derived from 
            the pending_productions set, the last thing we do is register the production as already processed to know not to 
            process it again in future recursive calls.
        6. Recursive call, we make the recursive call, the set_of_items in this one is the pending_items set, we do this to check 
            if any other item we added has a '•' followed by a non terminal that needs closure.
        """
        
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
        """
        This function creates all the states.
        1. self.create_state(set([0])) creates all the states recursively upon a single call by simply providing 
            the kernel start state (the starting production with a '•' as first element of rhs).
        2. The states and the transitions have now been created recursively, example:
            {
                State items: (0, 2, 6, 10, 13, 16, 19, 21, 23, 25): 
                state transitons :{'<B>': (11, 17), 'd': (14,), 'g': (20,), 'h': (24,), '<A>': (3,), None: (22, 26), '<C>': (7,), '<S>': (1,)}
                ...
            }
        3. The keys of the dictionary are already states, which are calculated with the closure of a starting 
            set of items, but the transitions are unclosed sets of items, which means they are just added, they
            are not states but instead are the items that if closure is performed on they become states.
            In the next for loop we replace the unclosed items for the actual states. Example:
            {
                (0, 2, 6, 10, 13, 16, 19, 21, 23, 25): 
                {'<C>': (7,), '<B>': (11, 17), 'h': (24,), '<A>': (3,), None: (22, 26), 'd': (14,), '<S>': (1,), 'g': (20,)}
                ...
            }
            - Bear in mind that sometimes the unclosed state have a closure of just themselves, therefore the unclosed states 
            are already states, but we do not know this until we replace them for the closed states.
        """
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
                else: print("second accept state present")
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
                print("REDUCE REDUCE BY TWO PRODUCTIONS ON EPSILON")
                exit(-1)
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
                # if (after_dot != '$'):
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
        """
        This function simply takes in a tuple item, separates the lhs from the rhs and to the rhs
        advances the dot at once.
        """
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
            to_save.pop('state_label_gen')
            pickle.dump(to_save, file)
            file.close()
    

SHIFT, REDUCE, GOTO, ACCEPT = 'S', 'R', 'G', 'A'
class slr:
    def __init__(self, lr_0_assembled:lr_0):
        self.lr_0                       = lr_0_assembled
        self.epsilon_states             = lr_0_assembled.epsilon_states
        self.epsilon_items              = lr_0_assembled.epsilon_items
        self.terminals                  = lr_0_assembled.terminals
        self.grammar_rules              = lr_0_assembled.grammar_rules
        self.states                     = lr_0_assembled.states
        self.reveresed_renamed_states   = lr_0_assembled.reveresed_renamed_states
        self.items                      = lr_0_assembled.items
        self.accept_state               = lr_0_assembled.accept_state
        self.leaf_states                = lr_0_assembled.leaf_states
        self.index_to_states            = {index:k for index,k in zip(range(len(self.states.keys())), self.states.keys())}
        self.states_to_index            = {k:index for index,k in self.index_to_states.items()}
        self.start_production           = lr_0_assembled.start_production
        self.slr_parsing_table          = None
        self.firsts_table               = dict()
        self.follow_table               = dict()
        self.first_of_current           = None
        self.follow_pending_stack       = list()
        self.current                    = None
        self.slr_stack                  = list()
        self.slr_grammar_rules          = dict()
        self.reverse_slr_grammar_rules  = dict()
        self.productions_tree_head      = None
        self.index_grammar_rules()
        # self.firsts()
        # self.follows()
        # self.unit_test('grammars/example_follow.yaml', 'grammars/example_first.yaml')
        self.construct_slr()
    
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
                self.slr_grammar_rules[index] = current_gr
                self.reverse_slr_grammar_rules[current_gr] = index
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
            print(f"LEFT RECURSION DETECTED AT {lhs}")
            exit(-1)
    
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

    def construct_slr(self):
        self.slr_parsing_table = {k:{} for k in self.index_to_states.keys()}
        for state, transitions in self.states.items():
            for transition_token, next_state in transitions.items():
                if is_nonterminal(transition_token): # nonterminal, therefore goto
                    self.slr_parsing_table[state][transition_token] = tuple([GOTO, next_state])
                else: # terminal, therefore action
                    self.slr_parsing_table[state][transition_token] = tuple([SHIFT, next_state])
        for leaf_state in self.leaf_states:
            state = self.reveresed_renamed_states[leaf_state]
            for item in state:
                reduce_production = list(self.items[item])
                reduce_production.remove('•')
                reduce_production_index = self.reverse_slr_grammar_rules[tuple(reduce_production)]
                for p in self.terminals:
                    if not self.slr_parsing_table[leaf_state].get(p):
                        self.slr_parsing_table[leaf_state][p] = tuple([REDUCE, reduce_production_index])
                    else:
                        print("ERROR IN SLR PARSING TABLE, POSITION ALREADY OCCUPIED")
                        exit(-1)
        for state, item in self.epsilon_states.items():
            reduce_production = list(self.items[item])
            reduce_production.remove('•')
            reduce_production.append(None)
            reduce_production_index = self.reverse_slr_grammar_rules[tuple(reduce_production)]
            if not self.slr_parsing_table[state].get(None):
                self.slr_parsing_table[state][None] = tuple([REDUCE, reduce_production_index])
            else:
                print("ERROR IN SLR EPSILON PARSING STATE, POSITION ALREADY OCCUPIED")
                exit(-1)
        
PARENT, CHILDREN, PTR = 0, 1, 1
class parser:
    def __init__(self, slr_table:slr, lexed_tokens):
        self.start_production   = slr_table.start_production
        self.e_reduce           = None
        self.slr_parsing_table  = slr_table.slr_parsing_table
        self.slr_grammar_rules  = slr_table.slr_grammar_rules
        self.productions_tree   = dict()
        self.state_stack        = list()
        self.productions_stack  = list()
        self.lexed_tokens       = lexed_tokens
        self.production_label   = num_label_maker()
        self.parse()

    def error(self, symbol):
        print(f"ERROR: NO OPERATION FOR THE SYMBOL {symbol}")
        error(-1)
        exit(-1)
    
    def reduce(self, rule):
        st, ps, pt = self.state_stack, self.productions_stack, self.productions_tree
        prod = self.slr_grammar_rules[rule]
        lhs = prod[LHS]
        rhs = prod[RHS:]
        if rhs[0] == None:
            self.productions_stack.append((lhs, None))
        else:
            current_node_id = next(self.production_label)
            self.productions_tree[current_node_id] = tuple([lhs, list()])
            cn = self.productions_tree[current_node_id]
            for x in range(len(rhs)):
                ptr = self.productions_stack.pop()[PTR]
                if ptr: self.productions_tree[current_node_id][CHILDREN].insert(0, ptr)
                self.state_stack.pop()
            self.productions_stack.append((lhs, current_node_id))
            if (len(self.productions_stack) == 1) and (self.productions_stack[-1][PARENT] == self.start_production):
                return
        self.goto(lhs)
    
    def goto(self, non_terminal):
        ss, ps, pt = self.state_stack, self.productions_stack, self.productions_tree
        if is_nonterminal(non_terminal):
            current_state   = self.state_stack[-1]
            operation, next_state  = self.slr_parsing_table[current_state][non_terminal]
            if (operation == GOTO): 
                self.state_stack.append(next_state)
                pass
            else: 
                print("GOTO not applicable")
                exit(-1)
        else:
            print("ERROR: TERMINAL CALLED ON GOTO")
            exit(-1)

    def shift(self, next_state, element):
        ss, ps, pt = self.state_stack, self.productions_stack, self.productions_tree
        self.state_stack.append(next_state)
        tree_element_index = next(self.production_label)
        t, v = element
        if (t == None):
            self.productions_tree[tree_element_index] = (v, None)
            self.productions_stack.append((v, tree_element_index))
        else:
            self.productions_tree[tree_element_index] = (v, None)
            element = (t, tree_element_index)
            percentage_element = next(self.production_label)
            self.productions_tree[percentage_element] = (t, tree_element_index)
            self.productions_stack.append((t, percentage_element))
    
    def parse(self):
        self.state_stack.append(0)
        index = 0
        lt = self.lexed_tokens
        while True:
            if (len(self.productions_stack) == 1) and (self.productions_stack[-1][PARENT] == self.start_production):
                self.productions_tree_head = self.productions_stack[-1][CHILDREN]
                break
            token, value = self.lexed_tokens[index]
            if token == None: token = value
            operation = param = None
            # if it exists
            top = self.state_stack[-1]
            s = self.slr_parsing_table[top]
            if self.slr_parsing_table[top].get(token):
                operation, param = self.slr_parsing_table[top][token]
            elif self.slr_parsing_table[top].get(None):
                operation, param = self.slr_parsing_table[top][None]
            else:
                self.error(token)
            # operation found
            if  operation == SHIFT:
                self.shift(param, self.lexed_tokens[index])
                if (index + 1) < len(self.lexed_tokens):
                    index += 1
            elif operation == REDUCE:
                self.reduce(param)
            else:
                self.goto(self.productions_stack[-1][PARENT])
            print(self.productions_stack)
            pass
        print(self.productions_tree)


code = scanner("./src_code.txt", "./tokens.yaml")
code.produce_automata()
code.save_automata("tokens.pickle")
code.scan()
code.linked_list_of_tokens.append((None, '$'))

# print(code.linked_list_of_tokens)
l = lr_0('<program>', 'productions.yaml', build=1, save=1)
s = slr(l)
p = parser(s, code.linked_list_of_tokens)
