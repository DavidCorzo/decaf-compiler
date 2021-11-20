from yaml import parse
from decaf_scanner import scanner
from decaf_parser import lr_0, lr_0_t, parser, is_nonterminal, is_pseudo_terminal, PARENT, PTR, CHILDREN
from decaf_semantic import semantic

mem_space = {'int':4, 'boolean': 1, 'class': 0, 'void': 0}
VAR_TYPE, SP_POS = 0, 1
METHOD_PREFIX, METHOD_POSTFIX = 'MB', 'ME'
FINISH_TAG, MAIN = 'finish:', 0
BEGIN_PROGRAM_MAIN = ['.data\n', '.text\n']
ENDING_TAG = 'end_program'
END_PROGRAM_MAIN = [f'{ENDING_TAG}:\n', '\t# end program\n', '\tli $v0, 10\n', '\tsyscall\n']

OCCUPIED, VACANT = 'OCCUPIED', 'VACANT'
temp_reg = {
    VACANT: {'$t0', '$t1', '$t2', '$t3', '$t4', '$t5', '$t6', '$t7', '$t8', '$t9'},
    OCCUPIED: set()
}


class codegen:
    def __init__(self, assembled_semantic:semantic, executable_filename='a.executable'):
        self.ast                        = assembled_semantic.ast
        self.ast_head                   = assembled_semantic.ast_head
        self.exprs_return               = assembled_semantic.exprs
        self.scope_stack                = list()
        self.next_scope_pending_vars    = dict()
        self.assembler_sections         = list()
        self.current_section            = None
        self.scope_index                = 0
        self.var_type                   = None
        self.stack_ptr                  = 0
        self.main_detected              = False
        self.method_detected            = False
        self.method_vars                = {}
        self.allocate_methods([self.ast_head])
        self.initiate()
        # print(self.assembler_sections)
        self.write_exe(executable_filename)
    
    def write_exe(self, executable_filename):
        with open(executable_filename, mode='w+') as file:
            file.writelines(BEGIN_PROGRAM_MAIN)
            file.writelines(self.assembler_sections[0])
            file.writelines(END_PROGRAM_MAIN)
            for section in self.assembler_sections[1:]:
                for instruction in section:
                    file.write(instruction)
    
    def allocate_methods(self, list_node_i):
        for node_index in list_node_i:
            prod, edges = self.ast[node_index]
            if (prod == '<method_decl*>'):
                var_type = self.ast[self.ast[edges[1]][PTR][0]]
                if var_type[0] == '%type%': var_type = self.ast[self.ast[self.ast[edges[1]][PTR][0]][PTR]][PARENT]
                else: var_type = var_type[0]
                var_name = self.ast[self.ast[edges[2]][PTR]][PARENT]
                self.method_vars[var_name] = [var_type]
            if is_nonterminal(prod) and (edges != None):
                self.allocate_methods(edges)
            
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
                self.allocate_field_decl_and_methods()
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
            elif (prod == '<method_decl*>'):
                self.method_decl_kleene(edges)
            elif (prod == '<statement>'):
                self.statement(edges)
                continue
            elif (prod == '<expr>'):
                self.expr(edges)
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
                    self.next_scope_pending_vars[var_name] = [self.var_type]
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
                    self.scope_stack[self.scope_index][var_name] = [self.var_type]
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
                    self.scope_stack[self.scope_index][var_name] = [self.var_type]
                elif prod == '%type%':
                    self.var_type = self.ast[edge][PARENT]
                elif is_nonterminal(prod) and (edge != None):
                    self.var_decl_kleene(edge)
    
    def allocate_vars_of_scope(self):
        space_to_be_allocated = sum([mem_space[x[VAR_TYPE]] for x in self.scope_stack[self.scope_index].values()])
        var_pos = 0
        for variable in self.scope_stack[self.scope_index]:
            self.scope_stack[self.scope_index][variable].append(var_pos)
            var_pos += mem_space[self.scope_stack[self.scope_index][variable][VAR_TYPE]]
        self.assembler_sections[self.current_section].append(f'\taddi $sp $sp -{space_to_be_allocated} # scope variable allocation\n')

    def allocate_field_decl_and_methods(self):
        s_scope_variables = sum([mem_space[x[VAR_TYPE]] for x in self.scope_stack[self.scope_index].values()])
        s_scope_methods   = sum([mem_space[x[VAR_TYPE]] for x in self.method_vars.values()])
        space_to_be_allocated =  s_scope_variables + s_scope_methods
        var_pos = 0
        for variable in self.scope_stack[self.scope_index]:
            self.scope_stack[self.scope_index][variable].append(var_pos)
            var_pos += mem_space[self.scope_stack[self.scope_index][variable][VAR_TYPE]]
        self.assembler_sections[self.current_section].append(f'\taddi $sp $sp -{space_to_be_allocated} # scope variable allocation\n')
    
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
            # self.assembler_sections[self.current_section].append(f'\tjr $ra\n') ????
            print("3")
            self.assembler_sections[self.current_section].append(f'\tj {ENDING_TAG}\n')
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
            # self.stack_ptr -= mem_space[method_type]
            # self.scope_stack[self.scope_index][method_name] = [method_type]
            # codegen
            if method_name == 'main':
                self.current_section = 0
                self.assembler_sections[0].insert(0, f'{method_name}:\n')
                self.main_detected = True
            else:
                self.current_section += 1
                self.current_section = (len(self.assembler_sections) - 1)
                self.assembler_sections[self.current_section].append(f'{METHOD_PREFIX}{method_name}:\n')
                self.main_detected = False
            self.method_detected = True
    
    def statement(self, edges):
        productions = [self.ast[x][PARENT] for x in edges]
        if productions == ['<assignment_statement>']:
            # ['%id%', '<subscript>', '<assign_op>', '<expr>', ';']
            RHS_EXPR = 3
            rhs_expr_reg = self.expr(self.ast[self.ast[edges[0]][PTR][RHS_EXPR]][PTR])
            # var_name = self.get_var_attributes()
            LHS_VAR = 0
            var_name = self.ast[self.ast[self.ast[edges[PARENT]][PTR][LHS_VAR]][PTR]][PARENT]
            var_attr = self.get_var_attributes(var_name)
            if self.ast[self.ast[edges[0]][PTR][1]][PTR]: # subscript == epsilon?
                SUBS_EXPR = 1
                subscript_offset_expr_reg = self.expr(self.ast[self.ast[self.ast[edges[0]][PTR][1]][PTR][SUBS_EXPR]][PTR])
                # here goes what we need to do with the subscript
            # else:
                
            
        elif productions == ['<method_call>', ';']:
            pass
        elif productions == ['if', '<expr>', '<block>', '<else_block>']:
            pass
        elif productions == ['for', '<for_eval>', '<block>']:
            pass
        elif productions == ['return', ';']:
            pass
        elif productions == ['return', '<expr>', ';']:
            pass
        elif productions == ['break', ';']:
            pass
        elif productions == ['continue', ';']:
            pass
        elif productions == ['<block>']:
            pass
        elif productions == ['<expr>', ';']:
            pass
    
    def subscript(self, edge):
        right_sb = edge[0]
        offset   = edge[1]
        left__sb = edge[2]
    
    def expr(self, edges):
        productions = [self.ast[x][PARENT] for x in edges]
        if (productions == ['%id%', '<subscript>']):
            return 
        elif (productions == ['<literal>']):
            next_prod = self.ast[self.ast[edges[0]][PTR][0]][PARENT]
            value = self.ast[self.ast[self.ast[edges[0]][PTR][0]][PTR]][PARENT]
            val = str()
            if (next_prod == '%int_literal%'):
                val = value
            elif (next_prod == '%char_literal%'):
                val = str(ord(value[1])) # ' <char> '
            elif (next_prod == '%bool_literal%'):
                if value == 'true': val = '1'
                elif value == 'false': val = '0'
                else: self.std_error('boolean is assigned value that is not \'true\' or \'false\'')
            else:
                self.std_error(f'<literal> is having value that is not defined {next_prod}')
            temp = self.get_vacant_temp()
            self.assembler_sections[self.current_section].append(f'\tli {temp} {val}\n')
            return temp
        elif (productions == ['<expr>', '<bin_op>', '<expr>']):
            pass
        elif (productions == ['%minus%', '<expr>']):
            right_expr_reg = self.expr(self.ast[edges[1]])
            self.assembler_sections[self.current_section].append(f'sub {right_expr_reg} $zero {right_expr_reg}')
            return right_expr_reg
        elif (productions == ['!', '<expr>']):
            right_expr_reg = self.expr(self.ast[edges[1]])
            self.assembler_sections[self.current_section].append(f'nor {right_expr_reg} {right_expr_reg} {right_expr_reg}')
            return right_expr_reg
        elif (productions == ['(', '<expr>', ')']):
            center_expr_reg = self.expr(self.ast[edges[1][PTR]])
            return center_expr_reg
        elif (productions == ['(', '<expr>', '<bin_op>', '<expr>', ')']):
            left_expr_reg   = self.expr(self.ast[edges[1]][PTR])
            bin_op_tup      = self.ast[self.ast[edges[2]][PTR][0]]
            right_expr_reg  = self.expr(self.ast[edges[3]][PTR])
            bin_op = str()
            if (bin_op_tup[PARENT] == '<arith_op>'):
                bin_op = self.ast[bin_op_tup[PTR][0]][PARENT]
                if (bin_op == '%plus%'): 
                    self.assembler_sections[self.current_section].append(f'')
                elif (bin_op == '%minus%'): 
                    # ['sub']
                    self.assembler_sections[self.current_section].append(f'')
                elif (bin_op == '%mult%'): 
                    # ['mult', 'mfhi', 'mflo']
                    self.assembler_sections[self.current_section].append(f'')
                elif (bin_op == '%div%'): 
                    # ['div', 'mfhi', 'mflo']
                    self.assembler_sections[self.current_section].append(f'')
                elif (bin_op == '%mod%'): 
                    # ['div', 'mfhi']
                    self.assembler_sections[self.current_section].append(f'')
                else:
                    self.std_error(f'unrecognized operator for <expr> {bin_op}')
            elif (bin_op_tup[PARENT] == '%rel_op%'):
                pass
            elif (bin_op_tup[PARENT] == '%eq_op%'):
                pass
            elif (bin_op_tup[PARENT] == '%cond_op%'):
                pass
        else:
            self.std_error(f'no <expr> form detected {productions}')


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
    
    def get_var_attributes(self, var_name):
        if self.scope_stack[self.scope_index].get(var_name):
            return self.scope_stack[self.scope_index][var_name]
        else:
            index = self.scope_index
            while index >= 0:
                if self.scope_stack[index].get(var_name):
                    return self.scope_stack[index][var_name]
                index -= 1
            self.std_error(f'{var_name} was not found in current scope nor in any previous scope.')
    
    def get_vacant_temp(self):
        if len(temp_reg[VACANT]):
            popped = temp_reg[VACANT].pop()
            temp_reg[OCCUPIED].add(popped)
            return popped
        else:
            print(f"Codegen error: not enough registers to compute operation {temp_reg}")
    
    def std_error(self, error_str):
        print(f'Codegen error: {error_str}')
        exit(-1)

s = scanner('./src_code.decaf', './tokens', build=1, save=0)
l = lr_0('<program>', './productions.yaml', build=1, save=0)
t = lr_0_t(l)
p = parser(t, s)
with open('tree_debug.txt', mode='w+') as file:
    file.write(str(p))
    file.close()
s = semantic(p)
c = codegen(s, 'a.executable')
