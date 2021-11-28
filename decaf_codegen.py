from yaml import load
from decaf_scanner import scanner
from decaf_parser import lr_0, lr_0_t, parser, is_nonterminal, PARENT, PTR, CHILDREN
from decaf_semantic import semantic
import sys

DEBUG = False

# GLOBAL VARIABLES
mem_space = {'int':4, 'boolean': 1, 'class': 0, 'void': 0}
VAR_TYPE, IS_ALLOCATED, SP_OFFSET, IS_ARGUMENT = 0, 1, 2, 3

CALLEE_BEGINING, CALLEE_ENDING = 0, 1
CALLEE_OFFSET = 40
MAIN_TAG = 'main'
FINISH_TAG = 'fin'
bool_dict = {'true':'1', 'false':'0'}

def tag_gen_with_name(name:list):
    i = 0
    while True:
        if len(name) > 1:
            yield [f'T_{i}_{n}' for n in name]
        elif len(name) == 1:
            yield f'T_{i}_{name[0]}'
        else:
            codegen_std_error(f'name={name} is empty or invalid')
        i += 1

def tag_gen_for_dot_data():
    i = 0
    while True:
        yield f'D_{i}'
        i += 1
IF, CALLEE_ENDER_TAG, FOR = 'if', 'callee_ender', 'for'
tags_generator = {
    '=='                : tag_gen_with_name(['eq_false', 'eq_fin']),
    '!='                : tag_gen_with_name(['neq_false', 'neq_fin']),
    '<'                 : tag_gen_with_name(['lt_false', 'lt_fin']),
    '>'                 : tag_gen_with_name(['gt_false', 'gt_fin']),
    '<='                : tag_gen_with_name(['lte_false', 'lte_fin']),
    '>='                : tag_gen_with_name(['bte_false', 'bte_fin']),
    '&&'                : tag_gen_with_name(['and_false', 'and_fin']),
    '||'                : tag_gen_with_name(['or_true', 'or_fin']),
    IF                  : tag_gen_with_name(['if_false']),
    CALLEE_ENDER_TAG    : tag_gen_with_name(['calle_ender']),
    FOR                 : tag_gen_with_name(['for_begin', 'for_end'])
}

intended_print = print
intended_exit = exit

OCCUPIED, VACANT = 'OCCUPIED', 'VACANT'
temp_reg_dict = {
    VACANT: {'$t0', '$t1', '$t2', '$t3', '$t4', '$t5', '$t6', '$t7'},
    OCCUPIED: set()
}

def codegen_std_error(str):
    intended_print(f'Codegen error: {str} .', end='')
    intended_print(f'In method {sys._getframe(1).f_code.co_name}.')
    intended_exit(-1)

def codegen_std_warning(str):
    intended_print(f'Codegen warning: {str}.')

def instruction(instruction, tabs=1):
    return (('\t'*tabs) + f"{instruction}\n")

def occupy_temp_reg():
    if len(temp_reg_dict[VACANT]):
        popped = temp_reg_dict[VACANT].pop()
        temp_reg_dict[OCCUPIED].add(popped)
        return popped
    else:
        codegen_std_error(f"not enough registers to compute operation {temp_reg_dict}")

def unoccupy_temp_reg(reg):
    if reg in temp_reg_dict[OCCUPIED]:
        temp_reg_dict[OCCUPIED].remove(reg)
        temp_reg_dict[VACANT].add(reg)
    else:
        codegen_std_error(f"did not find {reg} in temp_reg_dict[OCCUPIED]")

def method_name_gen(method_name):
    if method_name != 'main':
        return f'method_{method_name}'
    else:
        return method_name
    
