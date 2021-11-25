.data
str: .asciiz "\n"

.text
main:

    beq 

    # li $t0 10
    # li $t1 1
    # for:
    #     beq $t0, $zero, end_cond
    #     addi $t1 $t1 1
    


    
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
