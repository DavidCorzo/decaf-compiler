from os import error
from string import ascii_uppercase
from typing import Iterable, OrderedDict
from yaml import safe_load
import pickle
import sys

intended_print = print
intended_exit = exit

def scanning_std_error(str):
    intended_print(f'Scanning error: {str}.')
    intended_print(f'In method {sys._getframe(1).f_code.co_name}.')
    intended_exit(-1)


def add_edge(states, state, key, value):
    if (key == None):
        if (states[state].get(None) == None):
            states[state].update({key : set([value])})
        else:
            states[state][key].add(value)
    else:
        states[state].update({key : value})

def num_label_maker() -> int:
    num = 0
    while True:
        yield num
        num += 1

def letter_label_maker() -> int:
    letter_index = 0
    num = 0
    while True:
        letter_index %= len(ascii_uppercase)
        yield f"{ascii_uppercase[letter_index]}{num}"
        letter_index += 1
        num += 1

# global, gives unique name to the states in the nfa and dfa.
nfa_label_gen = num_label_maker()
dfa_label_gen = letter_label_maker()

class enfa:
    def __init__(self, start_state = None, final_state = None):
        if start_state == None:
            self.start_state:int = next(nfa_label_gen)
        else: 
            self.start_state:int = start_state

        if final_state == None:
            self.final_state:int = next(nfa_label_gen)
        else:
            self.final_state:int = final_state
    
    def __repr__(self) -> str:
        return f"start={self.start_state} final={self.final_state}"

    def __str__(self) -> str:
        return f"start={self.start_state} final={self.final_state}"

class dfa:
    # don't declare sets as default cuz python things it is a shared variable.
    def __init__(self, start_state = None, final_state = None):
        self.start_state : int = start_state
        if not final_state:
            self.final_states:  Iterable[int] = set()
        else: 
            self.final_states:  Iterable[int] = final_state
    
    def __repr__(self) -> str:
        return f"dfa: start={self.start_state} end={self.final_states}"

    def __str__(self) -> str:
        return f"dfa: start={self.start_state} end={self.final_states}"