class codegen:
    def __init__(self, assembled_semantic:semantic, executable_filename='a.asm', debug=False):
        # previous globals
        self.dot_data                   = [instruction(f'.data', tabs=0)]
        self.dot_data_tag_gen           = tag_gen_for_dot_data()
        self.debug                      = debug
        self.tag_calle_ender            = None
        # attr
        self.for_break                  = None
        self.for_begin                  = None
        self.executable_filename        = executable_filename
        self.ast                        = assembled_semantic.ast
        self.ast_head                   = assembled_semantic.ast_head
        self.scope_stack                = list()
        self.scope_space                = dict()
        self.assembler_sections         = list()
        self.main_section               = list()
        """IF THE FUNCTION TAKES IN NO ARGUMENTS THEN IT WILL NOT APPEAR IN THE METHOD_ARGUMENTS DICTIONARY """
        self.method_arguments           = dict()
        self.method_return_types        = dict()
        self.callee_actions_performed   = dict()
        self.stack_ptr                  = 0
        self.var_type                   = None
        self.current_method             = 'main'
        self.method_offset              = 0
        self.field_decl_offset          = 0
        self.var_decl_offset            = 0
        self.initiate()
    
    def append_instructions(self, current_method, instructions):
        if (current_method == 'main'):
            self.main_section += instructions
        else:
            self.assembler_sections[-1] += instructions
    
    def write_executable(self):
        with open(self.executable_filename, mode='w+') as file:
            file.truncate(0)
            file.writelines(self.dot_data)
            file.writelines(self.main_section)
            for section in self.assembler_sections:
                file.writelines(section)
            file.close()
        intended_print("Compiled Successfully")
    
    def get_pseudo_terminal_value(self, id_ptr):
        return self.ast[self.ast[id_ptr][PTR]][PARENT]

    def get_subscript_val(self, subs_ptr):
        """CAN BE NULL"""
        if self.ast[subs_ptr][PTR] != None:
            SQUARE_BRACE_LEFT_POS, INT_LITERAL_POS, SQUARE_BRACE_RIGHT_POS = 0, 1, 2
            children = self.ast[subs_ptr][CHILDREN]
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == ['[', '%int_literal%', ']']):
                int_literal_value = self.get_pseudo_terminal_value(children[INT_LITERAL_POS])
                return int_literal_value
            else:
                codegen_std_error(f'get_subscript_val did not find a production like {productions}')
        else:
            return None
        
    def add_space_to_scope(self, var_type):
        if self.scope_space.get((len(self.scope_stack) - 1)):
            self.scope_space[(len(self.scope_stack) - 1)] += abs(mem_space[var_type])
        else:
            self.scope_space[(len(self.scope_stack) - 1)] = abs(mem_space[var_type])

    def check_for_warnings(self):
        if len(temp_reg_dict[OCCUPIED]) != 0: 
            codegen_std_warning(f'temp_reg_dict is not empty {temp_reg_dict[OCCUPIED]} was never unoccupied')

    def initiate(self):
        # global scope that is not activated by opening_curly
        self.scope_stack.append({})
        self.scope_space[len(self.scope_stack)-1] = 0
        # main_section starting
        self.main_section += [instruction(f'.globl main', 0), instruction(f'{MAIN_TAG}:', 0)]
        self.callee_header_main()
        self.assembler_sections.append([])
        self.traverse([self.ast_head])
        self.callee_ender_main()
        self.dot_data += [instruction(f'.text', tabs=0)]
        self.check_for_warnings()
        self.write_executable()

    def traverse(self, list_node_i):
        for node_index in list_node_i:
            prod, children = self.ast[node_index]
            if (prod == '<program">'):
                self.program_dash_handler(children)
                continue
            # simply pass the next recursive call with the parameters
            if is_nonterminal(prod) and (children != None):
                self.traverse(children)
    
    def program_dash_handler(self, children):
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == ['class', '%id%', '{', '<field_decl*>', '<method_decl*>', '}']):
                FIELD_DECL_POS, METHOD_DECL_POS = 3, 4
                self.opening_curly()
                self.field_decl_handler(children[FIELD_DECL_POS])
                self.method_decl_handler(children[METHOD_DECL_POS])
                self.closing_curly()
            elif (productions == ['class', '%id%', '{', '<field_decl*>', '}']):
                FIELD_DECL_POS = 3
                self.opening_curly()
                self.field_decl_handler(children[FIELD_DECL_POS])
                self.closing_curly()
            elif (productions == ['class', '%id%', '{', '<method_decl*>', '}']):
                METHOD_DECL_POS = 3
                self.opening_curly()
                self.method_decl_handler(children[METHOD_DECL_POS])
                self.closing_curly()
            elif (productions == ['class', '%id%', '{', '}']):
                self.opening_curly()
                self.closing_curly()
                pass # the codegen is nothing? maybe just main with the termination
            else:
                codegen_std_error(f'program_dash did not find a productions template like {productions}')
    
    def block(self, children):
        """CANNOT BE NULL"""
        if children == None: codegen_std_error(f'children cannot be null in block.')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['{', '<var_decl*>', '<statement*>', '}']):
            LEFT_CURLY_POS, VAR_DECL_KLEENE_POS, STATEMENT_KLEENE_POS, RIGHT_CURLY_POS = 0, 1, 2, 3
            # '{'
            self.opening_curly()
            # '<var_decl*>'
            self.var_decl_offset = 0 # to define the scope
            var_decl_kleene_children = self.ast[children[VAR_DECL_KLEENE_POS]][CHILDREN]
            self.var_decl_kleene(var_decl_kleene_children)
            # '<statement*>'
            statement_kleene_children = self.ast[children[STATEMENT_KLEENE_POS]][CHILDREN]
            self.statement_kleene(statement_kleene_children)
            # '}'
            self.closing_curly()
        else:
            codegen_std_error(f'no production like {productions} found in block')
    
    def var_decl_kleene(self, children):
        """CAN BE NULL"""
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == ['<var_decl>', '<var_decl*>']):
                VAR_DECL_POS, VAR_DECL_KLEENE_POS = 0, 1
                var_decl_children = self.ast[children[VAR_DECL_POS]][CHILDREN]
                self.var_decl(var_decl_children)
                var_decl_kleene_children = self.ast[children[VAR_DECL_KLEENE_POS]][CHILDREN]
                self.var_decl_kleene(var_decl_kleene_children)
            else:
                codegen_std_error(f'var_decl_kleene did not recognize any production like {productions}')
    
    def var_decl(self, children):
        """CANNOT BE NULL"""
        if children == None: codegen_std_error(f'children cannot be null in var_decl')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['%type%', '%id%', '<args_list>', ';']):
            VAR_TYPE_POS, ID_POS, ARGS_LIST_POS = 0, 1, 2
            self.var_type = self.get_pseudo_terminal_value(children[VAR_TYPE_POS])
            var_name = self.get_pseudo_terminal_value(children[ID_POS])
            self.add_var_to_scope(var_name, self.var_type, has_been_allocated=False, stack_pointer_offset=self.var_decl_offset, is_argument=False)
            self.var_decl_offset += abs(mem_space[self.var_type]) # increment the offset
            args_list_children = self.ast[children[ARGS_LIST_POS]][CHILDREN]
            self.args_list(args_list_children)
        else:
            codegen_std_error(f'var_decl did not find any production like {productions}')

    def args_list(self, children):
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == [',', '%id%', '<args_list>']):
                ID_POS, ARGS_LIST_POS = 1, 2
                var_name = self.get_pseudo_terminal_value(children[ID_POS])
                self.add_var_to_scope(var_name, self.var_type, has_been_allocated=False, stack_pointer_offset=None, is_argument=False)
                args_list_children = self.ast[children[ARGS_LIST_POS]][CHILDREN]
                self.args_list(args_list_children)
            else:
                codegen_std_error(f'args_list did not find any production like {productions}')

    def statement_kleene(self, children):
        """CAN BE NULL"""
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == ['<statement>', '<statement*>']):
                STATEMENT_POS, STATEMENT_KLEENE_POS = 0, 1
                statement_children = self.ast[children[STATEMENT_POS]][CHILDREN]
                self.statement(statement_children)
                statement_kleene_children = self.ast[children[STATEMENT_KLEENE_POS]][CHILDREN]
                self.statement_kleene(statement_kleene_children)
            else:
                codegen_std_error(f'statement_kleene did not recognize production {productions}')

    def statement(self, children):
        """CANNOT BE NULL"""
        if children == None: codegen_std_error(f'chidren cannot be null in statent')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['<assignment_statement>']):
            ASSIGNMENT_STATEMENT_POS = 0
            assignment_statement_children = self.ast[children[ASSIGNMENT_STATEMENT_POS]][CHILDREN]
            self.assignment_statement(assignment_statement_children)
        elif (productions == ['<method_call>', ';']):
            METHOD_CALL_POS = 0
            method_call_children = self.ast[children[METHOD_CALL_POS]][CHILDREN]
            self.method_call(method_call_children)
        elif (productions == ['if', '<expr>', '<block>', '<else_block>']):
            IF_POS, EXPR_POS, BLOCK_POS, ELSE_BLOCK_POS = 0, 1, 2, 3
            # 'if'
            pass
            # '<expr>'
            expr_children = self.ast[children[EXPR_POS]][CHILDREN]
            expr_reg = self.expr(expr_children)
            if_false_tag = next(tags_generator[IF])
            self.append_instructions(self.current_method, [
                instruction(f'# if {expr_reg} ?'),
                instruction(f'beq {expr_reg} $zero {if_false_tag}'),
            ])
            unoccupy_temp_reg(expr_reg)
            # '<block>'
            block_children = self.ast[children[BLOCK_POS]][CHILDREN]
            self.block(block_children)
            # '<else_block>'
            self.append_instructions(self.current_method, [
                instruction(f'# else or end_if'),
                instruction(f'{if_false_tag}:')
            ])
            else_block_children = self.ast[children[ELSE_BLOCK_POS]][CHILDREN]
            self.else_block(else_block_children)
            
        elif (productions == ['for', '(', '<assignment_statement>', '<expr>', ';', '<assignment_statement>', ')', '<block>']):
            FOR_POS, INIT_ASSIGNMENT_STATEMENT_POS, BREAK_EXPR_POS, UPDATE_ASSIGNMENT_STATEMENT_POS, FOR_BLOCK_POS = 0, 2, 3, 5, 7
            self.append_instructions(self.current_method, [
                instruction(f'# for loop'),
                instruction(f'# for init asignment statement')
            ])
            # '<assignment_statement>'
            init_assignment_statement_children = self.ast[children[INIT_ASSIGNMENT_STATEMENT_POS]][CHILDREN]
            self.assignment_statement(init_assignment_statement_children)
            self.for_begin, self.for_break = next(tags_generator[FOR])
            self.append_instructions(self.current_method, [
                instruction(f'{self.for_begin}:')
            ])
            # '<expr>'
            expr_children = self.ast[children[BREAK_EXPR_POS]][CHILDREN]
            expr_reg = self.expr(expr_children)
            self.append_instructions(self.current_method, [
                instruction(f'beq {expr_reg} $zero {self.for_break}')
            ])
            unoccupy_temp_reg(expr_reg)
            # '<block>'
            block_children = self.ast[children[FOR_BLOCK_POS]][CHILDREN]
            self.block(block_children)
            # '<assignment_statement>'
            update_assignment_statement_children = self.ast[children[UPDATE_ASSIGNMENT_STATEMENT_POS]][CHILDREN]
            self.assignment_statement(update_assignment_statement_children)
            self.append_instructions(self.current_method, [
                instruction(f'j {self.for_begin}'),
                instruction(f'{self.for_break}:')
            ])
        elif (productions == ['return', ';']):
            # 'return'
            self.append_instructions(self.current_method, [
                instruction(f'j {self.tag_calle_ender}')
            ])
        elif (productions == ['return', '<expr>', ';']):
            EXPR_POS = 1
            # 'return'
            # '<expr>'
            expr_children = self.ast[children[EXPR_POS]][CHILDREN]
            expr_reg = self.expr(expr_children)
            self.append_instructions(self.current_method, [
                instruction(f'move {expr_reg} $v0 # return expr'),
                instruction(f'j {self.tag_calle_ender}')
            ])
            # ';'
            unoccupy_temp_reg(expr_reg)
        elif (productions == ['break', ';']):
            self.append_instructions(self.current_method, [
                instruction(f'j {self.for_break}')
            ])
        elif (productions == ['continue', ';']):
            self.append_instructions(self.current_method, [
                instruction(f'j {self.for_begin}')
            ])
        elif (productions == ['<block>']):
            BLOCK_POS = 0
            block_children = self.ast[children[BLOCK_POS]][CHILDREN]
            self.block(block_children)
        elif (productions == ['<expr>', ';']):
            EXPR_POS = 0
            expr_children = self.ast[children[EXPR_POS]][CHILDREN]
            expr_reg = self.expr(expr_children)
        elif (productions == ['<print_var>', ';']):
            PRINT_VAR_POS = 0
            print_var_children = self.ast[children[PRINT_VAR_POS]][CHILDREN]
            self.print_var(print_var_children)
        elif (productions == ['<print_str>', ';']):
            PRINT_STR_POS = 0
            print_str_children = self.ast[children[PRINT_STR_POS]][CHILDREN]
            self.print_str(print_str_children)
        else:
            codegen_std_error(f'statement not recognized {productions}')

    def else_block(self, children):
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == ['else', '<block>']):
                ELSE_POS, BLOCK_POS = 0, 1
                block_children = self.ast[children[BLOCK_POS]][CHILDREN]
                self.block(block_children)
            else:
                codegen_std_error(f'production like {productions} not recognized')
            
    def print_str(self, children):
        if children == None: codegen_std_error(f'children cannot be null in print_str')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['print_str', '(', '<string_literal>', ')']):
            PRINT_STR_POS, STRING_LITERAL_POS = 0, 2
            string_literal = self.get_pseudo_terminal_value(self.ast[children[STRING_LITERAL_POS]][CHILDREN][0])
            tag_dot_data = next(self.dot_data_tag_gen)
            self.dot_data += [
                instruction(f'{tag_dot_data}: .asciiz {string_literal}')
            ]
            self.append_instructions(self.current_method, [
                instruction(f'# print str'),
                instruction(f'li $v0, 4'),
                instruction(f'la $a0, {tag_dot_data}'),
                instruction(f'syscall')
            ])
        else:
            codegen_std_error(f'no production like {productions} in print_str')

    def method_call(self, children):
        """CANNOT BE NULL"""
        if children == None: codegen_std_error(f'method_call_children cannot be null in method_call')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['%id%', '(', ')']):
            ID_POS = 0
            # no allocation of the arguments
            method_name = method_name_gen(self.get_pseudo_terminal_value(children[ID_POS]))
            self.append_instructions(self.current_method, [
                instruction(f'# begin method_call to {method_name}'),
                instruction(f'move $t0 $s0'),
                instruction(f'move $t1 $s1'),
                instruction(f'move $t2 $s2'),
                instruction(f'move $t3 $s3'),
                instruction(f'move $t4 $s4'),
                instruction(f'move $t5 $s5'),
                instruction(f'move $t6 $s6'),
                instruction(f'move $t7 $s7'),
                instruction(f'# no arguments alloc'),
                instruction(f'jal {method_name}'),
                instruction(f'# no arguments dealloc'),
                instruction(f'move $s0 $t0'),
                instruction(f'move $s1 $t1'),
                instruction(f'move $s2 $t2'),
                instruction(f'move $s3 $t3'),
                instruction(f'move $s4 $t4'),
                instruction(f'move $s5 $t5'),
                instruction(f'move $s6 $t6'),
                instruction(f'move $s7 $t7'),
                instruction(f'# end of method_call to {method_name}'),
            ])
        elif (productions == ['%id%', '(', '<comma_expr>', ')']):
            ID_POS, COMMA_EXPR = 0, 2
            # no allocation of the arguments
            method_name = method_name_gen(self.get_pseudo_terminal_value(children[ID_POS]))
            arg_space_alloc = sum([mem_space[x[VAR_TYPE]] for x in self.method_arguments[method_name].values()])
            arg_names = '# '+''.join([f'{arg_attr[VAR_TYPE]} {arg_name} {arg_attr[SP_OFFSET]}($sp) ' for arg_name, arg_attr in self.method_arguments[method_name].items()])
            self.append_instructions(self.current_method, [
                instruction(f'# begin method_call to {method_name}'),
                instruction(f'move $t0 $s0'),
                instruction(f'move $t1 $s1'),
                instruction(f'move $t2 $s2'),
                instruction(f'move $t3 $s3'),
                instruction(f'move $t4 $s4'),
                instruction(f'move $t5 $s5'),
                instruction(f'move $t6 $s6'),
                instruction(f'move $t7 $s7'),
                instruction(f'# arguments {arg_names} alloc'),
                instruction(f'addi $sp $sp -{arg_space_alloc}')
            ])
            self.append_instructions(self.current_method, [
                instruction(f'jal {method_name}'),
                instruction(f'# arguments {arg_names} dealloc'),
                instruction(f'addi $sp $sp {arg_space_alloc}'),
                instruction(f'move $s0 $t0'),
                instruction(f'move $s1 $t1'),
                instruction(f'move $s2 $t2'),
                instruction(f'move $s3 $t3'),
                instruction(f'move $s4 $t4'),
                instruction(f'move $s5 $t5'),
                instruction(f'move $s6 $t6'),
                instruction(f'move $s7 $t7'),
                instruction(f'# end of method_call to {method_name}'),
            ])
        elif (productions == ['callout', '(', '<string_literal>',  ')']):
            # no se que es esto
            pass
        elif (productions == ['callout', '(', '<string_literal>', ',', '<callout_arg">', ')']):
            # no se que es esto
            pass
        else:
            codegen_std_error(f'did not find production like {productions} in method_call')

    def get_var_reg(self, var_name):
        var_attr, variable_offset = self.get_var(var_name)
        temp = occupy_temp_reg()
        load_operation = 'lw' if var_attr[VAR_TYPE] == 'int' else 'lb'
        self.append_instructions(self.current_method, [
            instruction(f'{load_operation} {temp} {variable_offset}($sp)')
        ])
        return temp

    def print_var(self, children):
        if children == None: codegen_std_error(f'children cannot be null in print_var')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['print_var', '(', '%id%', '<subscript>', ')']):
            PRINT_VAR_POS, ID_POS, SUBSCRIPT_POS = 0, 2, 3
            # 'print_var'
            pass
            # '%id%'
            var_name = self.get_pseudo_terminal_value(children[ID_POS])
            var_reg = self.get_var_reg(var_name)
            # '<subscript>'
            int_subscript = self.get_subscript_val(children[SUBSCRIPT_POS])
            self.append_instructions(self.current_method, [
                instruction(f'# print register/var'),
                instruction(f'li $v0, 1'),
                instruction(f'move $a0, {var_reg}'),
                instruction(f'syscall'),
            ])
            unoccupy_temp_reg(var_reg)
        else:
            codegen_std_error(f'no production like {productions} found for print_var')
            
    def assignment_statement(self, children):
        """CANNOT BE NULL"""
        if children == None: codegen_std_error(f'children cannot be null in assignment statement')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['%id%', '<subscript>', '<assign_op>', '<expr>', ';']):
            ID_POS, SUBSCRIPT_POS, ASSIGN_OP_POS, EXPR_POS = 0, 1, 2, 3
            var_name = self.get_pseudo_terminal_value(children[ID_POS])
            var_attr, variable_offset = self.get_var(var_name)
            int_literal_subscript_value = self.get_subscript_val(children[SUBSCRIPT_POS])
            assign_op = self.ast[self.ast[children[ASSIGN_OP_POS]][CHILDREN][0]][PARENT]
            expr_children = self.ast[children[EXPR_POS]][CHILDREN]
            expr_reg = self.expr(expr_children)
            if assign_op == '%assign%':
                load_operation = 'lw' if var_attr[VAR_TYPE] == 'int' else 'lb'
                store_operation = 'sw' if var_attr[VAR_TYPE] == 'int' else 'sb'
                temp = occupy_temp_reg()
                self.append_instructions(self.current_method, [
                    instruction(f'# {assign_op} statement to {var_name}'),
                    instruction(f'{store_operation} {expr_reg} {variable_offset}($sp) # returning {var_name}')
                ])
                unoccupy_temp_reg(temp)
                unoccupy_temp_reg(expr_reg)

            elif assign_op == '%assign_inc%':
                load_operation = 'lw' if var_attr[VAR_TYPE] == 'int' else 'lb'
                store_operation = 'sw' if var_attr[VAR_TYPE] == 'int' else 'sb'
                temp = occupy_temp_reg()
                self.append_instructions(self.current_method, [
                    instruction(f'# {assign_op} statement to {var_name}'),
                    instruction(f'{load_operation} {temp} {variable_offset}($sp) # fetching {var_name}'),
                    instruction(f'add {temp} {temp} {expr_reg}'),
                    instruction(f'{store_operation} {temp} {variable_offset}($sp) # returning {var_name}')
                ])
                unoccupy_temp_reg(temp)
                unoccupy_temp_reg(expr_reg)
            elif assign_op == '%assign_dec%':
                load_operation = 'lw' if var_attr[VAR_TYPE] == 'int' else 'lb'
                store_operation = 'sw' if var_attr[VAR_TYPE] == 'int' else 'sb'
                temp = occupy_temp_reg()
                self.append_instructions(self.current_method, [
                    instruction(f'# {assign_op} statement to {var_name}'),
                    instruction(f'{load_operation} {temp} {variable_offset}($sp) # fetching {var_name}'),
                    instruction(f'sub {temp} {temp} {expr_reg}'),
                    instruction(f'{store_operation} {temp} {variable_offset}($sp) # returning {var_name}')
                ])
                unoccupy_temp_reg(temp)
                unoccupy_temp_reg(expr_reg)
            else:
                codegen_std_error(f'assign_op {assign_op} not recognized')
        else:
            codegen_std_error(f'production {productions} not recognized in assignment_statement')
        
    def get_var(self, var_name):
        index = len(self.scope_stack) - 1
        scope_offset = 0
        while (index != 0):
            if self.scope_stack[index].get(var_name):
                offset = self.scope_stack[index][var_name][SP_OFFSET] + scope_offset
                t = (self.scope_stack[index][var_name], offset) # var attributes & the scope in which it was found
                return t
            scope_offset += abs(self.scope_space[index])
            index -= 1
        if self.method_arguments[self.current_method].get(var_name):
            offset = self.method_arguments[self.current_method][var_name][SP_OFFSET]
            offset += CALLEE_OFFSET
            offset += self.scope_space[len(self.scope_stack)-1]
            t = (self.method_arguments[self.current_method][var_name], offset)
            return t
        codegen_std_error(f'variable name "{var_name}" was not found in scope')
        
    def expr(self, children) -> str:
        """CANNOT BE NULL"""
        if children == None: codegen_std_error(f'children cannot be null in expression')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['%id%', '<subscript>']):
            VAR_POS, SUBSCRIPT_POS = 0, 1
            var_name = self.get_pseudo_terminal_value(children[VAR_POS])
            subscript_literal = self.get_subscript_val(children[SUBSCRIPT_POS])
            var_attr, variable_offset = self.get_var(var_name)
            temp = occupy_temp_reg()
            load_operation = 'lw' if var_attr[VAR_TYPE] == 'int' else 'lb'
            self.append_instructions(self.current_method, [instruction(f'{load_operation} {temp} {variable_offset}($sp) # <expr>::id {var_name} r-value id')])
            return temp
        elif (productions == ['<literal>']):
            LITERAL_POS = 0
            literal_children = self.ast[children[LITERAL_POS]][CHILDREN]
            literal_reg = self.literal(literal_children)
            return literal_reg
        elif (productions == ['%minus%', '<expr>']):
            MINUS_SIGN_POS, EXPR_POS = 0, 1
            expr_children = self.ast[children[EXPR_POS]][CHILDREN]
            expr_reg = self.expr(expr_children)
            self.append_instructions(self.current_method, [
                instruction(f'sub {expr_reg} $zero {expr_reg} # - <expr>')
            ])
            return expr_reg
        elif (productions == ['(', '!', '<expr>', ')']):
            INTERROGATION_SIGN_POS, EXPR_POS = 1, 2
            expr_children = self.ast[children[EXPR_POS]][CHILDREN]
            expr_reg = self.expr(expr_children)
            self.append_instructions(self.current_method, [
                instruction(f'nor {expr_reg} {expr_reg} {expr_reg} # ! <expr>')
            ])
            return expr_reg
        elif (productions == ['(', '<expr>', ')']):
            EXPR_POS = 1
            expr_children = self.ast[children[EXPR_POS]][CHILDREN]
            expr_reg = self.expr(expr_children)
            return expr_reg
        elif ((productions == ['(', '<expr>', '<bin_op>', '<expr>', ')']) or (productions == ['<expr>', '<bin_op>', '<expr>'])):
            if (productions == ['(', '<expr>', '<bin_op>', '<expr>', ')']):
                LEFT_EXPR, BIN_OP, RIGHT_EXPR = 1, 2, 3
            elif (productions == ['<expr>', '<bin_op>', '<expr>']):
                LEFT_EXPR, BIN_OP, RIGHT_EXPR = 0, 1, 2
            else:
                codegen_std_error(f'error in <expr> <bin_op> <expr>')
            left_expr_children = self.ast[children[LEFT_EXPR]][CHILDREN]
            left_expr = self.expr(left_expr_children)
            bin_op_parent = self.ast[self.ast[children[BIN_OP]][PTR][0]][PARENT]
            bin_op_ptr = self.ast[children[BIN_OP]][PTR][0]
            right_expr_children = self.ast[children[RIGHT_EXPR]][CHILDREN]
            right_expr = self.expr(right_expr_children)
            if (bin_op_parent == '<arith_op>'):
                symbol = self.get_pseudo_terminal_value(self.ast[bin_op_ptr][PTR][0])
                if (symbol == '+'):
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'add {left_expr} {left_expr} {right_expr}')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                elif (symbol == '-'):
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'sub {left_expr} {left_expr} {right_expr}')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                elif (symbol == '*'):
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'mult {left_expr} {right_expr}'),
                        instruction(f'mflo {left_expr}')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                elif (symbol == '/'):
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'div {left_expr} {right_expr}'),
                        instruction(f'mflo {left_expr}')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                elif (symbol == '%'):
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'div {left_expr} {right_expr}'),
                        instruction(f'mfhi {left_expr}')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                else:
                    codegen_std_error(f'no symbol found in <expr>::<arith_op> {symbol}')
            elif (bin_op_parent == '%rel_op%'):
                symbol = self.get_pseudo_terminal_value(bin_op_ptr)
                if (symbol == '<'):
                    lt_false, lt_fin = next(tags_generator[symbol])
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'bgt {left_expr} {right_expr} {lt_false}'),
                        instruction(f'beq {left_expr} {right_expr} {lt_false}'),
                        instruction(f'li {left_expr} 1', tabs=2),
                        instruction(f'j {lt_fin}', tabs=2),
                        instruction(f'{lt_false}:'),
                        instruction(f'li {left_expr} 0', tabs=2),
                        instruction(f'j {lt_fin}', tabs=2),
                        instruction(f'{lt_fin}:')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                elif (symbol == '>'):
                    gt_false, gt_fin = next(tags_generator[symbol])
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'blt {left_expr} {right_expr} {gt_false}'),
                        instruction(f'beq {left_expr} {right_expr} {gt_false}'),
                        instruction(f'li {left_expr} 1', tabs=2),
                        instruction(f'j {gt_fin}', tabs=2),
                        instruction(f'{gt_false}:'),
                        instruction(f'li {left_expr} 0', tabs=2),
                        instruction(f'j {gt_fin}', tabs=2),
                        instruction(f'{gt_fin}:')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                elif (symbol == '<='):
                    lte_false_tag, lte_fin_tag = next(tags_generator[symbol])
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'bgt {left_expr} {right_expr} {lte_false_tag}'),
                        instruction(f'li {left_expr} 1', tabs=2),
                        instruction(f'j {lte_fin_tag}', tabs=2),
                        instruction(f'{lte_false_tag}:'),
                        instruction(f'li {left_expr} 0', tabs=2),
                        instruction(f'j {lte_fin_tag}', tabs=2),
                        instruction(f'{lte_fin_tag}:')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                elif (symbol == '>='):
                    bte_false_tag, bte_fin_tag = next(tags_generator[symbol])
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'blt {left_expr} {right_expr} {bte_false_tag}'),
                        instruction(f'li {left_expr} 1', tabs=2),
                        instruction(f'j {bte_fin_tag}', tabs=2),
                        instruction(f'{bte_false_tag}:'),
                        instruction(f'li {left_expr} 0', tabs=2),
                        instruction(f'j {bte_fin_tag}', tabs=2),
                        instruction(f'{bte_fin_tag}:')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                else:
                    codegen_std_error(f'no symbol found in <expr>::%rel_op$ {symbol}')
            elif (bin_op_parent == '%eq_op%'):
                symbol = self.get_pseudo_terminal_value(bin_op_ptr)
                if (symbol == '=='):
                    eq_false_tag, eq_fin_tag = next(tags_generator[symbol])
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'bne {left_expr} {right_expr} {eq_false_tag}'),
                        instruction(f'li {left_expr} 1', tabs=2),
                        instruction(f'j {eq_fin_tag}', tabs=2),
                        instruction(f'{eq_false_tag}:'),
                        instruction(f'li {left_expr} 0', tabs=2),
                        instruction(f'j {eq_fin_tag}', tabs=2),
                        instruction(f'{eq_fin_tag}:')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                elif (symbol == '!='):
                    neq_false_tag, neq_fin_tag = next(tags_generator[symbol])
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'beq {left_expr} {right_expr} {neq_false_tag}'),
                        instruction(f'li {left_expr} 1', tabs=2),
                        instruction(f'j {neq_fin_tag}', tabs=2),
                        instruction(f'{neq_false_tag}:'),
                        instruction(f'li {left_expr} 0', tabs=2),
                        instruction(f'j {neq_fin_tag}', tabs=2),
                        instruction(f'{neq_fin_tag}:')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                else:
                    codegen_std_error(f'no symbol found in <expr>::%rel_op% {symbol}')
            elif (bin_op_parent == '%cond_op%'):
                symbol = self.get_pseudo_terminal_value(bin_op_ptr)
                if (symbol == '&&'):
                    and_false_tag, and_fin_tag = next(tags_generator[symbol])
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'beq {left_expr} $zero {and_false_tag}'),
                        instruction(f'beq {right_expr} $zero {and_false_tag}'),
                        instruction(f'li {left_expr} 1', tabs=2),
                        instruction(f'j {and_fin_tag}', tabs=2),
                        instruction(f'{and_false_tag}'),
                        instruction(f'li {left_expr} 0', tabs=2),
                        instruction(f'j {and_fin_tag}', tabs=2),
                        instruction(f'{and_fin_tag}:')

                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                if (symbol == '||'):
                    or_true_tag, or_fin_tag = next(tags_generator[symbol])
                    self.append_instructions(self.current_method, [
                        instruction(f'# {left_expr} {symbol} {right_expr} ?'),
                        instruction(f'bne {left_expr} $zero {or_true_tag}'),
                        instruction(f'bne {right_expr} $zero {or_true_tag}'),
                        instruction(f'li {left_expr} 0', tabs=2),
                        instruction(f'j {or_fin_tag}', tabs=2),
                        instruction(f'{or_true_tag}:'),
                        instruction(f'li {left_expr} 1', tabs=2),
                        instruction(f'j {or_fin_tag}', tabs=2),
                        instruction(f'{or_fin_tag}:')
                    ])
                    unoccupy_temp_reg(right_expr)
                    return left_expr
                else:
                    codegen_std_error(f'no symbol found in <expr>::%cond_op% {symbol}')
            else:
                codegen_std_error(f'production not found for bin_op_child {bin_op_parent}')
        else:
            codegen_std_error(f'production {productions} did not match any in expr')
        
    def literal(self, children):
        """CANNOT BE NULL"""
        if children == None: codegen_std_error(f'children cannot be null in literal')
        productions = [self.ast[x][PARENT] for x in children]
        value = None
        if (productions == ['%int_literal%']):
            INT_LITERAL_POS = 0
            value = self.get_pseudo_terminal_value(children[INT_LITERAL_POS])
        elif (productions == ['%char_literal%']):
            CHAR_LITERAL_POS = 0
            value = str(ord(self.get_pseudo_terminal_value(children[CHAR_LITERAL_POS])))
        elif (productions == ['%bool_literal%']):
            BOOL_LITERAL_POS = 0
            value = bool_dict[self.get_pseudo_terminal_value(children[BOOL_LITERAL_POS])]
        else:
            codegen_std_error(f'production {productions} was not recognized in literal')
        temp = occupy_temp_reg()
        self.append_instructions(self.current_method, [
            instruction(f'li {temp} {value}')
        ])
        return temp
        
    def callee_header(self):
        if (self.current_method == None):
            codegen_std_error(f'current_method is {self.current_method} in callee_h.')
        elif (self.current_method == 'main'):
            self.callee_header_main()
            return
        if self.callee_actions_performed.get(self.current_method):
            if self.callee_actions_performed[self.current_method][CALLEE_BEGINING]:
                return
        self.append_instructions(self.current_method, [
            instruction(f'# begin callee header'),
            instruction(f'addi $sp $sp -{CALLEE_OFFSET}'), # -40 it is
            instruction(f'move $sp $fp')    , # copy $sp to $fp
            instruction(f'sw $fp 0($sp)')   , # push $fp to stack
            instruction(f'sw $ra 4($sp)')   , # push $ra to stack
            instruction(f'sw $s0 8($sp)')   , # saving $s0 to stack
            instruction(f'sw $s1 12($sp)')  , # saving $s1 to stack
            instruction(f'sw $s2 16($sp)')  , # saving $s2 to stack
            instruction(f'sw $s3 20($sp)')  , # saving $s3 to stack
            instruction(f'sw $s4 24($sp)')  , # saving $s4 to stack
            instruction(f'sw $s5 28($sp)')  , # saving $s5 to stack
            instruction(f'sw $s6 32($sp)')  , # saving $s6 to stack
            instruction(f'sw $s7 36($sp)')  , # saving $s7 to stack
            instruction(f'# end callee header'),
        ])
        self.callee_actions_performed[self.current_method] = [False]*2
        self.callee_actions_performed[self.current_method][CALLEE_BEGINING] = True
    
    def callee_header_main(self):
        if (self.current_method == None) or (self.current_method != 'main'):
            codegen_std_error(f'current_method is {self.current_method} in calle_h_main.')
        if self.callee_actions_performed.get(self.current_method):
            if self.callee_actions_performed[self.current_method][CALLEE_BEGINING]:
                return
        instructions = [
            instruction(f'# start callee main header'),
            instruction(f'addi $sp $sp -{CALLEE_OFFSET}'), # -40 it is
            instruction(f'move $sp $fp')    , # copy $sp to $fp
            instruction(f'sw $fp 0($sp)')   , # push $fp to stack
            instruction(f'sw $ra 4($sp)')   , # push $ra to stack
            instruction(f'sw $s0 8($sp)')   , # saving $s0 to stack
            instruction(f'sw $s1 12($sp)')  , # saving $s1 to stack
            instruction(f'sw $s2 16($sp)')  , # saving $s2 to stack
            instruction(f'sw $s3 20($sp)')  , # saving $s3 to stack
            instruction(f'sw $s4 24($sp)')  , # saving $s4 to stack
            instruction(f'sw $s5 28($sp)')  , # saving $s5 to stack
            instruction(f'sw $s6 32($sp)')  , # saving $s6 to stack
            instruction(f'sw $s7 36($sp)')  , # saving $s7 to stack
            instruction(f'# end callee main header'),
        ]
        self.main_section += instructions
        self.callee_actions_performed['main'] = [False]*2
        self.callee_actions_performed['main'][CALLEE_BEGINING] = True
    
    def callee_ender_main(self):
        if (self.current_method == None) or (self.current_method != 'main'):
            codegen_std_error(f'current_method is {self.current_method} in calle_e_main.')
        if self.callee_actions_performed.get(self.current_method):
            if self.callee_actions_performed[self.current_method][CALLEE_ENDING]:
                return
        instructions = [
            # deallocate field_decl
            instruction(f'# begin callee main ender'),
            instruction(f'{self.tag_calle_ender}:'),
            instruction(f'addi $sp $sp {self.field_decl_offset} # field_decl dealloc'),
            # return has already been assigned to $v0
            instruction(f'lw $fp 0($sp)') , # recover $fp
            instruction(f'sw $ra 4($sp)') , # recover $ra
            instruction(f'sw $s0 8($sp)') , # recover $s0
            instruction(f'sw $s1 12($sp)'), # recover $s1
            instruction(f'sw $s2 16($sp)'), # recover $s2
            instruction(f'sw $s3 20($sp)'), # recover $s3
            instruction(f'sw $s4 24($sp)'), # recover $s4
            instruction(f'sw $s5 28($sp)'), # recover $s5
            instruction(f'sw $s6 32($sp)'), # recover $s6
            instruction(f'sw $s7 36($sp)'), # recover $s7
            instruction(f'move $fp $sp')  , # restore $sp this is the dealloc
            # instruction(f'jr $ra'), # this or end?
            instruction(f'# End Program'),
            instruction(f'li $v0, 10'),
            instruction(f'syscall'),
            instruction(f'# end callee main ender'),
        ]
        self.main_section += instructions
        self.callee_actions_performed['main'][CALLEE_ENDING] = True
    
    def callee_ender(self):
        """By now the local variables should have already been deallocated"""
        if (self.current_method == None):
            codegen_std_error(f'current_method is {self.current_method} in callee_h.')
        elif (self.current_method == 'main'):
            self.callee_ender_main()
            return
        if self.callee_actions_performed.get(self.current_method):
            if self.callee_actions_performed[self.current_method][CALLEE_ENDING]:
                return
        self.append_instructions(self.current_method, [
            # return has already been assigned to $v0
            instruction(f'# begin callee ender'),
            instruction(f'{self.tag_calle_ender}:'),
            instruction(f'lw $fp 0($sp)') , # recover $fp
            instruction(f'sw $ra 4($sp)') , # recover $ra
            instruction(f'sw $s0 8($sp)') , # recover $s0
            instruction(f'sw $s1 12($sp)'), # recover $s1
            instruction(f'sw $s2 16($sp)'), # recover $s2
            instruction(f'sw $s3 20($sp)'), # recover $s3
            instruction(f'sw $s4 24($sp)'), # recover $s4
            instruction(f'sw $s5 28($sp)'), # recover $s5
            instruction(f'sw $s6 32($sp)'), # recover $s6
            instruction(f'sw $s7 36($sp)'), # recover $s7
            instruction(f'move $fp $sp')  , # restore $sp this is the dealloc
            instruction(f'jr $ra'),
            instruction(f'# end callee ender'),
        ])
        self.callee_actions_performed[self.current_method][CALLEE_ENDING] = True

    def method_decl_handler(self, parent_ptr):
        children = self.ast[parent_ptr][PTR]
        self.method_decl_kleene(children) # <method_decl*>

    def method_decl_kleene(self, children):
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            self.method_offset = 0
            if (productions == ['def', '<type|void>', '%id%', '(', '<method_args>', ')', '<block>', '<method_decl*_aux>']):
                TYPE_OR_VOID_POS, ID_POS, METHOD_ARGS_POS, BLOCK_POS, METHOD_DECL_AUX_POS = 1, 2, 4, 6, 7
                # '%id%'
                method_name = method_name_gen(self.get_pseudo_terminal_value(children[ID_POS]))
                self.current_method = method_name
                if method_name != 'main':
                    self.assembler_sections.append(list())
                    self.append_instructions(self.current_method, [
                        instruction(f'{self.current_method}: # method tag', tabs=0)
                    ])
                # '<type|void>'
                self.method_return_types[method_name] = self.type_or_void(children[TYPE_OR_VOID_POS])
                # '(', '<method_args>', ')'
                method_args_children = self.ast[children[METHOD_ARGS_POS]][CHILDREN]
                self.method_args(method_args_children, method_name)
                # '<block>'
                block_children = self.ast[children[BLOCK_POS]][CHILDREN]
                self.callee_header()
                self.tag_calle_ender = next(tags_generator[CALLEE_ENDER_TAG])
                self.block(block_children)
                self.callee_ender()
                # '<method_decl*_aux>'
                method_decl_aux_children = self.ast[children[METHOD_DECL_AUX_POS]][CHILDREN]
                self.method_decl_aux(method_decl_aux_children)
            elif (productions == ['def', '<type|void>', '%id%', '(', ')', '<block>', '<method_decl*_aux>']):
                TYPE_OR_VOID_POS, ID_POS, BLOCK_POS, METHOD_DECL_AUX_POS = 1, 2, 5, 6
                # '%id%'
                method_name = method_name_gen(self.get_pseudo_terminal_value(children[ID_POS]))
                self.current_method = method_name
                if method_name != 'main':
                    self.assembler_sections.append(list())
                    self.append_instructions(self.current_method, [
                        instruction(f'{self.current_method}: # method tag', tabs=0)
                    ])
                # '<type|void>'
                self.method_return_types[method_name] = self.type_or_void(children[TYPE_OR_VOID_POS])
                # '(', ')'
                pass
                # '<block>'
                block_children = self.ast[children[BLOCK_POS]][CHILDREN]
                self.callee_header()
                self.tag_calle_ender = next(tags_generator[CALLEE_ENDER_TAG])
                self.block(block_children)
                self.callee_ender()
                # '<method_decl*_aux>'
                method_decl_aux_children = self.ast[children[METHOD_DECL_AUX_POS]][CHILDREN]
                self.method_decl_aux(method_decl_aux_children)
            else:
                codegen_std_error(f'method_decl_kleene did not find a production like {productions}')
    
    def method_decl_aux(self, children):
        """CAN BE NULL"""
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == ['<method_decl*>', '<method_decl*_aux>']):
                METHOD_DECL_KLEENE_POS, METHOD_DECL_AUX_POS = 0, 1
                method_decl_kleene_children = self.ast[children[METHOD_DECL_KLEENE_POS]][CHILDREN]
                self.method_decl_kleene(method_decl_kleene_children)
                method_decl_aux_children = self.ast[children[METHOD_DECL_AUX_POS]][CHILDREN]
                self.method_decl_aux(method_decl_aux_children)
            else:
                codegen_std_error(f'method_decl_aux did not find a production like {productions}')
            
    def type_or_void(self, ptr):
        """CANNOT BE NULL"""
        prod, edge = self.ast[self.ast[ptr][PTR][0]]
        if prod == '%type%':
            val = self.ast[edge][PARENT]
            return val
        elif (prod == 'void'):
            val = prod
            return val
        else:
            codegen_std_error(f'type_or_void did not recognize {prod} as a type')
    
    def method_args(self, children, method_name):
        """CANNOT BE NULL, <method_args>"""
        if children == None: codegen_std_error(f'<method_args> children cannot be null.')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['%type%', '%id%']):
            VAR_TYPE_POS, ID_POS = 0, 1
            self.var_type = self.get_pseudo_terminal_value(children[VAR_TYPE_POS])
            arg_name = self.get_pseudo_terminal_value(children[ID_POS])
            self.method_arguments_appender(method_name, arg_name, self.var_type, has_been_allocated=False, stack_pointer_offset=self.method_offset)
            self.method_offset += abs(mem_space[self.var_type])
        elif (productions == ['<method_args>', '<method_args">']):
            METHOD_ARGS_POS, METHOD_ARGS_DASH_POS = 0, 1
            method_args_children = self.ast[children[METHOD_ARGS_POS]][CHILDREN]
            self.method_args(method_args_children, method_name)
            method_args_dash_children = self.ast[children[METHOD_ARGS_DASH_POS]][CHILDREN]
            self.method_args_dash(method_args_dash_children, method_name)
        else:
            codegen_std_error(f'method_args did not recognize production like {productions}')
        
    def method_args_dash(self, children, method_name):
        """CAN BE NULL"""
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == [',', '%type%', '%id%', '<method_args">']):
                VAR_TYPE_POS, ID_POS, METHOD_ARGS_DASH_POS = 1, 2, 3
                self.var_type = self.get_pseudo_terminal_value(children[VAR_TYPE_POS])
                arg_name = self.get_pseudo_terminal_value(children[ID_POS])
                self.method_arguments_appender(method_name, arg_name, self.var_type, has_been_allocated=False, stack_pointer_offset=self.method_offset)
                self.method_offset += abs(mem_space[self.var_type])
                method_args_dash_children = self.ast[children[METHOD_ARGS_DASH_POS]][CHILDREN]
                self.method_args_dash(method_args_dash_children, method_name)
            else:
                codegen_std_error(f'method_args_dash did not recognize production like {productions}')
    
    def method_arguments_appender(self, method_name, arg_name, var_type, has_been_allocated, stack_pointer_offset, is_arg=True):
        if not self.method_arguments.get(method_name):
            self.method_arguments[method_name] = dict()
        self.method_arguments[method_name][arg_name] = [var_type, has_been_allocated, stack_pointer_offset, is_arg] 
    
    def opening_curly(self):
        """NO ASSEMBLER OUTPUT UNTIL VARIABLE DECLARATION OR FIELD DECLARATION"""
        self.scope_stack.append({})
        self.scope_space[len(self.scope_stack)-1] = 0

    def closing_curly(self):
        self.scope_stack.pop()
        self.scope_space.pop((len(self.scope_space)-1), None)
    
    def field_decl_handler(self, field_decl_ptr):
        """ Finds the children first and then allocates space for all fields """
        children = self.ast[field_decl_ptr][PTR]
        self.field_decl_offset = 0 # reseting field_decl just a formality
        self.field_decl_kleene(children)
        """ALLOCATE THE SPACE FOR THIS SCOPE, ACCESS THE SCOPE_SPACE"""
        self.main_section += [
            instruction(f'addi $sp $sp -{self.scope_space[(len(self.scope_stack)-1)]} # field_decl alloc')
        ]
    
    def add_to_scope_space(self, scope, num):
        if self.scope_space.get(scope):
            self.scope_space[scope] += abs(num)
        else:
            self.scope_space[scope] = abs(num)
    
    def field_decl_kleene(self, children):
        """CANNOT BE NULL, <field_decl*>"""
        if children == None: 
            codegen_std_error(f'children is none in field_decl_finder')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['%type%', '<field_decl>', '<field_decl*_aux>']):
            VAR_TYPE_POS, FIELD_DECL_POS, FIELD_DECL_AUX_POS = 0, 1, 2
            self.var_type = self.get_pseudo_terminal_value(children[VAR_TYPE_POS])
            self.field_decl(self.ast[children[FIELD_DECL_POS]][CHILDREN]) # <field_decl>
            self.field_decl_aux(self.ast[children[FIELD_DECL_AUX_POS]][CHILDREN])
        else:
            codegen_std_error(f'field_decl_kleene did not find production template like {productions}')
    
    def field_decl_aux(self, children):
        """CAN BE NULL, <field_decl*_aux>"""
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == ['<field_decl*>', '<field_decl*_aux>']):
                FIELD_DECL_KLEENE, FIELD_DECL_AUX = 0, 1
                self.field_decl_kleene(self.ast[children[FIELD_DECL_KLEENE]][CHILDREN])
                self.field_decl_aux(self.ast[children[FIELD_DECL_AUX]][CHILDREN])
            else:
                codegen_std_error(f'field_decl_aux did not find a production like {productions}')

    def field_decl(self, children):
        """CANNOT BE NULL, <field_decl>"""
        if children == None: codegen_std_error(f'children is none in field_decl')
        productions = [self.ast[x][PARENT] for x in children]
        if (productions == ['%id%', '<subscript>', ';']):
            ID_POS, SUBSCRIPT_POS = 0, 1
            var_name = self.get_pseudo_terminal_value(children[ID_POS])
            subscript_val = self.get_subscript_val(children[SUBSCRIPT_POS])
            self.add_var_to_scope(var_name, self.var_type, has_been_allocated=False, stack_pointer_offset=self.field_decl_offset, is_argument=False) # adding var to scope
            self.field_decl_offset += abs(mem_space[self.var_type])
        elif (productions == ['%id%', '<subscript>', '<var_array_list>', ';']):
            ID_POS, SUBSCRIPT_POS, VAR_ARRAY_LIST_POS = 0, 1, 2
            var_name = self.get_pseudo_terminal_value(children[ID_POS])
            subscript_val = self.get_subscript_val(children[SUBSCRIPT_POS])
            self.add_var_to_scope(var_name, self.var_type, has_been_allocated=False, stack_pointer_offset=self.field_decl_offset, is_argument=False) # adding var to scope
            self.field_decl_offset += abs(mem_space[self.var_type])
            self.var_array_list(self.ast[children[VAR_ARRAY_LIST_POS]][CHILDREN])
        else:
            codegen_std_error(f'field_decl did not find template like {productions}')
    
    def var_array_list(self, children):
        """CAN BE NULL"""
        if children:
            productions = [self.ast[x][PARENT] for x in children]
            if (productions == [',', '%id%', '<subscript>', '<var_array_list>']):
                ID_POS, SUBSCRIPT_POS, VAR_ARRAY_LIST_POS = 1, 2, 3
                var_name = self.get_pseudo_terminal_value(children[ID_POS])
                subscript_val = self.get_subscript_val(children[SUBSCRIPT_POS])
                self.add_var_to_scope(var_name, self.var_type, has_been_allocated=False, stack_pointer_offset=self.var_decl_offset, is_argument=False)
                self.var_decl_offset += abs(mem_space[self.var_type])
                self.var_array_list(self.ast[children[VAR_ARRAY_LIST_POS]][CHILDREN])
            else:
                codegen_std_error(f'var_array_list did not find production like {productions}')

    def add_var_to_scope(self, var_name, var_type, has_been_allocated, stack_pointer_offset, is_argument):
        """USED ONLY FOR LOCAL VARIABLES, NO METHOD ARGS"""
        self.scope_stack[-1][var_name] = [var_type, has_been_allocated, stack_pointer_offset, is_argument]
        self.add_space_to_scope(var_type) # registering space used so far.


s = scanner('./src_code.decaf', './decaf_scanner/tokens'    , build=1, save=0)
l = lr_0('<program>'          , './decaf_parser/productions', build=1, save=0)
t = lr_0_t(l)
p = parser(t, s)
with open('tree_debug.txt', mode='w+') as file:
    file.write(str(p))
    file.close()
sem = semantic(p)
c = codegen(sem)
