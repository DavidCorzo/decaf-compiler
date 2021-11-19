from os import error
from decaf_parser import lr_0, lr_0_t, parser, is_nonterminal, is_pseudo_terminal, PARENT, CHILDREN, PTR

PRODUCTION_DETECTED, SCOPE_OFFSET, = 0, 1
INT, BOOLEAN = 'int', 'boolean'
class semantic:
    var_type = None
    def __init__(self, p:parser):
        self.ast                        = p.ast
        self.ast_head                   = p.ast_head
        self.scope_stack                = list()
        self.next_scope_pending_vars    = dict()
        self.scope_index                = 0
        self.last_var                   = None
        self.exprs                      = dict()
        self.unique_variables_and_scope_access()
    
    def debug(self):
        print("PASSED SEMANTIC CHECK")
        print(f"EXPR RETURN {self.exprs}")

    def unique_variables_and_scope_access(self):
        self.scope_stack.append({})
        self.scope_index = 0
        self.traverse([self.ast_head], False, False)
        self.scope_stack.pop()
    
    def traverse(self, list_node_i, var_decl, append_next):
        for node_index in list_node_i:
            prod, edge = self.ast[node_index]
            if (prod == '<field_decl*>') or (prod == '<var_decl*>'):
                if (edge != None):
                    # if it is not epsilon make recursive call with the non-epsilon edge and var_decl=True and append_next=False. 
                    self.traverse(edge, True, False)
                    continue
                else:
                    # the edge is epsilon, so it is absent. This is basically a base case.
                    continue
            elif ((prod == '<method_args>') or (prod == '<method_args">')):
                # we are defining method args, these go on the next scope.
                if (edge != None):
                    self.traverse(edge, True, True)
                continue
            elif (prod == '<method_decl*>'):
                self.method_decl(edge)
                edge = edge[3:]
            elif (prod == '%type%'):
                self.var_type = self.ast[edge][PARENT]
            elif (prod == 'class'):
                self.var_type = prod
            elif (prod == '%id%'):
                self.id_(edge, var_decl, append_next)
            elif (prod == '{'):
                self.open_curly()
            elif (prod == '}'):
                self.closing_curly()
            elif (prod == '<assignment_statement>'):
                self.assignment_statement(edge, append_next)
            elif (prod == '<expr>'):
                if not self.exprs.get(node_index):
                    t = self.head_expr_return(node_index, append_next)

            if ((prod == ';') or (prod == '{')):
                var_decl = append_next = False

            # simply pass the next recursive call with the parameters 
            if is_nonterminal(prod) and (edge != None):
                self.traverse(edge, var_decl, append_next)
    
    def method_decl(self, edge):
        # we are defining a method, so collect the <type|void> and the %id%, then set it to start on the method args.
        # def 0 <type|void> 1 %id% 2 ( <method_args> ) <block> <method_decl*_aux>
        type_void, method_name = 1, 2
        temp = self.ast[edge[type_void]]
        if is_nonterminal(temp[PARENT]):
            if temp[PARENT] == '<type|void>':
                ptr = temp[PTR][0]
                t = self.ast[ptr]
                if is_pseudo_terminal(t[PARENT]): self.var_type = self.ast[t[PTR]][PARENT]
                else: self.var_type = t[PARENT]
        else:
            self.var_type = self.ast[temp[PTR]][PARENT]
        temp = self.ast[edge[method_name]]
        self.var_name = self.ast[temp[PTR]][PARENT]
        self.add_variable_to_scope(self.var_name, False)
    
    def id_(self, edge, var_decl, append_next):
        self.var_name = self.ast[edge][PARENT]
        if var_decl: 
            # we are declaring varibles, not using them. 
            self.add_variable_to_scope(self.var_name, append_next)
        elif (not var_decl): 
            # We are using variables that should have already been declared
            if self.var_type != 'class':
                self.check_if_var_exists(self.var_name)
            else:
                self.add_variable_to_scope(self.var_name, append_next)
    
    def open_curly(self):
        self.scope_stack.append({})
        self.scope_index += 1
        self.scope_stack[self.scope_index].update(self.next_scope_pending_vars)
        self.next_scope_pending_vars = dict()
    
    def closing_curly(self):
        self.scope_stack.pop()
        self.scope_index -= 1
    
    def assignment_statement(self, edge, append_next):
        # ['%id%', '<subscript>', '<assign_op>', '<expr>', ';']
        productions = [self.ast[x][PARENT] for x in edge]
        if productions == ['%id%', '<subscript>', '<assign_op>', '<expr>', ';']:
            t_expr = self.head_expr_return(edge[3], append_next)
            var_name = self.ast[self.ast[edge[0]][PTR]][PARENT]
            t_id   = self.return_t_of_var(var_name)
            if (t_id != t_expr):
                if (t_id == 'boolean') and (t_expr == 'int'):
                    print(f"Semantic error: '{var_name}' is type boolean and is being assigned an expression evaluated as int.")
                    exit(-1)

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
    
    def return_t_of_var(self, var_name):
        if self.scope_stack[self.scope_index].get(var_name):
            return self.scope_stack[self.scope_index][var_name]
        else:
            index = self.scope_index
            while index >= 0:
                if self.scope_stack[index].get(var_name):
                    return self.scope_stack[index][var_name]
                index -= 1
            self.var_not_declared(var_name)
    
    def head_expr_return(self, node_index, append_next):
        if self.exprs.get(node_index):
            return self.exprs[node_index]
        prod, edge = self.ast[node_index]
        productions = [self.ast[x][PARENT] for x in edge]
        edges       = [self.ast[x][CHILDREN] for x in edge]
        if   (productions == ['%id%', '<subscript>']):
            id_name = self.ast[self.ast[edge[0]][PTR]][PARENT]
            t = self.return_t_of_var(id_name)
            self.exprs[node_index] = t
            return t
        elif (productions == ['<literal>']):
            n = self.ast[self.ast[edge[PARENT]][CHILDREN][PARENT]][PARENT]
            if (n == '%int_literal%'):
                self.exprs[node_index] = 'int'
                return 'int'
            elif (n == '%char_literal%'):
                self.exprs[node_index] = 'int'
                return 'int'
            elif (n == '%bool_literal%'):
                self.exprs[node_index] = 'boolean'
                return 'boolean'
            else:
                print(f'Semantic error: {n} is not bool_literal, nor char_literal, nor int_literal.')
                exit(-1)
        elif (productions == ['<expr>', '<bin_op>', '<expr>']):
            lexpr = self.head_expr_return(edge[0], append_next)
            bin_op = self.ast[self.ast[edge[1]][PTR][PARENT]][PARENT]
            rexpr = self.head_expr_return(edge[2], append_next)
            if (lexpr in (INT, BOOLEAN)) and (rexpr in (INT, BOOLEAN)):
                if bin_op == '<arith_op>':
                    self.exprs[node_index] = INT
                    return INT
                elif bin_op in ('%rel_op%', '%eq_op%', '%cond_op%'):
                    self.exprs[node_index] = BOOLEAN
                    return BOOLEAN
                else:
                    print(f"Semantic error: expr {lexpr} {bin_op} {rexpr} is invalid because {bin_op} is not <arith_op> nor is any of %rel_op%, %eq_op%, %cond_op%.")
                    exit(-1)
            else:
                print(f"Semantic error: {lexpr} {bin_op} {rexpr} are non compatible expr type= ( <expr> <bin_op> <expr> )")
                exit(-1)
        elif (productions == ['%minus%', '<expr>']):
            first = productions[0]
            second = self.head_expr_return(edge[1], append_next)
            if second == 'int':
                self.exprs[node_index] = 'int'
                return 'int'
            elif second == 'boolean':
                print(f"Semantic error: {second} -<expr> cannot operate with boolean only with int.")
                exit(-1)
            else:
                print(f"Semantic error: {second} is not an int or boolean")
                exit(-1)
        elif (productions == ['!', '<expr>']):
            first = productions[0]
            second = self.head_expr_return(edge[1], append_next)
            if second == 'int':
                print(f"Semantic error: {first} operand cannot operate with int only with boolean.")
                exit(-1)
            elif second == 'boolean':
                self.exprs[node_index] = 'boolean'
                return 'boolean'
            else:
                print(f"Semantic error: {second} is not an int or boolean")
                exit(-1)
        elif (productions == ['(', '<expr>', ')']):
            first = productions[0]
            expr = self.head_expr_return(edge[1], append_next)
            second = productions[2]
            if (expr == 'int'):
                self.exprs[node_index] = 'int'
                return 'int'
            elif (expr == 'boolean'):
                self.exprs[node_index] = 'boolean'
                return 'boolean'
            else:
                print(f"Semantic error: expr returned {expr} which is not int nor boolean.")
                exit(-1)
        elif (productions == ['(', '<expr>', '<bin_op>', '<expr>', ')']):
            lparen = productions[0]
            lexpr = self.head_expr_return(edge[1], append_next)
            bin_op = self.ast[self.ast[edge[2]][PTR][PARENT]][PARENT]
            rexpr = self.head_expr_return(edge[3], append_next)
            rparen = productions[4]
            if (lexpr in (INT, BOOLEAN)) and (rexpr in (INT, BOOLEAN)):
                if bin_op == '<arith_op>':
                    self.exprs[node_index] = INT
                    return INT
                elif bin_op in ('%rel_op%', '%eq_op%', '%cond_op%'):
                    self.exprs[node_index] = BOOLEAN
                    return BOOLEAN
                else:
                    print(f"Semantic error: expr {lexpr} {bin_op} {rexpr} is invalid because {bin_op} is not <arith_op> nor is any of %rel_op%, %eq_op%, %cond_op%.")
                    exit(-1)
            else:
                print(f"Semantic error: {lexpr} {bin_op} {rexpr} are non compatible expr type= ( <expr> <bin_op> <expr> )")
                exit(-1)
