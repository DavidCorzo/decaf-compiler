from os import error
from string import ascii_lowercase, ascii_uppercase, digits
from typing import Iterable, OrderedDict
from yaml import safe_load
import pickle

# class dictlist(dict):
#     def __setitem__(self, key, value):
#         if (key == None):
#             if (self.get(None) == None):
#                 self.update({key: set([value])})
#             else: 
#                 self[key].add(value)
#         else:
#             self.update({key:value})

def add_edge(states, state, key, value):
    if (key == None):
        if (states[state].get(None) == None):
            states[state].update({key : set([value])})
        else:
            states[state][key].add(value)
    else:
        states[state].update({key : value})

def num_label_maker() -> int:
    """
    Generador para poder generar estados únicos. Usados en estados de nfa.
    """
    num = 0
    while True:
        yield num
        num += 1

def letter_label_maker() -> int:
    """
    Generador para poder generar estados únicos. Usados en estados de DFA.
    """
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
        Este método usa el atributo de clase self.infix, que es una expresión regular en forma infix.
        expandemos expresiones abreviadas como [a-c] -> (a|b|c) a su equivalente en ors.
        Luego procede a hacer una expresión regular que está en forma de postfix.
        Example: a+b+(c+d) -> cd+a+b+
        """
        postfix = ""
        stack   = []
        precedence = { # don't use 0, confuses the if's.
            '|': 1, '·': 2, '*': 3, '+': 4, '?': 5
        }
        ########################## EXPANDING RANGES #########################################
        # new_infix = ""
        # i = 0
        # while (i < len(infix)):
        #     if (infix[i] == "["):
        #         ii = 0
        #         i += 1
        #         char_inside = ""
        #         while (infix[i] != ']'):
        #             char_inside += infix[i]
        #             if ((infix[i] == '-') and (ii != 0)):
        #                 char_inside = char_inside[:-2]
        #                 low_lim = infix[i-1]
        #                 high_lim = infix[i+1]
        #                 if ((low_lim in digits) and (high_lim in digits)):
        #                     for r in range(int(low_lim), int(high_lim) + 1):
        #                         char_inside += str(r)
        #                 elif ((low_lim in ascii_lowercase) and (high_lim in ascii_lowercase)):
        #                     for r in range(ord(low_lim), ord(high_lim) + 1):
        #                         char_inside += '|' + chr(r)
        #                 elif ((low_lim in ascii_uppercase) and (high_lim in ascii_uppercase)):
        #                     for r in range(ord(low_lim), ord(high_lim) + 1):
        #                         char_inside += '|' + chr(r)
        #                 else:
        #                     print("Error in range of regular expression.")
        #                     exit(-1)
        #                 i += 1
        #             elif (infix[i] == '\\'):
        #                 print(char_inside)
        #                 char_inside += '\\' + infix[i+1]
        #                 i += 1
        #             ii += 1
        #             i  += 1
        #         print(char_inside)
        #         new_infix += f"({'|'.join([x for x in char_inside])})"
        #     else:
        #         new_infix += infix[i]
        #     i += 1
        ########################## EXPANDING RANGES #########################################
        ########################## POSTFIX STRING GENERATION #########################################
        # infix = new_infix
        # print(infix)
        # exit(-1)
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
        """
        Operación or. 
        Si la última operación y la penultima fueron 'c' y '|' estamos hablando de una operación tipo or encadenada, no crearemos más nodos con epsilon, usaremos los que ya están y sólo agregaremos la nueva arista de épsilon al nfa 'c'.
        De lo contrario creamos dos nuevos estados y unimos el estado inicial a los dos nfas que le dimos pop, a los dos nfas que les dimos pop les agregamos aristas al nuevo nodo final y le damos push al stack.
        registramos operación '|' a menos que nos indiquen lo contrario.
        """
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
        """
        Hacemos la operación de character.
        creamos dos estados.
        agregamos una arista del nodo inicial al final por medio del character que nos manden.
        hacemos push al stack.
        registramos la operación como 'c' en el stack.
        """
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
        """
        Opeación concatenación.
        Le damos pop dos veces al stack.
        Si son characteres no unimos con épsilon sino simplemente usamos las mismas aristas de caracteres para poder concatenar. de lo contrario usamos épsilon para unir dos nfas.
        Registramos la operacion '·' al stack a menos que nos especifiquen no hacerlo.
        """
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
        """
        Realizamos la operación de ?. que es (epsilon|nfa)
        Basicamente agregamos una arista de épsilon en el nodo inicial nfa que esta en el top del stack al final node del mismo nfa.
        Y registramos la operación ? a menos que no especifiquen no hacerlo.
        """
        # the character nfa is already the [-2] in the stack, the [-1] is epsilon.
        ## self.states[self.nfa_stack_frames[-1].start_state][None] = self.nfa_stack_frames[-1].final_state
        add_edge(self.states, self.nfa_stack_frames[-1].start_state, None, self.nfa_stack_frames[-1].final_state)
        if (push_to_op_stack): self.last_op_stack.append('?')
        
    def regex_kleene(self, push_to_op_stack=True) -> None:
        """
        Se encarga de realizar la operación de asterisko o kleene.
        haceos pop del último nfa que esta en el stack.
        creamos los estados necesarios para la operación unidos con épsilon respectivamente.
        agregamos dicho nfa de nuevo al stack.
        registramos como última operación el asterisco a menos que nos especifiquen que no lo hagamos con el argumento push_to_op_stack.
        """
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
        """
        Esto convierte la expresión regular en epsilon nfa, epsilon estará representado por 'None'
        Convertimos el regex a postfix.
        Checkeamos los operadores y llamamos a las funciones según la operación especificada.
        Si está precedida por \\ si escapa el siguiente character, si el character siguiente es n o t los registramos como \n y \t, de lo contrario omitimos \\ y solo agarramos el siguiente character.
        Si el char input no es ningun operador entonces asumimos que es un character. Si es épsilon no lo agregamos al input alphabet.
        """
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
            print(f"ERROR: nfa_stack_frames has length of {len(self.nfa_stack_frames)}")
            print(f"{self.infix} is incorrect")
            exit(-1)
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
    #     print(self.nfa)
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
        """
        Este método calcula recursivamente el closure de un sólo estado.
        Primero declaramos un set que contendrá todos los estados con los cuales podemos llegar con epsilon.
        Agregamos el estado actual.
        revisamos si la llave de épsilon existe, si no existe este es el base case.
        de lo contrario iteramos por todos los estados en los cuales podemos llegar con epsilon.
        Por cada de estos estados hay que verificar si tienen más aristas de épsilon entonces hacemos la llamada recursiva.
        Al terminar el for retornamos el closure del estado inicial que se pidió.
        """
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
        Este método calcula el closure de todos los estados.
        Toma los estados de las variables globales e itera en sus claves.
        Luego, para cada clave de estado, calculamos el closure utilizando el método self.e_closure.
        """
        for i in self.states.keys():
            self.closure_of_all_states.update({i: self.e_closure(i)})

    def closures(self, set_of_states) -> tuple:
        """
        Este método asume que el método calculate_closure_of_all_states se ejecutó primero.
        Este método toma un conjunto de estados, que en nuestro caso significa un conjunto de números.
        Estos estados son claves del diccionario de variables globales de closings_of_all_states.
        Este método simplemente agrega el closure de todos los estados que están contenidos en la variable de argumento set_of_states.
        """
        closure = set()
        for i in set_of_states:
            closure |= self.closure_of_all_states[i]
        return tuple(closure)

    def subset_construction(self, new_dfa_state:tuple):
        """
        turns nfa to dfa usando el algoritmo de subset construction especificado en el libro con epsilon closure.
        """
        # calculate e_closure de el start_state del nfa.
        if new_dfa_state in self.dfa_states.keys():
            return
        ec = set()
        for state in new_dfa_state: # (6,) -> (8,4,5,6)
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
                        dfa_state[new_dfa_state][char].add(next_state) # {(6,): {'a': {5,6}}} -> {(6,): {'a': (5,6)}}

        dfa_state[new_dfa_state] = {k:tuple(sorted(v)) for k,v in dfa_state[new_dfa_state].items()}
        self.dfa_states.update(dfa_state)
        if self.nfa.final_state in self.closures(new_dfa_state):
            self.dfa.final_states.add(new_dfa_state)
        for key, value in dfa_state[new_dfa_state].items():
            self.subset_construction(value)

    def dfa_states_prettify(self):
        """
        Cambia el nombre de los estados de tuplas a letras autogeneradas.
        """
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
        """
        Llama a los métodos correpondientes para construir el DFA a partir de una construcción de NFA.
        Primero calculamos el closure de todos los estados indiscriminadamente.
        Guardamos el estado de inicio del dfa para registrarlo en el objeto.
        Construimos el DFA con el algoritmo de subset construction.
        Por ultimo, puesto que las llaves del diccionario son tuplas dichas tuplas las remplazamos por una letra autogenerada única para hacer que debugging sea más fácil.
        """
        self.calculate_closure_of_all_states()
        self.dfa.start_state = tuple([self.nfa.start_state])
        self.subset_construction(tuple([self.nfa.start_state])) # (6,)
        self.dfa_states_prettify()
    
    def match(self, string_to_match) -> bool:
        """
        Nos permite meter un buffer de characteres y ver si hace match a la expresión regular actual que ya está en forma de DFA.
        """
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
    #     # print(self.dfa)
    #     draw_graph(edges, labels)
    
    def __repr__(self) -> str:
        return f"({self.dfa_states})"

    def __str__(self) -> str:
        return f"({self.dfa_states})"
    
    def consume(self, char) -> bool:
        """
        Avanza un solo caracter en el dfa, si no hay por donde avanzar retornamos false para denotar que no es un match.
        """
        if (self.current_position == None):
            self.current_position = self.dfa.start_state
        if (self.dfa_states[self.current_position].get(char) == None):
            return False
        else:
            self.current_position = self.dfa_states[self.current_position][char]
            # print(self.current_position)
            return True
    

