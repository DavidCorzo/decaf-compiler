from yaml import parse
from decaf_scanner import scanner
from decaf_parser import lr_0, lr_0_t, parser, is_nonterminal, is_pseudo_terminal, PARENT, PTR, CHILDREN
from decaf_semantic import semantic


class codegen:
    def __init__(self, assembled_semantic:semantic, executable_filename='a.asm'):
        self.ast                        = assembled_semantic.ast
        self.ast_head                   = assembled_semantic.ast_head
        self.exprs_return               = assembled_semantic.exprs
        self.scope_stack                = list()
        self.scope_space                = dict()
        self.method_reg                 = dict()
        self.next_scope_pending_vars    = dict()
        self.assembler_sections         = list()
        self.current_section            = None
        self.scope_index                = 0
        self.var_type                   = None
        self.stack_ptr                  = 0
        self.main_detected              = False
        self.method_detected            = False
        self.method_vars                = {}
        self.processed_expr             = set()
        self.offset                     = 0
        self.allocate_methods([self.ast_head])
        self.initiate()
        self.write_exe(executable_filename)
    
    def write_exe(self, executable_filename):
        with open(executable_filename, mode='w+') as file:
            file.truncate(0)
            file.writelines(BEGIN_PROGRAM_MAIN)
            file.writelines(self.assembler_sections[0])
            file.writelines(END_PROGRAM_MAIN)
            for section in self.assembler_sections[1:]:
                for instruction in section:
                    file.write(instruction)
            file.writelines(END_PROGRAM_TAG)
    
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
            elif (prod == '<statement*>'):
                self.statement_kleene(edges)
                continue
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
        if space_to_be_allocated:
            self.assembler_sections[self.current_section].append(f'\t# {self.scope_stack[self.scope_index]}\n')
            self.assembler_sections[self.current_section].append(f'\taddi $sp $sp -{space_to_be_allocated} # var alloc\n')
        if self.scope_space.get(self.scope_index):
            self.scope_space[self.scope_index] += space_to_be_allocated
        else:
            self.scope_space[self.scope_index] = space_to_be_allocated

    def allocate_field_decl_and_methods(self):
        s_scope_variables = sum([mem_space[x[VAR_TYPE]] for x in self.scope_stack[self.scope_index].values()])
        s_scope_methods   = 0 # use v sum([mem_space[x[VAR_TYPE]] for x in self.method_vars.values()])
        space_to_be_allocated =  s_scope_variables + s_scope_methods
        var_pos = 0
        for variable in self.scope_stack[self.scope_index]:
            self.scope_stack[self.scope_index][variable].append(var_pos)
            var_pos += mem_space[self.scope_stack[self.scope_index][variable][VAR_TYPE]]
        self.assembler_sections[self.current_section].append(f'\t# {self.scope_stack[self.scope_index]}\n')
        self.assembler_sections[self.current_section].append(f'\taddi $sp $sp -{space_to_be_allocated} # field_decl & methods alloc\n')
        if self.scope_space.get(self.scope_index):
            self.scope_space[self.scope_index] += space_to_be_allocated
        else:
            self.scope_space[self.scope_index] = space_to_be_allocated
    
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
        if deallocate:
            self.assembler_sections[self.current_section].append(f'\taddi $sp $sp {deallocate} # out of scope deallocation\n')
        self.scope_stack.pop()
        self.scope_index -= 1
        if (self.method_detected):
            self.assembler_sections[self.current_section].append(f'\taddi $sp $sp {self.offset} # frame dealloc\n')
            self.offset = 0
        if (self.main_detected):
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
            if method_name == 'main':
                self.current_section = 0
                self.assembler_sections[0].insert(0, f'{method_name}:\n')
                self.main_detected = True
            else:
                self.current_section += 1
                self.assembler_sections.insert(self.current_section, list())
                self.assembler_sections[self.current_section].append(f'{METHOD_PREFIX}{method_name}:\n')
                self.main_detected = False
            self.method_detected = True
            # allocate for the $ra, and all the $s<reg>
            RETURN_ADDRESS, S_REG, FP = 4, 4*8, 4
            self.offset = (RETURN_ADDRESS + S_REG + FP)
            self.stack_ptr -= self.offset
            self.assembler_sections[self.scope_index].append(f'\taddi $sp $sp -{(RETURN_ADDRESS + S_REG + FP)}\n')
            self.scope_stack[self.scope_index].update({
                '$ra': ['int', mem_space['int']*0],
                '$s0': ['int', mem_space['int']*1],
                '$s1': ['int', mem_space['int']*2],
                '$s2': ['int', mem_space['int']*3],
                '$s3': ['int', mem_space['int']*4],
                '$s4': ['int', mem_space['int']*5],
                '$s5': ['int', mem_space['int']*6],
                '$s6': ['int', mem_space['int']*7],
                '$s7': ['int', mem_space['int']*8],
                '$fp': ['int', mem_space['int']*9]
            })
            self.assembler_sections[self.current_section].append(f'\t# stack frame allocation\n')
            self.assembler_sections[self.current_section].append(f'\tsw $ra {mem_space["int"]*0}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $s0 {mem_space["int"]*1}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $s1 {mem_space["int"]*2}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $s2 {mem_space["int"]*3}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $s3 {mem_space["int"]*4}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $s4 {mem_space["int"]*5}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $s5 {mem_space["int"]*6}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $s6 {mem_space["int"]*7}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $s7 {mem_space["int"]*8}($sp)\n')
            self.assembler_sections[self.current_section].append(f'\tsw $fp {mem_space["int"]*9}($sp)\n')
    
    def statement_kleene(self, edges):
        if edges:
            for node_index in edges:
                prod, edge = self.ast[node_index]
                if prod == '<statement>':
                    self.statement(edge)
                    continue
                elif is_nonterminal(prod) and (edge != None):
                    self.statement_kleene(edge)
    
    def statement(self, edges):
        productions = [self.ast[x][PARENT] for x in edges]
        if productions == ['<assignment_statement>']:
            # ['%id%', '<subscript>', '<assign_op>', '<expr>', ';']
            LHS_VAR, SUBS, ASSIGN_OP, RHS_EXPR = 0, 1, 2, 3
            statement_edges = edges[0]
            assignment_statement_edges = self.ast[statement_edges][PTR]
            rhs_expr_reg = self.expr(self.ast[self.ast[edges[0]][PTR][RHS_EXPR]][PTR])
            var_name = self.ast[self.ast[self.ast[edges[PARENT]][PTR][LHS_VAR]][PTR]][PARENT]
            var_offset = self.get_var_position_respect_to_sp(var_name)
            subscript_expr = self.subscript_reg(assignment_statement_edges[SUBS])
            assign_op = self.ast[self.ast[assignment_statement_edges[ASSIGN_OP]][PTR][0]][PARENT]
            if (assign_op == '%assign%'):
                pass # do nothing
            elif (assign_op == '%assign_inc%'):
                temp = self.get_vacant_temp()
                self.assembler_sections[self.current_section].append(f'\tlw {temp} {var_offset}($sp)\n')
                self.assembler_sections[self.current_section].append(f'\taddi {rhs_expr_reg} {temp} {rhs_expr_reg}\n')
                self.unoccupy_var_temp(temp)
            elif (assign_op == '%assign_dec%'):
                temp = self.get_vacant_temp()
                self.assembler_sections[self.current_section].append(f'\tlw {temp} {var_offset}($sp)\n')
                self.assembler_sections[self.current_section].append(f'\tsubi {rhs_expr_reg} {temp} {rhs_expr_reg}\n')
                self.unoccupy_var_temp(temp)
            self.assembler_sections[self.current_section].append(f'\tsw {rhs_expr_reg} {var_offset}($sp)\n')
            self.unoccupy_var_temp(rhs_expr_reg)
            
        elif productions == ['<method_call>', ';']:
            pass
        elif productions == ['if', '<expr>', '<block>', '<else_block>']:
            IF_KW, IF_EXPR, IF_BLOCK, ELSE_BLOCK = 0, 1, 2, 3
            if_expr_reg = self.expr(self.ast[edges[IF_EXPR]][PTR])
            if_tag, else_tag = next(tags_generator[IF_COND_TAG_GEN])
            self.assembler_sections[self.current_section].append(f'\t# if-else statement\n')
            self.assembler_sections[self.current_section].append(f'\t{if_tag}:\n')
            self.assembler_sections[self.current_section].append(f'\tbeq {if_expr_reg} $zero {else_tag}\n')
            self.block(edges[IF_BLOCK])
            self.assembler_sections[self.current_section].append(f'\t{else_tag}:\n')
            self.else_block(self.ast[edges[ELSE_BLOCK]][PTR])
        elif productions == ['for', '<for_eval>', '<block>']:
            pass
        elif productions == ['return', ';']:
            # jr with out $v1
            pass 
        elif productions == ['return', '<expr>', ';']:
            EXPR = 1
            r_expr = self.expr(self.ast[edges[EXPR]][PTR])
            self.assembler_sections[self.current_section].append(f'\tmove {r_expr} $v1\n')
            
        elif productions == ['break', ';']:
            pass
        elif productions == ['continue', ';']:
            pass
        elif productions == ['<block>']:
            self.block(edges[0])
        elif productions == ['<expr>', ';']:
            pass
        elif productions == ['<print>', ';']:
            VAR_POS, SUBS_POS = 1, 2 # 'print_var', '%id%', '<subscript>'
            p_edges = self.ast[edges[0]][PTR]
            var_name = self.ast[self.ast[p_edges[VAR_POS]][PTR]][PARENT]
            subs = self.subscript_reg(p_edges[SUBS_POS])
            var_reg = self.get_var_value_in_reg(var_name)
            self.assembler_sections[self.current_section].append(f'\t# print(register)\n')
            self.assembler_sections[self.current_section].append(f'\tli $v0, 1\n')
            self.assembler_sections[self.current_section].append(f'\tmove $a0, {var_reg}\n')
            self.assembler_sections[self.current_section].append(f'\tsyscall\n')
            self.assembler_sections[self.current_section].append(f'\t# print(str1)\n')
            self.assembler_sections[self.current_section].append(f'\tli $v0, 4\n')
            self.assembler_sections[self.current_section].append(f'\tla $a0, endl\n')
            self.assembler_sections[self.current_section].append(f'\tsyscall\n')
            self.unoccupy_var_temp(var_reg)
    
    def block(self, block_ptr):
        LCURLY, VAR_DECL, STATEMENTS, RCURLY = 0, 1, 2, 3
        block_edges = [self.ast[x] for x in self.ast[block_ptr][PTR]]

        self.opening_curly() # { 
        self.var_decl_kleene(block_edges[VAR_DECL][PTR]) # <var_decl*>
        self.statement_kleene(block_edges[STATEMENTS][PTR]) # <statement*>
        self.closing_curly() # }

    def else_block(self, else_block_edges):
        ELSE_KW, ELSE_BLOCK = 0, 1
        self.block(else_block_edges[ELSE_BLOCK])
    
    def subscript_reg(self, subscript_ptr):
        subs_edges = self.ast[subscript_ptr][PTR]
        if subs_edges:
            right_sb    = self.ast[subs_edges[0]][PARENT]
            offset_expr = self.expr(self.ast[subs_edges[1]][PTR])
            left__sb    = self.ast[subs_edges[2]][PARENT]
            return offset_expr
        else:
            return None

    def get_var_value_in_reg(self, var_name):
        var_offset = self.get_var_position_respect_to_sp(var_name)
        temp = self.get_vacant_temp()
        self.assembler_sections[self.current_section].append(f'\tlw {temp} {var_offset}($sp)\n')
        return temp
    
    def expr(self, edges):
        productions = [self.ast[x][PARENT] for x in edges]
        if (productions == ['%id%', '<subscript>']):
            var_name = self.ast[self.ast[edges[0]][PTR]][PARENT]
            var_offset = self.get_var_position_respect_to_sp(var_name)
            temp = self.get_vacant_temp()
            self.assembler_sections[self.current_section].append(f'\tlw {temp} {var_offset}($sp)\n')
            return temp
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
        elif (productions == ['%minus%', '<expr>']):
            right_expr_reg = self.expr(self.ast[edges[1]][PTR])
            self.assembler_sections[self.current_section].append(f'\tsub {right_expr_reg} $zero {right_expr_reg}\n')
            return right_expr_reg
        elif (productions == ['(', '!', '<expr>', ')']):
            right_expr_reg = self.expr(self.ast[edges[2]][PTR])
            self.assembler_sections[self.current_section].append(f'\tnor {right_expr_reg} {right_expr_reg} {right_expr_reg}\n')
            return right_expr_reg
        elif (productions == ['(', '<expr>', ')']):
            center_expr_reg = self.expr(self.ast[edges[1]][PTR])
            return center_expr_reg
        elif (productions == ['<expr>', '<bin_op>', '<expr>']) or (productions == ['(', '<expr>', '<bin_op>', '<expr>', ')']):
            if (productions == ['<expr>', '<bin_op>', '<expr>']):
                left_expr_reg   = self.expr(self.ast[edges[0]][PTR])
                bin_op_tup      = self.ast[self.ast[edges[1]][PTR][0]]
                right_expr_reg  = self.expr(self.ast[edges[2]][PTR])
            else:
                left_expr_reg   = self.expr(self.ast[edges[1]][PTR])
                bin_op_tup      = self.ast[self.ast[edges[2]][PTR][0]]
                right_expr_reg  = self.expr(self.ast[edges[3]][PTR])
            bin_op = str()
            if (bin_op_tup[PARENT] == '<arith_op>'):
                bin_op = self.ast[bin_op_tup[PTR][0]][PARENT]
                if (bin_op == '%plus%'): 
                    self.assembler_sections[self.current_section].append(f'\tadd {left_expr_reg} {left_expr_reg} {right_expr_reg}\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                elif (bin_op == '%minus%'): 
                    # ['sub']
                    self.assembler_sections[self.current_section].append(f'\tsub {left_expr_reg} {left_expr_reg} {right_expr_reg}\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                elif (bin_op == '%mult%'): 
                    # ['mult', 'mfhi', 'mflo'] get the lower register.
                    self.assembler_sections[self.current_section].append(f'\tmult {left_expr_reg} {right_expr_reg}\n')
                    self.assembler_sections[self.current_section].append(f'\tmflo {left_expr_reg}\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                elif (bin_op == '%div%'): 
                    # ['div', 'mflo'] integer div
                    self.assembler_sections[self.current_section].append(f'\tdiv {left_expr_reg} {right_expr_reg}\n')
                    self.assembler_sections[self.current_section].append(f'\tmflo {left_expr_reg}\n')
                    return left_expr_reg
                elif (bin_op == '%mod%'): 
                    # ['div', 'mfhi'] remainder reg
                    self.assembler_sections[self.current_section].append(f'\tdiv {left_expr_reg} {right_expr_reg}\n')
                    self.assembler_sections[self.current_section].append(f'\tmfhi {left_expr_reg}\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                else:
                    self.std_error(f'unrecognized operator for <expr> {bin_op}')
            elif (bin_op_tup[PARENT] == '%rel_op%'):
                # '%rel_op%': "<|>|(<·=)|(>·=)"
                symbol = self.ast[bin_op_tup[PTR]][PARENT]
                if (symbol == '<'):
                    self.assembler_sections[self.current_section].append(f'\tslt {left_expr_reg} {left_expr_reg} {right_expr_reg}\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                elif (symbol == '>'):
                    self.assembler_sections[self.current_section].append(f'\tslt {left_expr_reg} {right_expr_reg} {left_expr_reg}\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                elif (symbol == '<='):
                    true_tag, fin_cond = next(tags_generator[LESS_THAN_OR_EQUAL_TAG_GEN])
                    self.assembler_sections[self.current_section].append(f'\tblt {left_expr_reg} {right_expr_reg} {true_tag}\n')
                    self.assembler_sections[self.current_section].append(f'\tbeq {left_expr_reg} {right_expr_reg} {true_tag}\n')
                    self.assembler_sections[self.current_section].append(f'\tli {left_expr_reg} 0 # false\n')
                    self.assembler_sections[self.current_section].append(f'\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{true_tag}:\n')
                    self.assembler_sections[self.current_section].append(f'\t\tli {left_expr_reg} 1 # true\n')
                    self.assembler_sections[self.current_section].append(f'\t\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{fin_cond}:\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                elif (symbol == '>='):
                    true_tag, fin_cond = next(tags_generator[GREATER_THAN_OR_EQUAL_TAG_GEN])
                    self.assembler_sections[self.current_section].append(f'\tbgt {left_expr_reg} {right_expr_reg} {true_tag}\n')
                    self.assembler_sections[self.current_section].append(f'\tbeq {left_expr_reg} {right_expr_reg} {true_tag}\n')
                    self.assembler_sections[self.current_section].append(f'\tli {left_expr_reg} 0 # false\n')
                    self.assembler_sections[self.current_section].append(f'\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{true_tag}:\n')
                    self.assembler_sections[self.current_section].append(f'\t\tli {left_expr_reg} 1 # true\n')
                    self.assembler_sections[self.current_section].append(f'\t\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{fin_cond}:\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
            elif (bin_op_tup[PARENT] == '%eq_op%'):
                symbol = self.ast[bin_op_tup[PTR]][PARENT]
                if (symbol == '=='):
                    true_tag, fin_cond = next(tags_generator[EQUAL_TAG_GEN])
                    self.assembler_sections[self.current_section].append(f'\tbeq {left_expr_reg} {right_expr_reg} {true_tag}\n')
                    self.assembler_sections[self.current_section].append(f'\tli {left_expr_reg} 0 # false\n')
                    self.assembler_sections[self.current_section].append(f'\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{true_tag}:\n')
                    self.assembler_sections[self.current_section].append(f'\t\tli {left_expr_reg} 1 # true\n')
                    self.assembler_sections[self.current_section].append(f'\t\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{fin_cond}:\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                elif (symbol == '!='):
                    true_tag, fin_cond = next(tags_generator[NOT_EQUAL_TAG_GEN])
                    self.assembler_sections[self.current_section].append(f'\tbne {left_expr_reg} {right_expr_reg} {true_tag}\n')
                    self.assembler_sections[self.current_section].append(f'\tli {left_expr_reg} 0 # false\n')
                    self.assembler_sections[self.current_section].append(f'\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{true_tag}:\n')
                    self.assembler_sections[self.current_section].append(f'\t\tli {left_expr_reg} 1 # true\n')
                    self.assembler_sections[self.current_section].append(f'\t\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{fin_cond}:\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
            elif (bin_op_tup[PARENT] == '%cond_op%'):
                # '%cond_op%': "&·&|\\|·\\|"
                symbol = self.ast[bin_op_tup[PTR]][PARENT]
                if (symbol == '&&'):
                    false_tag, fin_cond = next(tags_generator[AND_TAG_GEN])
                    self.assembler_sections[self.current_section].apend(f'\tbeq {left_expr_reg} $zero {false_tag}\n')
                    self.assembler_sections[self.current_section].apend(f'\tbeq {right_expr_reg} $zero {false_tag}\n')
                    self.assembler_sections[self.current_section].apend(f'\t# true\n')
                    self.assembler_sections[self.current_section].apend(f'\tli {left_expr_reg} 1\n')
                    self.assembler_sections[self.current_section].apend(f'\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].apend(f'\t{false_tag}:\n')
                    self.assembler_sections[self.current_section].apend(f'\t\tli {left_expr_reg} 0\n')
                    self.assembler_sections[self.current_section].apend(f'\t\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].apend(f'\t{fin_cond}:')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
                elif (symbol == '||'):
                    true_tag, fin_cond = next(tags_generator[OR_TAG_GEN])
                    self.assembler_sections[self.current_section].append(f'\tbne {left_expr_reg} $zero {true_tag}\n')
                    self.assembler_sections[self.current_section].append(f'\tbne {right_expr_reg} $zero {true_tag}\n')
                    self.assembler_sections[self.current_section].append(f'\t# false\n')
                    self.assembler_sections[self.current_section].append(f'\tli {left_expr_reg} 0\n')
                    self.assembler_sections[self.current_section].append(f'\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{true_tag}:\n')
                    self.assembler_sections[self.current_section].append(f'\t\tli {left_expr_reg} 1\n')
                    self.assembler_sections[self.current_section].append(f'\t\tj {fin_cond}\n')
                    self.assembler_sections[self.current_section].append(f'\t{fin_cond}:\n')
                    self.unoccupy_var_temp(right_expr_reg)
                    return left_expr_reg
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
        stack_offset = 0
        if self.scope_stack[self.scope_index].get(var_name):
            return self.scope_stack[self.scope_index][var_name]
        else:
            index = self.scope_index
            while index >= 0:
                if self.scope_stack[index].get(var_name):
                    return self.scope_stack[index][var_name]
                index -= 1
            self.std_error(f'{var_name} was not found in current scope nor in any previous scope.')
    
    def get_var_position_respect_to_sp(self, var_name):
        stack_offset = 0
        if self.scope_stack[self.scope_index].get(var_name):
            return (abs(self.scope_stack[self.scope_index][var_name][SP_POS]) + stack_offset)
        else:
            index = self.scope_index
            while index >= 0:
                if self.scope_stack[index].get(var_name):
                    return (abs(self.scope_stack[index][var_name][SP_POS]) + stack_offset)
                stack_offset += self.scope_space[index]
                index -= 1
            self.std_error(f'{var_name} was not found in current scope nor in any previous scope.')
    
    def get_vacant_temp(self):
        if len(temp_reg[VACANT]):
            popped = temp_reg[VACANT].pop()
            temp_reg[OCCUPIED].add(popped)
            return popped
        else:
            print(f"Codegen error: not enough registers to compute operation {temp_reg}")
    
    def unoccupy_var_temp(self, reg):
        temp_reg[OCCUPIED].remove(reg)
        temp_reg[VACANT].add(reg)
    
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
c = codegen(s)
