from string import ascii_lowercase, ascii_uppercase
from typing import Iterable
import argparse

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
        # try:
        if (key == None):
            if (self.get(None) == None):
                self.update({key: set([value])})
            else: 
                self[key].add(value)
        else:
            self.update({key:value})
        # except:
        # print(f"key={key}, value={value} got an error")
    
    # def add_with_epsilon(self, key, value):
    #     if (key == None):
    #         if (self.get(None) == None): # None key has not been created.
    #             self.update({None: [value]})
    #         else:
    #             self[None].append(value)
    #     else:
    #         self.update()


def label_maker() -> int:
    num = 0
    while True:
        yield num
        num += 1    

label_gen = label_maker()
dfa_label_gen = label_maker()
states = dict()
dfa_states = dict()
dfa_states_names = dict()
closure_of_all_states = dict()


class enfa:
    def __init__(self, start_state = None, final_state = None):
        if start_state == None:
            self.start_state:int = next(label_gen)
        else: 
            self.start_state:int = start_state

        if final_state == None:
            self.final_state:int = next(label_gen)
        else:
            self.final_state:int = final_state
    
    def __repr__(self) -> str:
        return f"start={self.start_state} final={self.final_state}"

    def __str__(self) -> str:
        return f"start={self.start_state} final={self.final_state}"

class dfa:
    def __init__(self, start_state = None, final_state = set()):
        self.start_state : int = start_state
        self.final_states:  Iterable[int] = final_state
    
    def __repr__(self) -> str:
        return f"dfa: start={self.start_state} end={self.final_states}"

    def __str__(self) -> str:
        return f"dfa: start={self.start_state} end={self.final_states}"

