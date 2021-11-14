from decaf_parser import lr_0, slr, parser, is_nonterminal, is_pseudo_terminal, is_terminal, is_terminal_with_value, PARENT, CHILDREN, print_dict
from scanner import scanner
import pdb
# unicidad de variables
# variables declaradas antes de acceder
# que sean accesibles

PRODUCTION_DETECTED, SCOPE_OFFSET, = 0, 1, 
class semantic:
    inside_productions = {
        '<field_decl*>' : [False, 0],
        '<program">'    : [False, 0],
        '<method_args>' : [False, 1]
    }
    var_type = None

    def __init__(self, p:parser):
        # self.lexed_tokens = p.lexed_tokens
        self.productions_tree           = p.productions_tree
        self.productions_tree_head      = p.productions_tree_head
        self.scope_stack                = list()
        self.next_scope_pending_vars    = dict()
        self.scope_index                = 0
        self.last_var                   = None
        # print(self.inside_productions['<method_args>'][SCOPE_OFFSET])
        self.unique_variables_and_scope_access()
        # self.expr_stack             = list()
        # self.traverse([self.productions_tree_head], '<expr>')
        # print(self.expr_stack)
        # for i in self.expr_stack:
        #     print(self.productions_tree[i])
    
    def unique_variables_and_scope_access(self):
        self.scope_stack.append({})
        self.scope_index = 0
        self.traverse([self.productions_tree_head])
    
    # def traverse(self, list_node_i, find):
    #     for node_index in list_node_i:
    #         prod, edge = self.productions_tree[node_index]
    #         if prod == None:
    #             pass
    #         elif is_pseudo_terminal(prod) or is_terminal(prod):
    #             pass
    #         else:
    #             if prod == find:
    #                 self.expr_stack.insert(-1, node_index)
    #             self.traverse(edge, find)

    def traverse(self, list_node_i, append_to_next=False):
        index = 0
        # print(list_node_i)
        while index < len(list_node_i):
            node_index = list_node_i[index]
            prod, edge = self.productions_tree[node_index]
            recursion = True
            ss, ns, lv, vt = self.scope_stack, self.next_scope_pending_vars, self.last_var, self.var_type
            if prod == '%id%':
                self.last_var = self.productions_tree[edge][PARENT]
                lv = self.last_var
                if not append_to_next:
                    if not self.scope_stack[self.scope_index].get(self.last_var):
                        self.scope_stack[self.scope_index][self.last_var] = self.var_type
                    else:
                        print("ERROR")
                else:
                    self.next_scope_pending_vars[self.last_var] = self.var_type
            elif prod == '{':
                self.scope_stack.append({})
                self.scope_index += 1
                self.scope_stack[self.scope_index].update(self.next_scope_pending_vars)
                print(self.scope_stack)
                self.next_scope_pending_vars = {}
            elif prod == '}':
                self.scope_stack.pop()
                self.scope_index -= 1
            elif (prod == '%type%') or (prod == 'class'):
                if is_pseudo_terminal(prod):
                    self.var_type = self.productions_tree[edge][PARENT]
                else:
                    self.var_type = prod
            elif (prod == '<subscript>'):
                if not append_to_next:
                    self.scope_stack[self.scope_index][self.last_var] += '[]'
                else:
                    self.next_scope_pending_vars[self.last_var] += '[]'
            elif prod == '<method_args>' or prod == '<method_args">':
                self.traverse(edge, append_to_next=True)
                recursion = False
            if is_nonterminal(prod) and recursion:
                # print(prod, edge, end=' ')
                self.traverse(edge, append_to_next)
            index += 1

    def collect_field_decl(self, ptr_list):
        # <field_decl*>

        pass

    def collect_method_decl(self):
        # <method_decl*>

        pass

    def collect_method_args(self):
        # <method_args>

        pass

    def collect_var_decl(self):
        # <var_decl*>

        pass

    # def traverse(self, list_node_i):
    #     """
    #     Uniqueness of variables and scope access.
    #     """
    #     ip = self.inside_productions
    #     for node_index in list_node_i:
    #         prod, edge = self.productions_tree[node_index]
    #         if (prod == '%id%'):
    #             self.var_name = self.productions_tree[edge][PARENT]
    #             if not self.scope_stack[self.scope_index].get(self.var_name):
    #                 self.insert_var_with_offset()
    #                 print(self.scope_stack)
    #                 print
    #         elif (prod == '{'):
    #             if self.scope_index == (len(self.scope_stack) - 1):
    #                 self.scope_stack.append({})
    #             self.scope_index += 1
    #             print(self.scope_stack)
    #             print
    #         elif (prod == '}'):
    #             self.scope_stack.pop()
    #             self.scope_index -= 1
    #             print(self.scope_stack)
    #             print
    #         elif (prod == '%type%'):
    #             self.var_type = self.productions_tree[edge][PARENT]
    #             print
    #         elif (prod == '<type|void>'):
    #             self.var_type = self.productions_tree[edge[0]]
    #             if (self.var_type[PARENT] == '%type%'):
    #                 self.var_type = self.productions_tree[self.var_type[CHILDREN]][PARENT]
    #             else:
    #                 self.var_type = self.var_type[CHILDREN]
    #             print
    #         elif (prod == 'class'):
    #             self.var_type = prod
    #             print
    #         elif (prod == '<subscript>'):
    #             self.scope_stack[-1][self.var_name] = self.scope_stack[-1][self.var_name] + '[]'
    #         elif is_nonterminal(prod):
    #             if self.inside_productions.get(prod) != None:
    #                 self.inside_productions[prod][PRODUCTION_DETECTED] = True
    #                 print
    #                 self.traverse(edge)
    #                 self.inside_productions[prod][PRODUCTION_DETECTED] = False
    #             else:
    #                 print
    #                 self.traverse(edge)
    
    # def insert_var_with_offset(self):
    #     if self.inside_productions['<method_args>'][PRODUCTION_DETECTED]:
    #         offset = self.inside_productions['<method_args>'][SCOPE_OFFSET]
    #         si, ss = self.scope_index, self.scope_stack
    #         if self.scope_index == (len(self.scope_stack) - 1):
    #             # pdb.set_trace()
    #             self.scope_index.append({})
    #         self.scope_stack[self.scope_index + offset][self.var_name] = self.var_type
    #     else:
    #         self.scope_stack[self.scope_index][self.var_name] = self.var_type

code = scanner("./src_code.decaf", "./tokens.yaml")
code.produce_automata()
code.save_automata("tokens.pickle")
code.scan()
code.linked_list_of_tokens.append((None, '$'))

# print(code.linked_list_of_tokens)
l = lr_0('<program>', 'productions.yaml', build=1, save=1)
s = slr(l)
p = parser(s, code.linked_list_of_tokens)
print(p)
s = semantic(p)

