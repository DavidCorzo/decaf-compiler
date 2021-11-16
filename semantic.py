from os import error
from decaf_parser import lr_0, slr, parser, is_nonterminal, is_pseudo_terminal, is_terminal, is_terminal_with_value, PARENT, CHILDREN, print_dict, PTR
from scanner import scanner
import pdb
# unicidad de variables
# variables declaradas antes de acceder
# que sean accesibles

PRODUCTION_DETECTED, SCOPE_OFFSET, = 0, 1, 
class semantic:
    var_type = None

    def __init__(self, p:parser):
        # self.lexed_tokens = p.lexed_tokens
        self.productions_tree           = p.productions_tree
        self.productions_tree_head      = p.productions_tree_head
        self.scope_stack                = list()
        self.next_scope_pending_vars    = dict()
        self.scope_index                = 0
        self.last_var                   = None
        self.exprs                      = dict()
        self.unique_variables_and_scope_access()

    def unique_variables_and_scope_access(self):
        self.scope_stack.append({})
        self.scope_index = 0
        self.traverse([self.productions_tree_head], False, False)
        self.scope_stack.pop()
        # self.get_head_expr([self.productions_tree_head])
    
    def traverse(self, list_node_i, var_decl, append_next):
        i = 0
        while i < len(list_node_i):
            node_index = list_node_i[i]
            prod, edge = self.productions_tree[node_index]
            if (prod == '<field_decl*>') or (prod == '<var_decl*>'):
                """ append variables in current scope """
                if (edge != None):
                    # if it is not epsilon make recursive call with the non-epsilon edge and 
                    # var_decl=True and append_next=False. 
                    self.traverse(edge, True, False)
                    i += 1
                    continue
                else:
                    # the edge is epsilon, so it is absent. This is basically a base case. 
                    i += 1
                    continue
            elif ((prod == '<method_args>') or (prod == '<method_args">')):
                # we are defining method args, these go on the next scope.
                if (edge != None):
                    self.traverse(edge, True, True)
                i += 1
                continue
            elif (prod == '<method_decl*>'):
                # we are defining a method, so collect the <type|void> and the %id%, then set it to start on the method args.
                # def 0 <type|void> 1 %id% 2 ( <method_args> ) <block> <method_decl*_aux>
                type_void, method_name = 1, 2
                temp = self.productions_tree[edge[type_void]]
                if is_nonterminal(temp[PARENT]):
                    if temp[PARENT] == '<type|void>':
                        ptr = temp[PTR][0]
                        t = self.productions_tree[ptr]
                        if is_pseudo_terminal(t[PARENT]): self.var_type = self.productions_tree[t[PTR]][PARENT]
                        else: self.var_type = t[PARENT]
                else:
                    self.var_type = self.productions_tree[temp[PTR]][PARENT]
                # print(self.var_type)
                # extract %id%
                temp = self.productions_tree[edge[method_name]]
                self.var_name = self.productions_tree[temp[PTR]][PARENT]
                self.add_variable_to_scope(self.var_name, False)
                edge = edge[3:]
            elif (prod == '%type%'):
                self.var_type = self.productions_tree[edge][PARENT]
            elif (prod == 'class'):
                self.var_type = prod
            elif (prod == '%id%'):
                self.var_name = self.productions_tree[edge][PARENT]
                v = self.var_name
                if var_decl: 
                    # we are declaring varibles, not using them. 
                    self.add_variable_to_scope(self.var_name, append_next)
                elif (not var_decl): 
                    # We are using variables that should have already been declared
                    if self.var_type != 'class':
                        self.check_if_var_exists(self.var_name)
                    else:
                        self.add_variable_to_scope(self.var_name, append_next)
            elif (prod == '{'):
                self.scope_stack.append({})
                self.scope_index += 1
                self.scope_stack[self.scope_index].update(self.next_scope_pending_vars)
                self.next_scope_pending_vars = dict()
            elif (prod == '}'):
                self.scope_stack.pop()
                self.scope_index -= 1
            elif (prod == '<expr>'):
                self.head_expr_return(node_index)

            if ((prod == ';') or (prod == '{')):
                var_decl = append_next = False

            # simply pass the next recursive call with the parameters 
            if is_nonterminal(prod) and (edge != None):
                self.traverse(edge, var_decl, append_next)
            i += 1

    def unique_var_error(self, var_name):
        print(f"SEMANTIC ERROR: {var_name} is already declared. Identifiers need to be unique.")
        error(-1)
        exit(-1)
    
    def var_not_declared(self, var_name):
        print(f"SEMANTIC ERROR: {var_name} is not declared. Declare it before you use it.")
        error(-1)
        exit(-1)
    
    def add_variable_to_scope(self, var_name, append_next):
        if append_next:
            if not self.next_scope_pending_vars.get(var_name):
                self.next_scope_pending_vars[var_name] = self.var_type
            else:
                self.unique_var_error(var_name)
        else:
            if not self.scope_stack[self.scope_index].get(var_name):
                self.scope_stack[self.scope_index][var_name] = self.var_type
            else:
                self.unique_var_error(var_name)
    
    def check_if_var_exists(self, var_name):
        if self.scope_stack[self.scope_index].get(var_name):
            return
        else:
            index = self.scope_index
            while index >= 0:
                if self.scope_stack[index].get(var_name):
                    return
                index -= 1
            self.var_not_declared(var_name)
    
    # def get_head_expr(self, list_node_i):
    #     for node_index in list_node_i:
    #         prod, edge = self.productions_tree[node_index]
    #         if prod == '<expr>':
    #             self.head_expr_return(node_index)
    #             continue
    #         elif is_nonterminal(prod) and (edge != None):
    #             self.get_head_expr(edge)
    
    def head_expr_return(self, node_index):
        # expr_base_case = [
        #     ['%id%', '<subscript>'],
        #     ['<method_call>'],
        #     ['<literal>'],
        #     ['<expr>', '<bin_op>', '<expr>'],
        #     ['%minus%', '<expr>'],
        #     ['!', '<expr>'],
        #     ['(', '<expr>', ')'],
        #     ['<expr>', '<expr>']
        # ]
        if not self.exprs.get(node_index):
            self.exprs[node_index] = None
        prod, edge = self.productions_tree[node_index]
        productions = [self.productions_tree[x][PARENT] for x in edge]
        edges       = [self.productions_tree[x][CHILDREN] for x in edge]
        print(productions, edges)
        if   (productions == ['%id%', '<subscript>']):
            return self.scope_stack[self.scope_index][edges[0][0]]
        elif (productions == ['<method_call>']):
            print
        elif (productions == ['<literal>']):
            n = self.productions_tree[self.productions_tree[edge[PARENT]][CHILDREN][PARENT]][PARENT]
            if (n == '%int_literal%'):
                return 'int'
            elif (n == '%char_literal%'):
                return 'int'
            elif (n == '%bool_literal%'):
                return 'boolean'
        elif (productions == ['<expr>', '<bin_op>', '<expr>']):
            
            print
        elif (productions == ['%minus%', '<expr>']):
            print
        elif (productions == ['!', '<expr>']):
            print
        elif (productions == ['(', '<expr>', ')']):
            print
        elif (productions == ['<expr>', '<expr>']):
            print
        pass
  

    # def find_expr(self, list_node_i):
    #     i = 0
    #     while i < len(list_node_i):
    #         node_index = list_node_i[i]
    #         prod, edge = self.productions_tree[node_index]
    #         if prod == '<expr>':
    #             self.expr_stack.update({node_index : None})
    #         if (edge != None) and (is_nonterminal(prod)):
    #             self.find_expr(edge)
    #         i += 1

    # def expr_return_val(self):
    #     # <expr>:
    #     #     - ['%id%', '<subscript>']
    #     #     - ['<method_call>']
    #     #     - ['<literal>']
    #     #     - ['<expr>', '<bin_op>', '<expr>']
    #     #     - ['%minus%', '<expr>']
    #     #     - ['!', '<expr>']
    #     #     - ['(', '<expr>', ')']
    #     #     - ['<expr>', '<expr>']
    #     pass
    
    # def traverse(self, list_node_i, find):
        # for node_index in list_node_i:
        #     prod, edge = self.productions_tree[node_index]
        #     if prod == None:
        #         pass
        #     elif is_pseudo_terminal(prod) or is_terminal(prod):
        #         pass
        #     else:
        #         if prod == find:
        #             self.expr_stack.insert(-1, node_index)
        #         self.traverse(edge, find)

code = scanner("./src_code.decaf", "./tokens.yaml")
code.produce_automata()
code.save_automata("tokens.pickle")
code.scan()
code.linked_list_of_tokens.append((None, '$'))

# print(code.linked_list_of_tokens)
l = lr_0('<program>', 'productions.yaml', build=1, save=1)
s = slr(l)
p = parser(s, code.linked_list_of_tokens)
s = semantic(p)

