from string import ascii_lowercase, ascii_uppercase
from typing import Iterable
import argparse
import yaml
# from draw import draw_graph
from dataclasses import dataclass

DIGITS = "0123456789"
SIGMA = ascii_lowercase + ascii_uppercase + DIGITS + "()+-*<>/%=!\"'}{"
DEBUG = True

def command_line_interpreter() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument('--o', help="rename file with -o")
    parser.add_argument('--target', help="-target <stage>", choices=["scan", "parse", "ast", "irt", "codegen"])
    parser.add_argument('--debug', help="-debug <stage>")
    args = parser.parse_args()
    return args.__dict__

class dictlist(dict):
    def __setitem__(self, key, value):
        if (key == None):
            if (self.get(None) == None):
                self.update({key: set([value])})
            else: 
                self[key].add(value)
        else:
            self.update({key:value})


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
    """
    This class takes in a regular expression and returns a epsilon-nfa.
    """
    def __init__(self, infix:str):
        self.states = dict()
        self.infix              :str            = infix
        self.postfix            :str            = None
        self.nfa_stack_frames   :Iterable[enfa] = [] 
        self.last_op_stack      :Iterable[str]  = []
        self.nfa                :enfa           = None
        self.input_alphabet     :str            = set()
        

    def infix_to_postfix(self, infix) -> str:
        """
        This method uses the class attribute self.infix which is a regular expression in the infix form.
        It then proceeds to make a regular expression that is in the postfix form.
        Example: a+b+(c+d) -> cd+a+b+
        """
        postfix = ""
        stack   = []
        precedence = { # don't use 0, confuses the if's.
            '|': 1, '·': 2, '*': 3, '+': 4, '?': 5
        }
        ########################## EXPANDING RANGES #########################################
        new_infix = ""
        i = 0
        while (i < len(infix)):
            if (infix[i] == "["):
                ii = 0
                i += 1
                char_inside = ""
                while (infix[i] != ']'):
                    char_inside += infix[i]
                    if ((infix[i] == '-') and (ii != 0)):
                        char_inside = char_inside[:-2]
                        low_lim = infix[i-1]
                        high_lim = infix[i+1]
                        if ((low_lim in DIGITS) and (high_lim in DIGITS)):
                            for r in range(int(low_lim), int(high_lim) + 1):
                                char_inside += str(r)
                        elif ((low_lim in ascii_lowercase) and (high_lim in ascii_lowercase)):
                            for r in range(ord(low_lim), ord(high_lim) + 1):
                                char_inside += chr(r)
                        elif ((low_lim in ascii_uppercase) and (high_lim in ascii_uppercase)):
                            for r in range(ord(low_lim), ord(high_lim) + 1):
                                char_inside += chr(r)
                        else:
                            print("Error in range of regular expression.")
                            exit(-1)
                        i += 1
                    ii += 1
                    i  += 1
                new_infix += f"({'|'.join([x for x in char_inside])})"
            else:
                new_infix += infix[i]
            i += 1
        ########################## EXPANDING RANGES #########################################
        ########################## POSTFIX STRING GENERATION #########################################
        infix = new_infix
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
            if ( (self.last_op_stack[-2] == '|') and (self.last_op_stack[-1] == 'c') ): 
                character_nfa: enfa = self.nfa_stack_frames.pop() # pop the character nfa
                or_nfa: enfa        = self.nfa_stack_frames.pop() # pop the or nfa
                self.states[or_nfa.start_state][None] = character_nfa.start_state
                self.states[character_nfa.final_state][None] = or_nfa.final_state
                self.nfa_stack_frames.append(or_nfa)
                if (push_to_op_stack): self.last_op_stack.append('|') 
                return
        # If it is not a chained or operation then create or nfa as regularly
        nfa2: enfa = self.nfa_stack_frames.pop()
        nfa1: enfa = self.nfa_stack_frames.pop()
        # create a new initial and final state
        new_nfa = enfa()
        self.states[new_nfa.start_state] = dictlist() # creating states in dict
        self.states[new_nfa.final_state] = dictlist() # creating states in dict
        # adding epsilons from the new accepting state to the new accepting state.
        self.states[new_nfa.start_state][None] = nfa1.start_state # creating edge through epsilon
        self.states[new_nfa.start_state][None] = nfa2.start_state # creating edge through epsilon
        # start_state.edges[None] = nfa1.start_state # (A) -epsilon-> (character nfa 1)
        # start_state.edges[None] = nfa2.start_state # (A) -epsilon-> (character nfa 2)
        # adding epsilons from the old ending states to the new end state.
        self.states[nfa1.final_state][None] = new_nfa.final_state # (character nfa 1) -epsilon-> (B)
        self.states[nfa2.final_state][None] = new_nfa.final_state # (character nfa 2) -epsilon-> (B)
        # pushing the merged or nfa to the stack frame.
        self.nfa_stack_frames.append(new_nfa)
        # add last op
        if (push_to_op_stack): self.last_op_stack.append('|')
        
    def regex_character(self, char, push_to_op_stack=True) -> None:
        new_nfa = enfa()
        self.states[new_nfa.start_state] = dictlist() # creating the new keys:{}
        self.states[new_nfa.final_state] = dictlist() # creating the new keys:{}
        if (char != 'ε'):
            self.states[new_nfa.start_state][char] = new_nfa.final_state
        else:
            self.states[new_nfa.start_state][None] = new_nfa.final_state
        self.nfa_stack_frames.append(new_nfa)
        if (push_to_op_stack): self.last_op_stack.append('c')

    def regex_concatenation(self, push_to_op_stack=True) -> None:
        # CONCATENATION/UNION EXPRESSION 
        nfa2: enfa = self.nfa_stack_frames.pop()
        nfa1: enfa = self.nfa_stack_frames.pop()
        if ((self.last_op_stack[-1] == 'c')): #  and (self.last_op_stack[-2] == 'c')
            # char, state_f = list(nfa2.start_state.edges.items())[0] # get the char that creates the transition to the end state nfa.
            char, state_f = list(self.states[nfa2.start_state].items())[0]
            self.states[nfa1.final_state][char] = state_f
            nfa1.final_state = state_f
            del self.states[nfa2.start_state]
            self.nfa_stack_frames.append(nfa1)
            push_to_op_stack = False
        else:
            # the accepting state of the first nfa will be the starting state of the second nfa
            self.states[nfa1.final_state][None] = nfa2.start_state
            concatenation_nfa = enfa(nfa1.start_state, nfa2.final_state)
            # adding the new nfa of the concatenated string.
            self.nfa_stack_frames.append(concatenation_nfa)
        if (push_to_op_stack): self.last_op_stack.append('·')
        
    def regex_question_mark(self, char, push_to_op_stack=True) -> None:
        self.regex_character('ε', False) # create epsilon constrution without registering it as a char operation.
        # the character nfa is already the [-2] in the stack, the [-1] is epsilon.
        self.regex_or(False) # Create an or construction without registering it as a or operation.
        if (push_to_op_stack): self.last_op_stack.append('?')
        
    def regex_kleene(self, push_to_op_stack=True) -> None:
        # poping the previous nfa that we are going to do (nfa)*
        nfa1: enfa = self.nfa_stack_frames.pop()
        # start and final states for the new nfa
        new_nfa = enfa()
        self.states[new_nfa.start_state] = dictlist()
        self.states[new_nfa.final_state] = dictlist()
        # adding epsilon to the start of nfa1
        self.states[new_nfa.start_state][None] = nfa1.start_state
        # adding epsilon to the final state in the case of just epsilon. 
        self.states[new_nfa.start_state][None] = new_nfa.final_state
        # adding an edge for repetition to the begining of the already constructed nfa.
        self.states[nfa1.final_state][None] = nfa1.start_state
        # adding to the final state of the constructed nfa an edge to the new final state
        self.states[nfa1.final_state][None] = new_nfa.final_state
        # creating the kleene star nfa 
        # push to the stack frames.
        self.nfa_stack_frames.append(new_nfa)
        if (push_to_op_stack): self.last_op_stack.append('*')

    def thompson_construction(self) -> None:
        """ This turns the regex into epsilon nfa, epsilon will be represented by 'None' """
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
                char += self.postfix[index]
                self.regex_character(char)
                self.input_alphabet.add(char)
            else:
                self.regex_character(char)
                if (char != 'ε'):
                    self.input_alphabet.add(char)
            index += 1
        # the nfa_stack_frames should be of length 1 at this point, otherwise the regex is missing a concatenation or some other thing.
        if (len(self.nfa_stack_frames) != 1): 
            if DEBUG: 
                print(f"ERROR: nfa_stack_frames has length of {len(self.nfa_stack_frames)}")
            else:
                print(f"ERROR: nfa_stack_frames has length of {len(self.nfa_stack_frames)}" + f'\n{self.nfa_stack_frames}')
            exit(-1)
        self.nfa = self.nfa_stack_frames.pop()
        
    def draw_nfa(self):
        # for efficiency just import the function if it is required.
        from draw import draw_graph
        edges = []
        labels = []
        for state,char_next_state in self.states.items():
            for char, next_state in char_next_state.items():
                if (char == None):
                    for i in next_state:
                        edges.append([state, i])
                        labels.append('ε')
                else:
                    edges.append([state, next_state])
                    labels.append(char)
        print(self.nfa)
        draw_graph(edges, labels)