class scanner:
    def __init__(self, filename, token_file=None):
        self.filename = filename
        self.current_line = 0
        self.current_line_index = 0
        self.file = open(filename, mode="r", encoding="utf-8")
        self.content = self.file.read()
        self.content_index = 0
        self.line_num = 1
        self.char_num = 1
        self.deterministic_finite_automata = {}
        if token_file != None:
            with open(token_file, mode="r") as file:
                self.tokens = OrderedDict(safe_load(file))
                file.close()
        else:
            self.load_automata()
        self.linked_list_of_tokens = []
        self.candidates = []
        self.error = error_msg()
    
    def produce_automata(self):
        """
        Toma los tokens del archivo tokens.yaml y los compila a NFA y después a DFA y los agrega al diccionario deterministic_finite_automata como el <nombre del token>: <dfa compilado>.
        """
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
            # self.deterministic_finite_automata = pickle.Unpickler(file).load()
            self.deterministic_finite_automata = pickle.load(file)
            file.close()

    def next_char(self):
        """
        Avanza al siguiente caracter en la cadena de input.
        """
        self.content_index += 1
        
    def peek_current(self):
        """
        nos permite leer el caracter actual en el que estamos.
        Si ya estamos en EOF retorna None. 
        Consiguientemente terminando el proceso.
        """
        if self.content_index < len(self.content):
            return self.content[self.content_index]
        else:
            return None
    
    def peek_next(self):
        """
        nos permite ver el siguiente caracter en el archivo para tomar decisiones.
        """
        if ((self.content_index + 1) < len(self.content)):
            return self.content[self.content_index + 1]
        else:
            return None
    
    def recognize(self, buffer):
        """
        Toma un texto que es posiblemente un candidato a ser un token y las compara con todo el banco de expresiones regulares.
        El primero que haga match es el que retorna, si ninguno hace match retorna None y se produce un error.
        El primero significa que hay una precedencia, por ello ID esta de último.
        """
        for token, determ_fa in self.deterministic_finite_automata.items():
            if (determ_fa.match(buffer)):
                return token
        return None
    
    def append_to_list_of_token(self, match, token):
        if (match == None):
            self.linked_list_of_tokens.append(token)
        elif (':value' in match[1:-1]):
            self.linked_list_of_tokens.append(token)
        else:
            self.linked_list_of_tokens.append((match, token))

    def scan(self):
        """
        Con los DFAs ya construidos hace el scanning y le pasa el texto al lexer para reconocer los tokens.
        """
        buffer = ""
        while (self.content_index < len(self.content)):
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
            elif char in "(){}[];,":
                if buffer != '':
                    match_regex = self.recognize(buffer)
                    if match_regex: 
                        self.append_to_list_of_token(match_regex, buffer)
                    else: self.error.no_regex_match(self)
                self.append_to_list_of_token(None, char)
                buffer = ''
            elif char in "<>=!+-*/":
                symbol = char
                next_char = self.peek_next()
                if next_char != None:
                    if next_char in "=<>": 
                        symbol += next_char
                match_regex = self.recognize(symbol)
                if (match_regex): 
                    self.append_to_list_of_token(match_regex, symbol)
                else: self.error.no_regex_match(self)
                buffer = ''
            elif char in "\"\'":
                terminal = char
                buffer += char
                self.content_index += 1
                double_quote_detected = True
                while (self.content_index < len(self.content)):
                    char = self.content[self.content_index]
                    buffer += char
                    if (char == terminal):
                        double_quote_detected = False
                        break
                    elif (char == '\\'):
                        self.content_index += 1
                        char = self.content[self.content_index]
                        if (char == 'n'):   buffer += '\n'
                        elif (char == 't'): buffer += '\t'
                        else:               buffer += char
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
        """
        Chequea si los characteres son ascii.
        """
        return len(char) == len(char.encode())