class NFA:
    def __init__(self, infix:str):
        self.states = dict()
        self.infix              :str            = infix
        self.postfix            :str            = None
        self.nfa_stack_frames   :Iterable[enfa] = [] 
        self.last_op_stack      :Iterable[str]  = []
        self.nfa                :enfa           = None
        self.input_alphabet     :str            = set()
        

    def infix_to_postfix(self, infix) -> str:
        postfix = ""
        stack   = []
        precedence = { # don't use 0, confuses the if's.
            '|': 1, '·': 2, '*': 3, '+': 4, '?': 5
        }
        i = 0
        while (i < len(infix)):
            char = infix[i]
            if char == '(': 
                stack.append(char)
            elif char == ')':
                while (stack[-1] != '('):
                    postfix += stack.pop()
                stack.pop()
            elif char == '\\':
                postfix += char
                i += 1
                postfix += infix[i]

            elif char in precedence.keys():
                while ( (len(stack) != 0) and  (precedence.get(char, 0) <= precedence.get(stack[-1], 0))):
                    postfix += stack.pop()
                stack.append(char)
            else:
                postfix += char
            i += 1
        
        while len(stack) != 0:
            postfix += stack.pop()
        ########################## POSTFIX STRING GENERATION #########################################
        return postfix
    
    def regex_or(self, push_to_op_stack=True) -> None:
        # OR a|b
        # pop the last two nfas.
        if ( len(self.last_op_stack) >= 2 ):
            # the last operation was an or then it is a chained or.
            if ( (self.last_op_stack[-1] == 'c') and (self.last_op_stack[-2] == '|') ): 
                character_nfa: enfa = self.nfa_stack_frames.pop() # pop the character nfa
                or_nfa: enfa        = self.nfa_stack_frames.pop() # pop the or nfa
                ## self.states[or_nfa.start_state][None] = character_nfa.start_state
                ## self.states[character_nfa.final_state][None] = or_nfa.final_state
                add_edge(self.states, or_nfa.start_state, None, character_nfa.start_state)
                add_edge(self.states, character_nfa.final_state, None, or_nfa.final_state)
                self.nfa_stack_frames.append(or_nfa)
                if (push_to_op_stack): self.last_op_stack.append('|') 
                return
        # If it is not a chained or operation then create or nfa as regularly
        nfa2: enfa = self.nfa_stack_frames.pop()
        nfa1: enfa = self.nfa_stack_frames.pop()
        # create a new initial and final state
        new_nfa = enfa()
        self.states[new_nfa.start_state] = {} ## dictlist() # creating states in dict
        self.states[new_nfa.final_state] = {} ## dictlist() # creating states in dict
        # adding epsilons from the new accepting state to the new accepting state.
        add_edge(self.states, new_nfa.start_state, None, nfa1.start_state)
        add_edge(self.states, new_nfa.start_state, None, nfa2.start_state)
        ## self.states[new_nfa.start_state][None] = nfa1.start_state # creating edge through epsilon
        ## self.states[new_nfa.start_state][None] = nfa2.start_state # creating edge through epsilon
        # adding epsilons from the old ending states to the new end state.
        add_edge(self.states, nfa1.final_state, None, new_nfa.final_state)
        add_edge(self.states, nfa2.final_state, None, new_nfa.final_state)
        ## self.states[nfa1.final_state][None] = new_nfa.final_state # (character nfa 1) -epsilon-> (B)
        ## self.states[nfa2.final_state][None] = new_nfa.final_state # (character nfa 2) -epsilon-> (B)
        # pushing the merged or nfa to the stack frame.
        self.nfa_stack_frames.append(new_nfa)
        # add last op
        if (push_to_op_stack): self.last_op_stack.append('|')
        
    def regex_character(self, char, push_to_op_stack=True) -> None:
        new_nfa = enfa()
        self.states[new_nfa.start_state] = {} ## dictlist() # creating the new keys:{}
        self.states[new_nfa.final_state] = {} ## dictlist() # creating the new keys:{}
        if (char != 'ε'):
            add_edge(self.states, new_nfa.start_state, char, new_nfa.final_state)
            ## self.states[new_nfa.start_state][char] = new_nfa.final_state
        else:
            add_edge(self.states, new_nfa.start_state, None, new_nfa.final_state)
            ## self.states[new_nfa.start_state][None] = new_nfa.final_state
        self.nfa_stack_frames.append(new_nfa)
        if (push_to_op_stack): self.last_op_stack.append('c')

    def regex_concatenation(self, push_to_op_stack=True) -> None:
        # CONCATENATION/UNION EXPRESSION 
        nfa2: enfa = self.nfa_stack_frames.pop()
        nfa1: enfa = self.nfa_stack_frames.pop()
        if ((self.last_op_stack[-1] == 'c')): #  and (self.last_op_stack[-2] == 'c')
            # char, state_f = list(nfa2.start_state.edges.items())[0] # get the char that creates the transition to the end state nfa.
            char, state_f = list(self.states[nfa2.start_state].items())[0]
            add_edge(self.states, nfa1.final_state, char, state_f)
            nfa1.final_state = state_f
            del self.states[nfa2.start_state]
            self.nfa_stack_frames.append(nfa1)
            push_to_op_stack = False
        else:
            # the accepting state of the first nfa will be the starting state of the second nfa
            add_edge(self.states, nfa1.final_state, None, nfa2.start_state)
            ## self.states[nfa1.final_state][None] = nfa2.start_state
            concatenation_nfa = enfa(nfa1.start_state, nfa2.final_state)
            # adding the new nfa of the concatenated string.
            self.nfa_stack_frames.append(concatenation_nfa)
        if (push_to_op_stack): self.last_op_stack.append('·')
        
    def regex_question_mark(self, char, push_to_op_stack=True) -> None:
        # the character nfa is already the [-2] in the stack, the [-1] is epsilon.
        ## self.states[self.nfa_stack_frames[-1].start_state][None] = self.nfa_stack_frames[-1].final_state
        add_edge(self.states, self.nfa_stack_frames[-1].start_state, None, self.nfa_stack_frames[-1].final_state)
        if (push_to_op_stack): self.last_op_stack.append('?')
        
    def regex_kleene(self, push_to_op_stack=True) -> None:
        # poping the previous nfa that we are going to do (nfa)*
        nfa1: enfa = self.nfa_stack_frames.pop()
        # start and final states for the new nfa
        new_nfa = enfa()
        self.states[new_nfa.start_state] = {} ## dictlist()
        self.states[new_nfa.final_state] = {} ## dictlist()
        # adding epsilon to the start of nfa1
        ## self.states[new_nfa.start_state][None] = nfa1.start_state
        add_edge(self.states, new_nfa.start_state, None, nfa1.start_state)
        # adding epsilon to the final state in the case of just epsilon. 
        ## self.states[new_nfa.start_state][None] = new_nfa.final_state
        add_edge(self.states, new_nfa.start_state, None, new_nfa.final_state)
        # adding an edge for repetition to the begining of the already constructed nfa.
        ## self.states[nfa1.final_state][None] = nfa1.start_state
        add_edge(self.states, nfa1.final_state, None, nfa1.start_state)
        # adding to the final state of the constructed nfa an edge to the new final state
        ## self.states[nfa1.final_state][None] = new_nfa.final_state
        add_edge(self.states, nfa1.final_state, None, new_nfa.final_state)
        # creating the kleene star nfa 
        # push to the stack frames.
        self.nfa_stack_frames.append(new_nfa)
        if (push_to_op_stack): self.last_op_stack.append('*')

    def thompson_construction(self) -> None:
        index = 0
        self.postfix = self.infix_to_postfix(self.infix)
        while (index < len(self.postfix)):
            # The sight of an operator means we already have at least one nfa stack frame
            char = self.postfix[index]
            if (char == '?'):
                self.regex_question_mark(char)
            elif (char == '*'):
                self.regex_kleene()
            elif (char == '·'):
                self.regex_concatenation()
            elif (char == '|'):
                self.regex_or(char)
            elif (char == '\\'): 
                index += 1
                char = self.postfix[index]
                if char == 'n': char = '\n'
                elif char == 't': char = '\t'
                self.regex_character(char)
                self.input_alphabet.add(char)
            else:
                self.regex_character(char)
                if (char != 'ε'):
                    self.input_alphabet.add(char)
            index += 1
        # the nfa_stack_frames should be of length 1 at this point, otherwise the regex is missing a concatenation or some other thing.
        if (len(self.nfa_stack_frames) != 1): 
            scanning_std_error(f'nfa_stack_frames has length of {len(self.nfa_stack_frames)}\n\t\'{self.infix}\' is incorrect')
        self.nfa = self.nfa_stack_frames.pop()
        
    # def draw_nfa(self):
    #     # for efficiency just import the function if it is required.
    #     from draw import draw_graph
    #     edges = []
    #     labels = []
    #     for state,char_next_state in self.states.items():
    #         for char, next_state in char_next_state.items():
    #             if (char == None):
    #                 for i in next_state:
    #                     edges.append([state, i])
    #                     labels.append('ε')
    #             else:
    #                 edges.append([state, next_state])
    #                 labels.append(char)
    #     draw_graph(edges, labels)

