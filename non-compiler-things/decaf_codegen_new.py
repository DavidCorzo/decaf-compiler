from typing import Iterable
from decaf_scanner import scanner
from decaf_parser import lr_0, lr_0_t, parser, is_nonterminal, is_pseudo_terminal, PARENT, PTR, CHILDREN
from decaf_semantic import semantic

# GLOBAL VARIABLES
mem_space = {'int':4, 'boolean': 1, 'class': 0, 'void': 0}
VAR_TYPE, SP_POS = 0, 1

MAIN_TAG = 'main'
FINISH_TAG = 'fin'

def tag_gen_with_name(beg_name, end_name=None):
    i = 0
    while True:
        if end_name:
            yield (f'beg_{beg_name}_{i}', f'end_{end_name}_{i}')
        else:
            yield (f'beg_{beg_name}_{i}', f'end_{beg_name}_{i}')
        i += 1

IF_COND_TAG_GEN, ELSE_COND_TAG_GEN, FOR_LOOP_TAG_GEN, LESS_THAN_OR_EQUAL_TAG_GEN, GREATER_THAN_OR_EQUAL_TAG_GEN, EQUAL_TAG_GEN, NOT_EQUAL_TAG_GEN, AND_TAG_GEN, OR_TAG_GEN = 'if', 'else_or_end_if', 'for', 'less_than', 'greater_than', 'equal', 'not_equal', 'and', 'or'
tags_generator = {
    IF_COND_TAG_GEN                 : tag_gen_with_name(IF_COND_TAG_GEN, ELSE_COND_TAG_GEN),
    FOR_LOOP_TAG_GEN                : tag_gen_with_name(FOR_LOOP_TAG_GEN),
    LESS_THAN_OR_EQUAL_TAG_GEN      : tag_gen_with_name(LESS_THAN_OR_EQUAL_TAG_GEN),
    GREATER_THAN_OR_EQUAL_TAG_GEN   : tag_gen_with_name(GREATER_THAN_OR_EQUAL_TAG_GEN),
    EQUAL_TAG_GEN                   : tag_gen_with_name(EQUAL_TAG_GEN),
    NOT_EQUAL_TAG_GEN               : tag_gen_with_name(NOT_EQUAL_TAG_GEN),
    AND_TAG_GEN                     : tag_gen_with_name(AND_TAG_GEN), 
    OR_TAG_GEN                      : tag_gen_with_name(OR_TAG_GEN)
}

print_debug = print

OCCUPIED, VACANT = 'OCCUPIED', 'VACANT'
temp_reg = {
    VACANT: {'$t0', '$t1', '$t2', '$t3', '$t4', '$t5', '$t6', '$t7'},
    OCCUPIED: set()
}

def codegen_std_error(str):
    print(f'Codegen error: {str}')
    exit(-1)

def codegen_instruction_wrapper(instruction, tabs=1):
    return (('\t'*tabs) + f"{instruction}\n")

def occupy_temp_reg():
    if len(temp_reg[VACANT]):
        popped = temp_reg[VACANT].pop()
        temp_reg[OCCUPIED].add(popped)
        return popped
    else:
        codegen_std_error(f"not enough registers to compute operation {temp_reg}")

def unoccupy_temp_reg(reg):
    if reg in temp_reg[OCCUPIED]:
        temp_reg[OCCUPIED].remove(reg)
        temp_reg[VACANT].add(reg)
    else:
        codegen_std_error(f"did not find {reg} in temp_reg[OCCUPIED]")

def method_name(method_name):
    return f'method_{method_name}'

class codegen:
    def __init__(self, assembled_semantic:semantic, exec_filename='a.decaf_exe'):
        self.ast                = assembled_semantic.ast
        self.ast_head           = assembled_semantic.ast_head
        self.assembler_sections = dict()
        self.current_section    = 0
        self.scope_stack        = list()
        self.scope_index        = 0
        self.scope_vars_space   = dict()
        self.expr_handler       = codegen_expr(self)
        self.statement_handler  = codegen_statement(self)
        self.initiate()
    
    def subscript(self, subscript_head):
        subscript_children = self.ast[subscript_head][CHILDREN]
        if subscript_children:
            L_SB_POS, INT_LITERAL_POS, R_SB_POS = 0, 1, 2
            l_sb = self.ast[subscript_children[L_SB_POS]]
            int_literal = self.ast[subscript_children[INT_LITERAL_POS]]
            r_sb = self.ast[subscript_children[R_SB_POS]]
            return int_literal
        else:
            return None
    
    def initiate(self):
        self.assembler_sections[MAIN_TAG] = list()
        self.assembler_sections[FINISH_TAG] = list()
        self.traverse_ast([self.ast_head])
    
    def traverse_ast(self, list_node_i:Iterable[int]):
        for node_index in list_node_i:
            prod, edges = self.ast[node_index]
            if (prod == '<statement>'):
                self.statement_handler.codegen_statement(node_index)
                continue
            elif (is_nonterminal(prod) and (edges != None)):
                self.traverse_ast(edges)
