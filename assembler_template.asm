.data
    str: .asciiz "hello world\n"
.text 
main:
    # and
    li $t0 0
    li $t1 1
    # print(str1)
    li $v0, 4
    la $a0, str
    syscall 
    # print(register)
    li $v0, 1
    move $a0, $t0
    syscall
    # print(register)
    li $v0, 1
    move $a0, $t1
    syscall
    # End Program
    li $v0, 10
    syscall

    
#boolean a;
#int b;
#int y1[1];
#def int exp(int num, boolean r, int y) {
#    num = (num + 1);
#    print_var(num);
#    print_str("string hello world ???");
#    if (num == 2) {
#        print_str("num is equal to 2");
#    }
#    else {
#        print_str("num is not equal to 2");
#    }
#    return num;
#}
#def void y(int j, int k, boolean g) {
#    print_var(y1);
#}
#def void j() {
#    print_var(b);
#}