class DFA:
    def __init__(self, nfa:NFA):
        self.dfa_states = dict()
        self.dfa_states_names = dict()
        self.closure_of_all_states = dict()
        self.states = nfa.states
        self.input_alphabet = nfa.input_alphabet
        self.nfa = nfa.nfa
        self.dfa:dfa = dfa()
        self.current_position:int = None
        self.current_match = False

    def e_closure(self, state) -> set:
        closure_states = set()
        closure_states.add(state)
        if (self.states[state].get(None) == None): # there is no epsilon key.
            return closure_states
        else:
            for edge in self.states[state][None]:
                closure_states |= self.e_closure(edge)
            return closure_states

    def calculate_closure_of_all_states(self):
        for i in self.states.keys():
            self.closure_of_all_states.update({i: self.e_closure(i)})

    def closures(self, set_of_states) -> tuple:
        closure = set()
        for i in set_of_states:
            closure |= self.closure_of_all_states[i]
        return tuple(closure)

    def subset_construction(self, new_dfa_state:tuple):
        # calculate e_closure de el start_state del nfa.
        if new_dfa_state in self.dfa_states.keys():
            return
        ec = set()
        for state in new_dfa_state: # (6,) -> (8,4,5,6)
            ec |= self.closure_of_all_states[state]
        dfa_state = {new_dfa_state: {}}
        for char in self.input_alphabet:
            for state in ec:
                # iterate over the keys and see if char is in the state
                for transition_letter, next_state in self.states[state].items():
                    if (transition_letter == char):
                        if (dfa_state[new_dfa_state].get(char) == None):
                            dfa_state[new_dfa_state].update({char : set()})
                        dfa_state[new_dfa_state][char].add(next_state) # {(6,): {'a': {5,6}}} -> {(6,): {'a': (5,6)}}

        dfa_state[new_dfa_state] = {k:tuple(sorted(v)) for k,v in dfa_state[new_dfa_state].items()}
        self.dfa_states.update(dfa_state)
        if self.nfa.final_state in self.closures(new_dfa_state):
            self.dfa.final_states.add(new_dfa_state)
        for key, value in dfa_state[new_dfa_state].items():
            self.subset_construction(value)

    def dfa_states_prettify(self):
        for state in self.dfa_states.keys():
            self.dfa_states_names.update({state : next(dfa_label_gen)})

        named_states = {self.dfa_states_names[state]:{} for state in self.dfa_states.keys()}

        for state, edge in self.dfa_states.items():
            for char, next_state in edge.items():
                if (char == None):
                    if not named_states[self.dfa_states_names[state]].get(None):
                        named_states[self.dfa_states_names[state]][None] = set()
                    for s in next_state:
                        named_states[self.dfa_states_names[state]].add(self.dfa_states_names[s])
                else:
                    named_states[self.dfa_states_names[state]][char] = self.dfa_states_names[next_state]
        self.dfa_states = named_states

        self.dfa.start_state = self.dfa_states_names[self.dfa.start_state]
        named_final_states = set()
        for state in self.dfa.final_states:
            named_final_states.add(self.dfa_states_names[state])
        self.dfa.final_states = named_final_states

    def turn_to_dfa(self):
        self.calculate_closure_of_all_states()
        self.dfa.start_state = tuple([self.nfa.start_state])
        self.subset_construction(tuple([self.nfa.start_state])) # (6,)
        # self.dfa_states_prettify()
    
    def match(self, string_to_match) -> bool:
        current_state = self.dfa.start_state
        for char in string_to_match:
            if (self.dfa_states[current_state].get(char) != None):
                current_state = self.dfa_states[current_state][char]
            else:
                return False
        if (current_state in self.dfa.final_states):
            return True
        else:
            return False

    # def draw_dfa(self):
    #     # for efficiency just import the function if it is required.
    #     from draw import draw_graph
    #     edges = []
    #     labels = []
    #     for state,char_next_state in self.dfa_states.items():
    #         for char, next_state in char_next_state.items():
    #             if (char == None):
    #                 for i in next_state:
    #                     edges.append([state, i])
    #                     labels.append('ε')
    #             else:
    #                 edges.append([state, next_state])
    #                 labels.append(char)
    #     draw_graph(edges, labels)
    
    def __repr__(self) -> str:
        return f"({self.dfa_states})"

    def __str__(self) -> str:
        return f"({self.dfa_states})"
    
    def consume(self, char) -> bool:
        if (self.current_position == None):
            self.current_position = self.dfa.start_state
        if (self.dfa_states[self.current_position].get(char) == None):
            return False
        else:
            self.current_position = self.dfa_states[self.current_position][char]
            return True
    

