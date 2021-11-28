.data
D_0: .asciiz "\n"
D_1: .asciiz "\n"
D_2: .asciiz "\n"
D_3: .asciiz "\n"
.text
main:
move $fp $sp
addi $sp $sp -40
sw $fp 0($sp)
sw $ra 4($sp)
sw $s0 8($sp)
sw $s1 12($sp)
sw $s2 16($sp)
sw $s3 20($sp)
sw $s4 24($sp)
sw $s5 28($sp)
sw $s6 32($sp)
sw $s7 36($sp)
addi $sp $sp -4
li $t2 0
sw $t2 0($sp) T_0_for_begin:
lw $t1 0($sp) li $t5 10
bgt $t1 $t5 T_0_lt_false
beq $t1 $t5 T_0_lt_false
li $t1 1
j T_0_lt_fin
T_0_lt_false:
li $t1 0
j T_0_lt_fin
T_0_lt_fin:
beq $t1 $zero T_0_for_end
lw $t3 0($sp) li $t4 2
div $t3 $t4
mfhi $t3
li $t6 0
bne $t3 $t6 T_0_eq_false
li $t3 1
j T_0_eq_fin
T_0_eq_false:
li $t3 0
j T_0_eq_fin
T_0_eq_fin:
beq $t3 $zero T_0_if_false
lw $t7 0($sp)
li $v0, 1
move $a0, $t7
syscall
li $v0, 4
la $a0, D_2
syscall
T_0_if_false:
li $t2 1
lw $t0 0($sp) add $t0 $t0 $t2
sw $t0 0($sp) j T_0_for_begin
T_0_for_end:
li $v0, 4
la $a0, D_3
syscall
move $t0 $s0
move $t1 $s1
move $t2 $s2
move $t3 $s3
move $t4 $s4
move $t5 $s5
move $t6 $s6
move $t7 $s7
addi $sp $sp -12
li $t1 56
sw $t1 0($sp)
li $t5 56
li $t3 2
mult $t5 $t3
mflo $t5
sw $t5 4($sp)
li $t4 7
sw $t4 8($sp)
jal method_sum
addi $sp $sp 12
move $s0 $t0
move $s1 $t1
move $s2 $t2
move $s3 $t3
move $s4 $t4
move $s5 $t5
move $s6 $t6
move $s7 $t7
addi $sp $sp 4
T_1_calle_ender:
lw $fp 0($sp)
sw $ra 4($sp)
sw $s0 8($sp)
sw $s1 12($sp)
sw $s2 16($sp)
sw $s3 20($sp)
sw $s4 24($sp)
sw $s5 28($sp)
sw $s6 32($sp)
sw $s7 36($sp)
move $sp $fp
li $v0, 10
syscall
method_sum: move $fp $sp
addi $sp $sp -40
sw $fp 0($sp)
sw $ra 4($sp)
sw $s0 8($sp)
sw $s1 12($sp)
sw $s2 16($sp)
sw $s3 20($sp)
sw $s4 24($sp)
sw $s5 28($sp)
sw $s6 32($sp)
sw $s7 36($sp)
lw $t0 40($sp) lw $t1 44($sp) add $t0 $t0 $t1
sw $t0 40($sp) lw $t3 40($sp)
li $v0, 1
move $a0, $t3
syscall
li $v0, 4
la $a0, D_0
syscall
lw $t4 44($sp)
li $v0, 1
move $a0, $t4
syscall
li $v0, 4
la $a0, D_1
syscall
lw $t6 48($sp)
li $v0, 1
move $a0, $t6
syscall
li $t7 0
move $t7 $v0 j T_0_calle_ender
T_0_calle_ender:
lw $fp 0($sp)
sw $ra 4($sp)
sw $s0 8($sp)
sw $s1 12($sp)
sw $s2 16($sp)
sw $s3 20($sp)
sw $s4 24($sp)
sw $s5 28($sp)
sw $s6 32($sp)
sw $s7 36($sp)
move $sp $fp
jr $ra
