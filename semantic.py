from decaf_parser import lr_0, slr, parser, is_nonterminal, is_pseudo_terminal, is_terminal, is_terminal_with_value, PARENT, CHILDREN
from scanner import scanner
# unicidad de variables
# variables declaradas antes de acceder
# que sean accesibles

class semantic:
    def __init__(self, p:parser):
        # self.lexed_tokens = p.lexed_tokens
        self.productions_tree       = p.productions_tree
        self.productions_tree_head  = p.productions_tree_head
        self.scope_stack            = list()
        self.expr_stack             = list()
        self.traverse([self.productions_tree_head], '<expr>')
        print(self.expr_stack)
        for i in self.expr_stack:
            print(self.productions_tree[i])
    


    def traverse(self, list_node_i, find):
        for node_index in list_node_i:
            prod, edge = self.productions_tree[node_index]
            if prod == None:
                pass
            elif is_pseudo_terminal(prod) or is_terminal(prod):
                pass
            else:
                if prod == find:
                    self.expr_stack.insert(-1, node_index)
                self.traverse(edge, find)

    
    def add_scope(self):
        pass

code = scanner("./src_code.decaf", "./tokens.yaml")
code.produce_automata()
code.save_automata("tokens.pickle")
code.scan()
code.linked_list_of_tokens.append((None, '$'))

# print(code.linked_list_of_tokens)
l = lr_0('<program>', 'productions.yaml', build=1, save=1)
s = slr(l)
p = parser(s, code.linked_list_of_tokens)
# print(p)
# s = semantic(p)