class scanner:
    def __init__(self, src_code_filename, token_filename_wo_ext, build, save):
        self.filename = src_code_filename
        self.current_line = 0
        self.current_line_index = 0
        self.file = open(src_code_filename, mode="r", encoding="utf-8")
        self.content = self.file.read()
        self.content_index = 0
        self.line_num = 1
        self.char_num = 1
        self.deterministic_finite_automata = {}
        self.linked_list_of_tokens = []
        self.candidates = []
        self.error = error_msg()
        if build:
            with open((token_filename_wo_ext + '.yaml'), mode="r") as file:
                self.tokens = OrderedDict(safe_load(file))
                file.close()
            self.produce_automata()
            if save:
                save_filename = token_filename_wo_ext + '.pickle'
                self.save_automata(save_filename)
        else:
            try:
                self.load_automata(token_filename_wo_ext + '.pickle')
            except:
                error("Scanning error: loading automata file corrupt or non existant. Provide a token file to produce the automata.")
                exit(-1)
        self.scan()
        self.linked_list_of_tokens.append((None, '$'))
    
    def __del__(self):
        self.file.close()
    
    def debug(self, scan_file='./decaf_debug/scan_debug.txt'):
        STAGE = 'SCANNING'
        intended_print(f'{"-"*10}PASSED {STAGE} STAGE{"-"*10}')
        intended_print(f'\tLINKED LIST OF TOKENS IN {scan_file}')
        with open(scan_file, mode='w+', encoding='utf8') as file:
            for k,v in self.linked_list_of_tokens:
                file.write(f'{k} {v}\n')
            file.close()
    
    def produce_automata(self):
        for token, regex in self.tokens.items():
            nfa1 = NFA(regex)
            nfa1.thompson_construction()
            dfa1 = DFA(nfa1)
            dfa1.turn_to_dfa()
            self.deterministic_finite_automata.update({token: dfa1})
    
    def save_automata(self, fa_name):
        with open(fa_name, mode='wb') as file:
            pickle.dump(self.deterministic_finite_automata, file)
            file.close()
    
    def load_automata(self, fa_name):
        with open(fa_name, mode='rb') as file:
            self.deterministic_finite_automata = pickle.load(file)
            file.close()

    def next_char(self):
        self.content_index += 1
        
    def peek_current(self):
        if self.content_index < len(self.content):
            return self.content[self.content_index]
        else:
            return None
    
    def peek_next(self):
        if ((self.content_index + 1) < len(self.content)):
            return self.content[self.content_index + 1]
        else:
            return None
    
    def recognize(self, buffer):
        for token, determ_fa in self.deterministic_finite_automata.items():
            if (determ_fa.match(buffer)):
                return token
        return None
    
    def append_to_list_of_token(self, match, token):
        if (match != None) and (':None' in match[1:-1]):
            match = None
        self.linked_list_of_tokens.append((match, token))

    def scan(self):
        buffer = ""
        while (self.content_index < len(self.content)):
            char = self.content[self.content_index]
            if char == '#': # comment
                while char != '\n':
                    self.content_index += 1
                    char = self.content[self.content_index]
            if (char in " \n\t"):
                if buffer != '':
                    match_regex = self.recognize(buffer)
                    if (match_regex):
                        self.append_to_list_of_token(match_regex, buffer)
                    else:
                        self.error.no_regex_match(self)
                buffer = ""
                if (char == '\n'):
                    self.line_num += 1
                    self.char_num = 0
            elif char in "(){}[]:;,!":
                if buffer != '':
                    match_regex = self.recognize(buffer)
                    if match_regex: 
                        self.append_to_list_of_token(match_regex, buffer)
                    else: self.error.no_regex_match(self)
                self.append_to_list_of_token(None, char)
                buffer = ''
            elif char in "<>=+-*/%":
                if buffer != '':
                    match_regex = self.recognize(buffer)
                    if match_regex:
                        self.append_to_list_of_token(match_regex, buffer)
                    else:
                        self.error.no_regex_match(self)
                    buffer = ''
                symbol = char
                next_char = self.peek_next()
                if (next_char != None) and (char in '+-='):
                    if next_char in "=<>": 
                        symbol += next_char
                        self.content_index += 1
                match_regex = self.recognize(symbol)
                if (match_regex): 
                    self.append_to_list_of_token(match_regex, symbol)
                else: self.error.no_regex_match(self)
            elif char in "\"\'":
                terminal = char
                buffer += char
                self.content_index += 1
                double_quote_detected = True
                while (self.content_index < len(self.content)):
                    char = self.content[self.content_index]
                    buffer += char
                    if (char == '\\'):
                        self.content_index += 1
                        char = self.content[self.content_index]
                        if (char not in 'nt'):
                            buffer += f'{char}'
                        else:
                            buffer += char
                    elif (char == terminal):
                        double_quote_detected = False
                        break
                    self.content_index += 1
                    self.char_num += 1
                if (double_quote_detected):
                    self.error.unmatching_doublequotes(self)
                match_regex = self.recognize(buffer)
                if (match_regex): self.append_to_list_of_token(match_regex, buffer)
                else: self.error.no_regex_match(self)
                buffer = ''
            else:
                if self.isascii(char):
                    buffer += char
                else:
                    self.error.illegal_character(self)
            self.content_index += 1
            self.char_num += 1
    
    def isascii(self, char):
        return len(char) == len(char.encode())

