.data
D_0: .asciiz "\n"
D_1: .asciiz "Odd\n"
D_2: .asciiz "i="
D_3: .asciiz " -> i*i -> "
D_4: .asciiz "\n"
D_5: .asciiz "j="
D_6: .asciiz " -> (j / 8) -> "
D_7: .asciiz "\n"
D_8: .asciiz "j="
D_9: .asciiz " -> (j + 3) -> \n"
D_10: .asciiz "\n"
D_11: .asciiz "j="
D_12: .asciiz " -> (j - 30) -> \n"
D_13: .asciiz "\n"
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
addi $sp $sp -8
li $t0 0
sw $t0 0($sp) T_0_for_begin:
lw $t3 0($sp) li $t1 10
bgt $t3 $t1 T_0_lt_false
beq $t3 $t1 T_0_lt_false
li $t3 1
j T_0_lt_fin
T_0_lt_false:
li $t3 0
j T_0_lt_fin
T_0_lt_fin:
beq $t3 $zero T_0_for_end
lw $t7 0($sp) li $t2 2
div $t7 $t2
mfhi $t7
li $t6 0
bne $t7 $t6 T_0_eq_false
li $t7 1
j T_0_eq_fin
T_0_eq_false:
li $t7 0
j T_0_eq_fin
T_0_eq_fin:
beq $t7 $zero T_0_else
lw $t5 0($sp)
li $v0, 1
move $a0, $t5
syscall
li $v0, 4
la $a0, D_0
syscall
j T_0_e_if T_0_else:
li $v0, 4
la $a0, D_1
syscall
j T_0_e_if T_0_e_if:
li $t0 1
lw $t4 0($sp) add $t4 $t4 $t0
sw $t4 0($sp) j T_0_for_begin
T_0_for_end:
li $v0, 4
la $a0, D_2
syscall
lw $t3 0($sp)
li $v0, 1
move $a0, $t3
syscall
li $v0, 4
la $a0, D_3
syscall
lw $t1 0($sp) lw $t7 0($sp) mult $t1 $t7
mflo $t1
sw $t1 4($sp) lw $t6 4($sp)
li $v0, 1
move $a0, $t6
syscall
li $v0, 4
la $a0, D_4
syscall
li $v0, 4
la $a0, D_5
syscall
lw $t5 4($sp)
li $v0, 1
move $a0, $t5
syscall
li $v0, 4
la $a0, D_6
syscall
lw $t0 4($sp) li $t4 8
div $t0 $t4
mflo $t0
sw $t0 4($sp) lw $t1 4($sp)
li $v0, 1
move $a0, $t1
syscall
li $v0, 4
la $a0, D_7
syscall
li $v0, 4
la $a0, D_8
syscall
lw $t7 4($sp)
li $v0, 1
move $a0, $t7
syscall
li $v0, 4
la $a0, D_9
syscall
lw $t2 4($sp) li $t6 3
add $t2 $t2 $t6
sw $t2 4($sp) lw $t0 4($sp)
li $v0, 1
move $a0, $t0
syscall
li $v0, 4
la $a0, D_10
syscall
li $v0, 4
la $a0, D_11
syscall
lw $t4 4($sp)
li $v0, 1
move $a0, $t4
syscall
li $v0, 4
la $a0, D_12
syscall
lw $t3 4($sp) li $t1 30
sub $t3 $t3 $t1
sw $t3 4($sp) lw $t2 4($sp)
li $v0, 1
move $a0, $t2
syscall
li $v0, 4
la $a0, D_13
syscall
addi $sp $sp 8
T_0_calle_ender:
lw $fp 0($sp)
lw $ra 4($sp)
lw $s0 8($sp)
lw $s1 12($sp)
lw $s2 16($sp)
lw $s3 20($sp)
lw $s4 24($sp)
lw $s5 28($sp)
lw $s6 32($sp)
lw $s7 36($sp)
move $sp $fp
li $v0, 10
syscall