class Graph:
    def __init__(self, infix:str):
        self.infix              :str            = infix
        self.postfix            :str            = self.infix_to_postfix()
        self.nfa_stack_frames   :Iterable[enfa] = [] 
        self.last_op_stack      :Iterable[str]  = []
        self.nfa                :enfa           = None
        self.input_alphabet     :str            = set()
        self.dfa                :dfa            = dfa()
        # file report and error log.
        self.debug_info = open("report.txt", mode="a")
        self.debug_info.truncate(0)
        self.error_log = open("error.log", mode="a")
        self.error_log.truncate(0)
    
    def __del__(self):
        self.debug_info.close()
        self.error_log.close()

    def infix_to_postfix(self) -> str:
        self.postfix = ""
        stack   = []
        precedence = { # don't use 0, confuses the if's.
            '|': 1, '·': 2, '*': 3, '+': 4, '?': 5, 
        }
        ########################## EXPANDING RANGES #########################################
        new_infix = ""
        i = 0
        while (i < len(self.infix)):
            if (self.infix[i] == "["):
                ii = 0
                i += 1
                char_inside = ""
                while (self.infix[i] != ']'):
                    char_inside += self.infix[i]
                    if ((self.infix[i] == '-') and (ii != 0)):
                        char_inside = char_inside[:-2]
                        low_lim = self.infix[i-1]
                        high_lim = self.infix[i+1]
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
                new_infix += self.infix[i]
            i += 1
        ########################## EXPANDING RANGES #########################################
        ########################## POSTFIX STRING GENERATION #########################################
        self.infix = new_infix
        i = 0
        while (i < len(self.infix)):
            char = self.infix[i]
            if char == '(': 
                stack.append(char)
            elif char == ')':
                while (stack[-1] != '('): 
                    self.postfix += stack.pop()
                stack.pop()
            elif char in precedence.keys():
                while ( (len(stack) != 0) and  (precedence.get(char, 0) <= precedence.get(stack[-1], 0))):
                    self.postfix += stack.pop()
                stack.append(char)
            else:
                self.postfix += char
            i += 1
        
        while len(stack) != 0:
            self.postfix += stack.pop()
        ########################## POSTFIX STRING GENERATION #########################################
        return self.postfix
    
    def regex_or(self, push_to_op_stack=True) -> None:
        # OR a|b
        # pop the last two nfas.
        if ( len(self.last_op_stack) >= 2 ):
            # the last operation was an or then it is a chained or.
            if ( (self.last_op_stack[-2] == '|') and (self.last_op_stack[-1] == 'c') ): 
                character_nfa: enfa = self.nfa_stack_frames.pop() # pop the character nfa
                or_nfa: enfa        = self.nfa_stack_frames.pop() # pop the or nfa
                states[or_nfa.start_state][None] = character_nfa.start_state
                states[character_nfa.final_state][None] = or_nfa.final_state
                self.nfa_stack_frames.append(or_nfa)
                if (push_to_op_stack): self.last_op_stack.append('|') 
                return
        # If it is not a chained or operation then create or nfa as regularly
        nfa2: enfa = self.nfa_stack_frames.pop()
        nfa1: enfa = self.nfa_stack_frames.pop()
        # create a new initial and final state
        new_nfa = enfa()
        states[new_nfa.start_state] = dictlist() # creating states in dict
        states[new_nfa.final_state] = dictlist() # creating states in dict
        # adding epsilons from the new accepting state to the new accepting state.
        states[new_nfa.start_state][None] = nfa1.start_state # creating edge through epsilon
        states[new_nfa.start_state][None] = nfa2.start_state # creating edge through epsilon
        # start_state.edges[None] = nfa1.start_state # (A) -epsilon-> (character nfa 1)
        # start_state.edges[None] = nfa2.start_state # (A) -epsilon-> (character nfa 2)
        # adding epsilons from the old ending states to the new end state.
        states[nfa1.final_state][None] = new_nfa.final_state # (character nfa 1) -epsilon-> (B)
        states[nfa2.final_state][None] = new_nfa.final_state # (character nfa 2) -epsilon-> (B)
        # pushing the merged or nfa to the stack frame.
        self.nfa_stack_frames.append(new_nfa)
        # add last op
        if (push_to_op_stack): self.last_op_stack.append('|')
        
    def regex_character(self, char, push_to_op_stack=True) -> None:
        new_nfa = enfa()
        states[new_nfa.start_state] = dictlist() # creating the new keys:{}
        states[new_nfa.final_state] = dictlist() # creating the new keys:{}
        if (char != 'ε'):
            states[new_nfa.start_state][char] = new_nfa.final_state
        else:
            states[new_nfa.start_state][None] = new_nfa.final_state
        self.nfa_stack_frames.append(new_nfa)
        if (push_to_op_stack): self.last_op_stack.append('c')

    def regex_concatenation(self, push_to_op_stack=True) -> None:
        # CONCATENATION/UNION EXPRESSION 
        nfa2: enfa = self.nfa_stack_frames.pop()
        nfa1: enfa = self.nfa_stack_frames.pop()
        if ((self.last_op_stack[-1] == 'c')): #  and (self.last_op_stack[-2] == 'c')
            # char, state_f = list(nfa2.start_state.edges.items())[0] # get the char that creates the transition to the end state nfa.
            char, state_f = list(states[nfa2.start_state].items())[0]
            states[nfa1.final_state][char] = state_f
            nfa1.final_state = state_f
            del states[nfa2.start_state]
            self.nfa_stack_frames.append(nfa1)
            push_to_op_stack = False
        else:
            # the accepting state of the first nfa will be the starting state of the second nfa
            states[nfa1.final_state][None] = nfa2.start_state
            concatenation_nfa = enfa(nfa1.start_state, nfa2.final_state)
            # adding the new nfa of the concatenated string.
            self.nfa_stack_frames.append(concatenation_nfa)
            print(f"\n{concatenation_nfa}")
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
        states[new_nfa.start_state] = dictlist()
        states[new_nfa.final_state] = dictlist()
        # adding epsilon to the start of nfa1
        states[new_nfa.start_state][None] = nfa1.start_state
        # adding epsilon to the final state in the case of just epsilon. 
        states[new_nfa.start_state][None] = new_nfa.final_state
        # adding an edge for repetition to the begining of the already constructed nfa.
        states[nfa1.final_state][None] = nfa1.start_state
        # adding to the final state of the constructed nfa an edge to the new final state
        states[nfa1.final_state][None] = new_nfa.final_state
        # creating the kleene star nfa 
        # push to the stack frames.
        self.nfa_stack_frames.append(new_nfa)
        if (push_to_op_stack): self.last_op_stack.append('*')

    def e_closure(self, state) -> set:
        closure_states = set()
        closure_states.add(state)
        if (states[state].get(None) == None): # there is no epsilon key.
            return closure_states
        else:
            for edge in states[state][None]:
                closure_states |= self.e_closure(edge)
            return closure_states


    def thompson_construction(self) -> None:
        """ This turns the regex into epsilon nfa, epsilon will be represented by 'None' """
        if DEBUG: self.debug_info.write(self.postfix + '\n')
        index = 0
        for char in self.postfix:
            # The sight of an operator means we already have at least one nfa stack frame
            if (char == '?'):
                self.regex_question_mark(char)
            elif (char == '*'):
                self.regex_kleene()
            elif (char == '·'):
                self.regex_concatenation()
            elif (char == '|'):
                self.regex_or(char)
            else:
                self.regex_character(char)
                if (char != 'ε'):
                    self.input_alphabet.add(char)

            if DEBUG:
                for i in self.nfa_stack_frames:
                    self.debug_info.write(f"{i}\n")
                self.debug_info.write(f"index: {index} {char} "+"-"*100+'\n')
                index += 1
        if DEBUG: self.debug_info.write(f"{self.nfa_stack_frames}\n")
        if (len(self.nfa_stack_frames) != 1): 
            if DEBUG: 
                print(f"ERROR: nfa_stack_frames has length of {len(self.nfa_stack_frames)}")
            else:
                self.error_log.write(f"ERROR: nfa_stack_frames has length of {len(self.nfa_stack_frames)}" + f'\n{self.nfa_stack_frames}')
            exit(-1)
        self.nfa = self.nfa_stack_frames.pop()

    def calculate_closure_of_all_states(self):
        for i in states.keys():
            closure_of_all_states.update({i: self.e_closure(i)})
    
    def closures(self, set_of_states) -> tuple:
        closure = set()
        for i in set_of_states:
            closure |= closure_of_all_states[i]
        return tuple(closure)

    def closure_to_dfa_state(self, new_dfa_state:tuple):
        """
        set_states: is the set of states that we need to perform closure on.
        """
        # calculate e_closure de el start_state del nfa.
        if new_dfa_state in dfa_states.keys():
            return
        ec = set()
        for state in new_dfa_state:
            ec |= closure_of_all_states[state]
        # print(f"ec={ec}")
        dfa_state = {new_dfa_state: {}}
        for char in self.input_alphabet:
            for state in ec:
                # iterate over the keys and see if char is in the state
                for transition_letter, next_state in states[state].items():
                    if (transition_letter == char):
                        # print(state, states[state])
                        if (dfa_state[new_dfa_state].get(char) == None):
                            dfa_state[new_dfa_state].update({char : set()})
                        dfa_state[new_dfa_state][char].add(next_state)
                        
        dfa_state[new_dfa_state] = {k:tuple(sorted(v)) for k,v in dfa_state[new_dfa_state].items()}
        dfa_states.update(dfa_state)
        if self.nfa.final_state in new_dfa_state:
            self.dfa.final_states.add(new_dfa_state)
        for key, value in dfa_state[new_dfa_state].items():
            self.closure_to_dfa_state(value)
        
    def turn_to_dfa(self):
        self.dfa.start_state = tuple([self.nfa.start_state])
        self.closure_to_dfa_state(tuple([self.nfa.start_state]))
        for k,v in dfa_states.items():
            print(k,v)
        print(self.dfa)
    
    def match(self, string_to_match) -> bool:
        current_state = self.dfa.start_state
        for char in string_to_match:
            if (dfa_states[current_state].get(char) != None):
                current_state = dfa_states[current_state][char]
                # print(current_state)
            else:
                return False
        if (current_state in self.dfa.final_states):
            return True
        else:
            return False
        

n = Graph("(a|b)*·a·b·b") #  -?·[0-9]·[0-9]*·(.·[0-9])?
n.thompson_construction()
print(states)
print(n.nfa)
n.calculate_closure_of_all_states()
n.turn_to_dfa()
print(n.match("aabbb"))