class error_msg:
    def illegal_character(self, scanner_instance:scanner):
        scanning_std_error(f'illegal_character\n\t\
            ILLEGAL CHARACTER FOUND \'{scanner_instance.content[scanner_instance.content_index]}\'\n\t\
            illegal character found at line {scanner_instance.line_num} column {scanner_instance.char_num}'
        )
    
    def no_regex_match(self, scanner_instance):
        scanning_std_error(f'no_regex_match\n\t\
            NO KEYWORD MATCH FOR \'{scanner_instance.content[scanner_instance.content_index]}\'\n\t\
            No match was found for the above char in line {scanner_instance.line_num} column {scanner_instance.char_num}'
        )

    def unmatching_doublequotes(self, scanner_instance):
        scanning_std_error(f'unmatching_doublequotes\n\t\
            FILE TERMINATED WITHOUT CLOSING STRING \'{scanner_instance.content[scanner_instance.content_index]}\'\n\t\
            No double quote to close, above char in line {scanner_instance.line_num} column {scanner_instance.char_num}'
        )
    
    def unmatching_singlequotes(self, scanner_instance):
        scanning_std_error(f'unmatching_singlequotes\n\t\
            FILE TERMINATED WITHOUT CLOSING CHAR LITERAL \'{scanner_instance.content[scanner_instance.content_index]}\'\n\t\
            "No single quote to close, above char in line {scanner_instance.line_num} column {scanner_instance.char_num}'
        )

