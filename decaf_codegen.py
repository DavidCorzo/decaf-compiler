from yaml import parse
from scanner import scanner
from decaf_parser import lr_0, slr, parser, is_nonterminal, is_pseudo_terminal, PARENT, PTR, CHILDREN
from semantic import semantic

mem_space = {'int':4, 'boolean': 1, 'class': 0, 'void': 0}
VAR_TYPE, SP_POS = 0, 1
METHOD_PREFIX, METHOD_POSTFIX = 'MB', 'ME'
FINISH_TAG, MAIN = 'finish:', 0
BEGIN_PROGRAM_MAIN = ['.data\n', '.text\n']
END_PROGRAM_MAIN = ['\tli $v0, 10\n', '\tsyscall\n']
class codegen:
    def __init__(self, assembled_semantic:semantic, executable_filename='a.executable'):
        self.ast                        = assembled_semantic.productions_tree
        self.ast_head                   = assembled_semantic.productions_tree_head
        self.executable_f               = str()
        self.scope_stack                = list()
        self.next_scope_pending_vars    = dict()
        self.assembler_sections         = list()
        self.current_section            = None
        self.scope_index                = 0
        self.var_type                   = None
        self.stack_ptr                  = 0
        self.main_detected              = False
        self.method_detected            = False
        self.initiate()
        self.write_exe(executable_filename)
    
    def write_exe(self, executable_filename):
        with open(executable_filename, mode='w+') as file:
            file.writelines(BEGIN_PROGRAM_MAIN)
            file.writelines(self.assembler_sections[0])
            file.writelines(END_PROGRAM_MAIN)
            for section in self.assembler_sections[1:]:
                for instruction in section:
                    file.write(instruction)
    
    def initiate(self):
        self.scope_stack.append({})
        self.scope_index = 0
        self.assembler_sections.insert(0, list()) # first main section
        self.current_section = 0
        self.traverse([self.ast_head])

    
    def traverse(self, list_node_i):
        for node_index in list_node_i:
            prod, edges = self.ast[node_index]
            if (prod == '<field_decl*>'):
                self.field_decl_kleene(edges)
                self.allocate_vars_of_scope()
                continue
            elif (prod == '<var_decl*>'):
                self.var_decl_kleene(edges)
                self.allocate_vars_of_scope()
                continue
            elif (prod == '<method_args>'):
                self.method_args(edges)
                continue
            elif (prod == '<method_call>'):
                self.method_call(edges)
                continue
            elif (prod == '<statement>'):
                self.statement(edges)
                continue
            # elif (prod == '<program">'):
            #     self.program_quote(edges)
            elif (prod == '<method_decl*>'):
                self.method_decl_kleene(edges)
            elif (prod == '{'):
                self.opening_curly()
            elif (prod == '}'):
                self.closing_curly()

            # simply pass the next recursive call with the parameters 
            if is_nonterminal(prod) and (edges != None):
                self.traverse(edges)
    
    def method_args(self, edges): # will return dict with all declared vars.
        if edges:
            for node_index in edges:
                prod, edge = self.ast[node_index]
                if prod == '%id%':
                    var_name = self.ast[edge][PARENT]
                    # reserve memory
                    self.stack_ptr -= mem_space[self.var_type]
                    self.next_scope_pending_vars[var_name] = (self.var_type, self.stack_ptr)
                elif prod == '%type%':
                    self.var_type = self.ast[edge][PARENT]
                elif is_nonterminal(prod) and (edge != None):
                    self.method_args(edge)
    
    def field_decl_kleene(self, edges):
        if edges:
            for node_index in edges:
                prod, edge = self.ast[node_index]
                if prod == '%id%':
                    var_name = self.ast[edge][PARENT]
                    # reserve memory
                    self.stack_ptr -= mem_space[self.var_type]
                    self.scope_stack[self.scope_index][var_name] = (self.var_type, self.stack_ptr)
                elif prod == '%type%':
                    self.var_type = self.ast[edge][PARENT]
                elif is_nonterminal(prod) and (edge != None):
                    self.field_decl_kleene(edge)
    
    def var_decl_kleene(self, edges):
        if edges:
            for node_index in edges:
                prod, edge = self.ast[node_index]
                if prod == '%id%':
                    var_name = self.ast[edge][PARENT]
                    # reserve memory
                    self.stack_ptr -= mem_space[self.var_type]
                    self.scope_stack[self.scope_index][var_name] = (self.var_type, self.stack_ptr)
                elif prod == '%type%':
                    self.var_type = self.ast[edge][PARENT]
                elif is_nonterminal(prod) and (edge != None):
                    self.var_decl_kleene(edge)
    
    def allocate_vars_of_scope(self):
        space = 0
        for variable, attr in self.scope_stack[self.scope_index].items():
            space += mem_space[attr[VAR_TYPE]]
        self.assembler_sections[self.current_section].append(f'\taddi $sp $sp -{space} # allocate scop vars\n')
    
    # def program_quote(self, edges):
    #     if edges:
    #         var_name = self.ast[self.ast[edges[PTR]][PTR]][PARENT]
    #         # don't really need Program, consider removing it
    #         self.scope_stack[self.scope_index][var_name] = ('class', self.stack_ptr)
    #         # codegen
    #         self.executable_f += f'{var_name}:\n'
    
    def opening_curly(self):
        self.scope_stack.append({})
        self.scope_index += 1
        # codegen with pending vars
        self.scope_stack[self.scope_index].update(self.next_scope_pending_vars)
        self.next_scope_pending_vars = dict()
    
    def closing_curly(self):
        # free the memory allocated in this scope.
        deallocate = 0
        for att in self.scope_stack[-1].values():
            deallocate += mem_space[att[VAR_TYPE]]
        self.assembler_sections[self.current_section].append(f'\taddi $sp $sp {deallocate} # out of scope deallocation\n')
        self.scope_stack.pop()
        self.scope_index -= 1
        if (not self.main_detected) and  (self.method_detected):
            self.assembler_sections[self.current_section].append(f'\tjr $ra\n')
        self.method_detected = self.main_detected = False
    
    def method_decl_kleene(self, edges):
        if edges:
            method_name = self.ast[self.ast[edges[2]][PTR]][PARENT]
            method_type = self.ast[self.ast[edges[1]][PTR][0]]
            if method_type[PARENT] == '%type%':
                method_type = self.ast[method_type[CHILDREN]][PARENT]
            else:
                method_type = method_type[PARENT]
            # reserve memory
            self.stack_ptr -= mem_space[method_type]
            self.next_scope_pending_vars[method_name] = (method_type, self.stack_ptr)
            # codegen
            if method_name == 'main':
                self.current_section = 0
                self.assembler_sections[0].insert(0, f'{method_name}:\n')
                self.main_detected = True
            else:
                self.assembler_sections.append([])
                self.current_section += 1
                self.current_section = (len(self.assembler_sections) - 1)
                self.assembler_sections[-1].append(f'{METHOD_PREFIX}{method_name}:\n')
                self.main_detected = False
            # if mem_space[method_type] != 0:
            #     self.assembler_sections[self.current_section].append(f'\taddi $sp $sp -{mem_space[method_type]} # return {method_type} {method_name} \n')
            self.method_detected = True
    
    def statement(self, edges):
        productions = [self.ast[x][PARENT] for x in edges]
        if productions == ['%id%', '<subscript>', '<assign_op>', '<expr>', ';']:
            var_name = self.ast[self.ast[edges[0]][PTR]][PARENT]
            subscript_offset = self.ast[edges[1]]
            print(subscript_offset)
    
    def subscript(self, edge):
        right_sb = edge[0]
        offset   = edge[1]
        left__sb = edge[2]
    
    def expr(self, edges):
        pass

    def method_call(self, edges):
        # %id% ( )
        # %id% ( <comma_expr> )
        # callout ( <str|null> ) 
        # callout ( <str|null> <comma_callout_arg> )
        for node_index in edges:
            prod, edge = self.ast[node_index]
            if prod == '%id%':
                var_name = self.ast[edge][PARENT]
                self.assembler_sections[self.current_section].append(f'\tjal {var_name} # method call\n')
            elif prod == 'callout':
                pass

code = scanner("./src_code.decaf", "./tokens.yaml")
code.produce_automata()
code.save_automata("tokens.pickle")
code.scan()
code.linked_list_of_tokens.append((None, '$'))

l = lr_0('<program>', 'productions.yaml', build=1, save=1)
s = slr(l)
for c in code.linked_list_of_tokens:
    print(c)
p = parser(s, code.linked_list_of_tokens)
print(p)
# s = semantic(p)
# c = codegen(s)