class DFA:
    def __init__(self, nfa:NFA):
        self.dfa_states = dict()
        self.dfa_states_names = dict()
        self.closure_of_all_states = dict()
        self.states = nfa.states
        self.input_alphabet = nfa.input_alphabet
        self.nfa = nfa.nfa
        self.dfa:dfa = dfa()

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
        """
        This method calculates the closure of all states.
        It takes the global variable states and iterates in its keys.
        Then for each state key we calculate the closure using the self.e_closure method.
        """
        for i in self.states.keys():
            self.closure_of_all_states.update({i: self.e_closure(i)})

    def closures(self, set_of_states) -> tuple:
        """
        This method assumes that the calculate_closure_of_all_states method has been runned first.
        This method takes in a set of states, which in our case means a set of numbers.
        These states are keys of the closure_of_all_states global variable dictionary.
        This method simply adds the closure of all the states that are contained in set_of_states argument variable.
        """
        closure = set()
        for i in set_of_states:
            closure |= self.closure_of_all_states[i]
        return tuple(closure)

    def subset_construction(self, new_dfa_state:tuple):
        """
        turns nfa to dfa
        """
        # calculate e_closure de el start_state del nfa.
        if new_dfa_state in self.dfa_states.keys():
            return
        ec = set()
        for state in new_dfa_state:
            ec |= self.closure_of_all_states[state]
        # print(f"ec={ec}")
        dfa_state = {new_dfa_state: {}}
        # print(self.input_alphabet)
        for char in self.input_alphabet:
            for state in ec:
                # iterate over the keys and see if char is in the state
                for transition_letter, next_state in self.states[state].items():
                    if (transition_letter == char):
                        # print(state, states[state])
                        if (dfa_state[new_dfa_state].get(char) == None):
                            dfa_state[new_dfa_state].update({char : set()})
                        dfa_state[new_dfa_state][char].add(next_state)
                        
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
            named_final_states.

    def turn_to_dfa(self):
        self.calculate_closure_of_all_states()
        self.dfa.start_state = tuple([self.nfa.start_state])
        self.subset_construction(tuple([self.nfa.start_state]))
        self.dfa_states_prettify()
    
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

    def draw_dfa(self):
        # for efficiency just import the function if it is required.
        from draw import draw_graph
        edges = []
        labels = []
        for state,char_next_state in self.dfa_states.items():
            for char, next_state in char_next_state.items():
                if (char == None):
                    for i in next_state:
                        edges.append([state, i])
                        labels.append('ε')
                else:
                    edges.append([state, next_state])
                    labels.append(char)
        print(self.dfa)
        draw_graph(edges, labels)
    
    def __repr__(self) -> str:
        return f"({self.dfa_states})"

    def __str__(self) -> str:
        return f"({self.dfa_states})"

