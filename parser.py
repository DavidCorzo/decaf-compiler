from scanner import scanner

if __name__ == '__main__':
    code = scanner("./src_code.txt", "./tokens.yaml")
    code.produce_automata()
    code.scan()
    print(code.linked_list_of_tokens)

class shift_reduce():
    def __init__(self, scanned_tokens):
        self.tokens = scanned_tokens
    
