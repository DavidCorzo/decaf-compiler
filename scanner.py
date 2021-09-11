from __future__ import annotations
from dataclasses import dataclass
from string import ascii_lowercase, ascii_uppercase
from copy import deepcopy, copy


def label_maker():
    num = 0
    while True:
        yield num
        num += 1    

DEBUG = True
label_gen = label_maker()

class dictlist(dict):
    def __setitem__(self, key, value):
        try:
            # Assumes there is a list on the key
            self[key].append(value)
        except KeyError: # If it fails, because there is no key
            super(dictlist, self).__setitem__(key, value)
        except AttributeError: # If it fails because it is not a list
            super(dictlist, self).__setitem__(key, [self[key], value])

@dataclass(repr=True, init=True)
class state:
    def __init__(self, label = None):
        if (label == None): self.label = next(label_gen)
        else: self.label = label
        self.edges:dictlist = dictlist()

    def __str__(self) -> str:
        return f"state={self.label} {self.edges}" 

    def __repr__(self) -> str:
        return f"state={self.label} {self.edges}" 
            

@dataclass(repr=True, init=True)
class epsilon_nfa():
    start_state   : state = None
    final_state   : state = None
    last_op       : str   = None

    def __str__(self) -> str:
        return f"nfa: {self.start_state}"

    def __repr__(self) -> str:
        return f"nfa: {self.start_state}"