class lexer_graph():
    def __init__(self, list_of_dfas):

        pass

if __name__ == '__main__':
    tokens = {
        "TYPE": "(i·n·t|b·o·o·l·e·a·n)", 
        "IF": "i·f", 
        "BOOL_LITERAL": "(t·r·u·e|f·a·l·s·e)" 
    }
    deterministic_finite_automata = {}
    for token, regex in tokens.items():
        nfa1 = NFA(regex)
        nfa1.thompson_construction()
        dfa1 = DFA(nfa1)
        dfa1.turn_to_dfa()
        dfa1.draw_dfa()
        deterministic_finite_automata.update({token: dfa1})
    print(deterministic_finite_automata)







# nfa1 = NFA("a?") #  -?·[0-9]·[0-9]*·(.·[0-9])? ·a·m·\\n
    # nfa1.thompson_construction()
    # dfa1 = DFA(nfa1)
    # dfa1.calculate_closure_of_all_states()
    # dfa1.turn_to_dfa()
    # print(f"{dfa1.dfa_states} \nfinal={dfa1.dfa.final_states}\n\n")
    # nfa2 = NFA("a·b·b*")
    # nfa2.thompson_construction()
    # dfa2 = DFA(nfa2)
    # dfa2.calculate_closure_of_all_states()
    # dfa2.turn_to_dfa()
    # print(f"{dfa2.dfa_states} \nfinal={dfa2.dfa.final_states}\n\n")
    # nfa3 = NFA("a·b·c·\\n")
    # nfa3.thompson_construction()
    # dfa3 = DFA(nfa3)
    # dfa3.calculate_closure_of_all_states()
    # dfa3.turn_to_dfa()
    # print(f"{dfa3.dfa_states} \nfinal={dfa3.dfa.final_states}")

