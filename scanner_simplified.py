
def infix_to_postfix(self) -> str:
    self.postfix = ""
    stack   = []
    precedence = { # don't use 0, confuses the if's.
        '|': 1, '·': 2, '*': 3, '+': 4, '?': 5, 
    }
    ########################## EXPANDING RANGES #########################################
    new_infix = ""
    i = 0
    while (i < len(self.infix)):
        if (self.infix[i] == "["):
            ii = 0
            i += 1
            char_inside = ""
            while (self.infix[i] != ']'):
                char_inside += self.infix[i]
                if ((self.infix[i] == '-') and (ii != 0)):
                    char_inside = char_inside[:-2]
                    low_lim = self.infix[i-1]
                    high_lim = self.infix[i+1]
                    if ((low_lim in DIGITS) and (high_lim in DIGITS)):
                        for r in range(int(low_lim), int(high_lim) + 1):
                            char_inside += str(r)
                    elif ((low_lim in ascii_lowercase) and (high_lim in ascii_lowercase)):
                        for r in range(ord(low_lim), ord(high_lim) + 1):
                            char_inside += chr(r)
                    elif ((low_lim in ascii_uppercase) and (high_lim in ascii_uppercase)):
                        for r in range(ord(low_lim), ord(high_lim) + 1):
                            char_inside += chr(r)
                    else:
                        print("Error in range of regular expression.")
                        exit(-1)
                    i += 1
                ii += 1
                i  += 1
            new_infix += f"({'|'.join([x for x in char_inside])})"
        else:
            new_infix += self.infix[i]
        i += 1
    ########################## EXPANDING RANGES #########################################
    ########################## POSTFIX STRING GENERATION #########################################
    self.infix = new_infix
    i = 0
    while (i < len(self.infix)):
        char = self.infix[i]
        if char == '(': 
            stack.append(char)
        elif char == ')':
            while (stack[-1] != '('): 
                self.postfix += stack.pop()
            stack.pop()
        elif char in precedence.keys():
            while ( (len(stack) != 0) and  (precedence.get(char, 0) <= precedence.get(stack[-1], 0))):
                self.postfix += stack.pop()
            stack.append(char)
        else:
            self.postfix += char
        i += 1
    
    while len(stack) != 0:
        self.postfix += stack.pop()
    ########################## POSTFIX STRING GENERATION #########################################
    return self.postfix