class NFAGenerator():
    DIGITS = "0123456789"
    def __init__(self, infix:str):
        self.infix = infix
        self.postfix = self.infix_to_postfix()
        self.nfa_stack_frames = [] # list[epsilon_nfa]
        self.last_op_stack = []
        # file report
        self.file = open("report.txt", mode="a")
        self.file.truncate(0)

    def __del__(self):
        self.file.close()

    def infix_to_postfix(self) -> str:
        """ 
        https://www.youtube.com/watch?v=vq-nUF0G4fI
        1. declare a postfix string and a stack string.
        2. declare precedence for the operators (|,.,*,+,?)
        2. for every character do the following:
        2.1     if it is a opening parenthesis append to the stack 
        2.2     if it is a closing parenthesis, pop the stack until the top of the 
                stack is not a closing parenthesis.
        2.3     it it is an operator, check if the stack is not empty, check if the top of 
                the stack has higher precedence than the operator, if it does have higher 
                precedence, pop the stack until it does not have higher precedence or is 
                empty while appending the popped elements to the postfix expression. Then 
                push the char to the stack.
        2.4     if it is not a parenthesis and it is not an operator it can only be an 
                operand. In which case append to the postfix.
        3. if the stack is not empty, pop everything and append it to the postfix expression.
        4. return the post fix expression.
        """
        self.postfix = ""
        stack   = []
        precedence = { # don't use 0, confuses the if's.
            '|': 1, 
            '·': 2, 
            '*': 3, 
            '+': 4, 
            '?': 5, 
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
                        if ((low_lim in self.DIGITS) and (high_lim in self.DIGITS)):
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
    
    def regex_or(self, push_to_op_stack=True):
        # OR a|b
        # pop the last two nfas.
        if ( len(self.last_op_stack) >= 2 ):
            if ( (self.last_op_stack[-2] == '|') and (self.last_op_stack[-1] == 'c') ): # the last operation was an or then it is a chained or.
                character_nfa: epsilon_nfa = self.nfa_stack_frames.pop() # pop the character nfa
                or_nfa: epsilon_nfa        = self.nfa_stack_frames.pop() # pop the or nfa
                or_nfa.start_state.edges[None] = character_nfa.start_state
                character_nfa.final_state.edges[None] = or_nfa.final_state
                self.nfa_stack_frames.append(or_nfa)
                if (push_to_op_stack): self.last_op_stack.append('|') 
                return
        # If it is not a chained or operation then create or nfa as regularly
        nfa2: epsilon_nfa = self.nfa_stack_frames.pop()
        nfa1: epsilon_nfa = self.nfa_stack_frames.pop()
        # create a new initial and final state
        start_state = state()
        final_state = state()
        # adding epsilons from the new accepting state to the new accepting state.
        start_state.edges[None] = nfa1.start_state # (A) -epsilon-> (character nfa 1)
        start_state.edges[None] = nfa2.start_state # (A) -epsilon-> (character nfa 2)
        # adding epsilons from the old ending states to the new end state.
        nfa1.final_state.edges[None] = final_state # (character nfa 1) -epsilon-> (B)
        nfa2.final_state.edges[None] = final_state # (character nfa 2) -epsilon-> (B)
        # constructing the new nfa representing the 'or' construction.
        or_nfa = epsilon_nfa(start_state, final_state)
        # registering that the nfa is of type 'or'
        or_nfa.last_op = '|'
        # pushing the merged or nfa to the stack frame.
        self.nfa_stack_frames.append(or_nfa)
        # add last op
        if (push_to_op_stack): self.last_op_stack.append('|')
        
    def regex_character(self, char, push_to_op_stack=True):
        # CHARACTER state(A) -char-> state(B)
        start_state = state() # adding initial state
        final_state = state() # adding ending state
        if (char != 'ε'): # adding edge -char->
            start_state.edges.update({char : final_state}) 
        else: 
            start_state.edges.update({None : final_state})
        # creating character nfa to push to the nfa stack.
        character_nfa = epsilon_nfa(start_state, final_state)
        # pushing character nfa to the nfa stack.
        self.nfa_stack_frames.append(character_nfa)
        # appending the operation to the char stack
        if (push_to_op_stack):
            self.last_op_stack.append('c')
        # print(character_nfa)
        # print("-"*100)

    # def regex_plus(self, push_to_op_stack=True):
    #     # (nfa1)+ -> (nfa1)·(nfa1)*
    #     # copy all the pointers and the data pointed to of nfa1.
    #     nfa1: epsilon_nfa = deepcopy(self.nfa_stack_frames[-1])
    #     # creates new stack frame of (nfa1)
    #     self.nfa_stack_frames.append(nfa1)
    #     # print("copy??")
    #     print(self.nfa_stack_frames[-2])
    #     print(self.nfa_stack_frames[-1])
    #     exit(-1)
    #     # applies kleene to the top of the stack but we have made a copy (nfa1)* without registering it as a kleene operation.
    #     self.regex_kleene(False)
    #     # applies concatenation to nfa1 to create nfa1·nfa1* into a single nfa. Without registeriing it as a concatenation operation.
    #     self.regex_concatenation(False) # merges the (nfa1)·(nfa2)* into a single nfa
    #     if (push_to_op_stack): self.last_op_stack.append('+')
    
    def regex_concatenation(self, push_to_op_stack=True):
        # CONCATENATION/UNION EXPRESSION 
        nfa2: epsilon_nfa = self.nfa_stack_frames.pop()
        nfa1: epsilon_nfa = self.nfa_stack_frames.pop()
        # the accepting state of the first nfa will be the starting state of the second nfa
        nfa1.final_state.edges[None] = nfa2.start_state
        concatenation_nfa = epsilon_nfa(nfa1.start_state, nfa2.final_state)
        # adding the new nfa of the concatenated string.
        self.nfa_stack_frames.append(concatenation_nfa)
        if (push_to_op_stack): self.last_op_stack.append('·')
        
    def regex_question_mark(self, char, push_to_op_stack=True):
        self.regex_character('ε', False) # create epsilon constrution without registering it as a char operation.
        # the character nfa is already the [-2] in the stack, the [-1] is epsilon.
        self.regex_or(False) # Create an or construction without registering it as a or operation.
        if (push_to_op_stack): self.last_op_stack.append('?')
        
    def regex_kleene(self, push_to_op_stack=True):
        # poping the previous nfa that we are going to do (nfa)*
        nfa1: epsilon_nfa = self.nfa_stack_frames.pop()
        # start and final states for the new nfa
        start_state = state()
        final_state = state()
        # adding epsilon to the start of nfa1
        start_state.edges[None] = nfa1.start_state
        # adding epsilon to the final state in the case of just epsilon. 
        start_state.edges[None] = final_state
        # adding an edge for repetition to the begining of the already constructed nfa.
        nfa1.final_state.edges[None] = nfa1.start_state
        # adding to the final state of the constructed nfa an edge to the new final state
        nfa1.final_state.edges[None] = final_state
        # creating the kleene star nfa 
        kleene_nfa: epsilon_nfa = epsilon_nfa(start_state, final_state)
        # push to the stack frames.
        self.nfa_stack_frames.append(kleene_nfa)
        if (push_to_op_stack): self.last_op_stack.append('*')

    def thompson_construction(self):
        """ This turns the regex into epsilon nfa, epsilon will be represented by 'None' """
        self.file.write(self.postfix + '\n')
        index = 0
        for char in self.postfix:
            # The sight of an operator means we already have at least one nfa stack frame
            if (char == '?'):
                self.regex_question_mark(char)
            # elif (char == '+'):
            #     self.regex_plus()
            elif (char == '*'):
                self.regex_kleene()
            elif (char == '·'):
                self.regex_concatenation()
            elif (char == '|'):
                self.regex_or(char)
            else:
                self.regex_character(char)
            for i in self.nfa_stack_frames:
                self.file.write(f"{i}\n")
            self.file.write(f"index: {index} {char}"+"-"*100+'\n')
            index += 1
        
        self.file.write(f"{self.nfa_stack_frames[0]}\n")
        print(len(self.nfa_stack_frames), char)

    

# 
nfa = NFAGenerator("-?·[0-9][0-9]*·(.·[0-9])?")
# print(nfa.infix_to_postfix())
nfa.thompson_construction()