# EXPR
class codegen_expr:
    def __init__(self, codegen_instance:codegen):
        # (<expr>, [children])
        self.ast = codegen_instance.ast
        self.codegen_instance = codegen_instance
        self.assembler_section = list()
    
    def codegen_expr(self, expr_head):
        self.assembler_section = list()
        self.traverse_expr([expr_head])
        return self.assembler_section
    
    def traverse_expr(self, children_of_expr:list):
        productions = tuple([self.ast[x] for x in children_of_expr])
        pass

class codegen_statement:
    def __init__(self, codegen_instance:codegen):
        self.ast = codegen_instance.ast
        self.codegen_instance = codegen_instance
        self.assembler_sections = list()
    
    def codegen_statement(self, statement_head:int):
        statement_children = self.ast[statement_head][CHILDREN]
        self.assembler_sections = list()
        if statement_children:
            self.traverse_statement(statement_children)
        return self.assembler_sections

    def traverse_statement(self, statement_children:list):
        productions = [self.ast[x][PARENT] for x in statement_children]
        if (productions == ['<assignment_statement>']):
            assignment_statement_children = self.ast[statement_children[0]][CHILDREN]
            self.assignment_statement(assignment_statement_children)
        elif (productions == ['<method_call>', ';']):
            pass
        elif (productions == ['if', '<expr>', '<block>', '<else_block>']):
            pass
        elif (productions == ['for', '<for_eval>', '<block>']):
            pass
        elif (productions == ['return', ';']):
            pass
        elif (productions == ['return', '<expr>', ';']):
            pass
        elif (productions == ['break', ';']):
            pass
        elif (productions == ['continue', ';']):
            pass
        elif (productions == ['<block>']):
            pass
        elif (productions == ['<expr>', ';']):
            pass
        elif (productions == ['<print_var>', ';']):
            pass
        else:
            codegen_std_error(f'statement {productions} did not match any.')
    
    def assignment_statement(self, assignment_statement_children:list):
        # ['%id%', '<subscript>', '<assign_op>', '<expr>', ';']
        ID_POS, SUBS_POS, ASSIGN_OP_POS, EXPR_POS = 0, 1, 2, 3
        var_name = self.ast[self.ast[assignment_statement_children[ID_POS]][PTR]][PARENT]
        subscript = self.codegen_instance.subscript(assignment_statement_children[SUBS_POS])
        assign_op = self.ast[self.ast[assignment_statement_children[ASSIGN_OP_POS]][PTR][0]][PARENT]
        expr = self.codegen_instance.expr_handler.codegen_expr(assignment_statement_children[EXPR_POS])
        if subscript:
            pass
        if (assign_op == '%assign%'):
            pass
        elif (assign_op == '%assign_inc%'):
            temp = self.get_vacant_temp()
            f'lw {temp} {var_offset}($sp)'
            f'addi {rhs_expr_reg} {temp} {rhs_expr_reg}'
            pass
        elif (assign_op == '%assign_dec%'):
            pass

class codegen_method_decl:
    def __init__(self, ast:dict):
        pass

class codegen_fiedl_decl:
    def __init__(self, ast:dict):
        pass

class codegen_var_decl:
    def __init__(self, ast:dict):
        pass

s = scanner('./src_code.decaf', './decaf_scanner/tokens', build=1, save=0)
l = lr_0('<program>', './decaf_parser/productions', build=1, save=0)
t = lr_0_t(l)
p = parser(t, s)
with open('tree_debug.txt', mode='w+') as file:
    file.write(str(p))
    file.close()
s = semantic(p)
c = codegen(s)