class error_msg:
    """
    Esta clase es la de mensajes de error.
    illegal characters: toma como argumento la instancia del scanner y extrae el caracter y la posición de dicho caracter. Desupués para la ejecución.
    no_regex_match: toma con argumento la instancia del scanner y extrae las coordenadas. Después para ejecución.
    """
    def illegal_character(self, scanner_instance:scanner):
        print(f"ILLEGAL CHARACTER FOUND '{scanner_instance.content[scanner_instance.content_index]}'")
        print(f"illegal character found at line {scanner_instance.line_num} column {scanner_instance.char_num}")
        exit(-1)
    
    def no_regex_match(self, scanner_instance):
        print(f"NO KEYWORD MATCH FOR '{scanner_instance.content[scanner_instance.content_index]}'")
        print(f"No match was found for the above char in line {scanner_instance.line_num} column {scanner_instance.char_num}")
        exit(-1)

    def unmatching_doublequotes(self, scanner_instance):
        print(f"FILE TERMINATED WITHOUT CLOSING STRING '{scanner_instance.content[scanner_instance.content_index]}'")
        print(f"No double quote to close, above char in line {scanner_instance.line_num} column {scanner_instance.char_num}")
        exit(-1)
    
    def unmatching_singlequotes(self, scanner_instance):
        print(f"FILE TERMINATED WITHOUT CLOSING CHAR LITERAL '{scanner_instance.content[scanner_instance.content_index]}'")
        print(f"No single quote to close, above char in line {scanner_instance.line_num} column {scanner_instance.char_num}")
        exit(-1)
    
if __name__ == '__main__':
    code = scanner("./src_code.txt", "./tokens.yaml")
    code.produce_automata()
    code.save_automata("tokens.pickle")
    # code.load_automata("./tokens.pickle")
    code.scan()
    print(code.linked_list_of_tokens)
