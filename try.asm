.data
str: .asciiz "\n"

.text
main:
    addi $sp $sp -8
    li $t0 10 # 4
    li $t1 14 # 4
    sw $t0, 0($sp)
    sw $t1, 4($sp)
    lw $t0, 0($sp)
    lw $t1, 4($sp)
end:
    # print(register)
    li $v0, 1
    move $a0, $t0
    syscall
    # print(str1)
    li $v0, 4
    la $a0, str
    syscall 
    # 
    addi $sp $sp 8
    # print(register)
    li $v0, 1
    move $a0, $t0
    syscall
    # End Program
    li $v0, 10
    syscall
