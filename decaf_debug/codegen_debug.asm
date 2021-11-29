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
	# start callee main header
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
	# end callee main header
	# var_decl alloc
	addi $sp $sp -8
	# for loop
	# for init asignment statement
	li $t0 0
	# %assign% statement to i
	sw $t0 0($sp) # returning i
	T_0_for_begin:
	lw $t3 0($sp) # <expr>::id i r-value id
	li $t1 10
	# $t3 < $t1 ?
	bgt $t3 $t1 T_0_lt_false
	beq $t3 $t1 T_0_lt_false
		li $t3 1
		j T_0_lt_fin
	T_0_lt_false:
		li $t3 0
		j T_0_lt_fin
	T_0_lt_fin:
	beq $t3 $zero T_0_for_end
	lw $t7 0($sp) # <expr>::id i r-value id
	li $t2 2
	# $t7 % $t2 ?
	div $t7 $t2
	mfhi $t7
	li $t6 0
	# $t7 == $t6 ?
	bne $t7 $t6 T_0_eq_false
		li $t7 1
		j T_0_eq_fin
	T_0_eq_false:
		li $t7 0
		j T_0_eq_fin
	T_0_eq_fin:
	# if $t7 ?
	beq $t7 $zero T_0_else
	lw $t5 0($sp)
	# print register/var
	li $v0, 1
	move $a0, $t5
	syscall
	# print str
	li $v0, 4
	la $a0, D_0
	syscall
	j T_0_e_if # jump to end if
	# else or end_if
	T_0_else:
	# print str
	li $v0, 4
	la $a0, D_1
	syscall
	j T_0_e_if # jump to end if
	T_0_e_if:
	li $t0 1
	# %assign_inc% statement to i
	lw $t4 0($sp) # fetching i
	add $t4 $t4 $t0
	sw $t4 0($sp) # returning i
	j T_0_for_begin
	T_0_for_end:
	# print str
	li $v0, 4
	la $a0, D_2
	syscall
	lw $t3 0($sp)
	# print register/var
	li $v0, 1
	move $a0, $t3
	syscall
	# print str
	li $v0, 4
	la $a0, D_3
	syscall
	lw $t1 0($sp) # <expr>::id i r-value id
	lw $t7 0($sp) # <expr>::id i r-value id
	# $t1 * $t7 ?
	mult $t1 $t7
	mflo $t1
	# %assign% statement to j
	sw $t1 4($sp) # returning j
	lw $t6 4($sp)
	# print register/var
	li $v0, 1
	move $a0, $t6
	syscall
	# print str
	li $v0, 4
	la $a0, D_4
	syscall
	# print str
	li $v0, 4
	la $a0, D_5
	syscall
	lw $t5 4($sp)
	# print register/var
	li $v0, 1
	move $a0, $t5
	syscall
	# print str
	li $v0, 4
	la $a0, D_6
	syscall
	lw $t0 4($sp) # <expr>::id j r-value id
	li $t4 8
	# $t0 / $t4 ?
	div $t0 $t4
	mflo $t0
	# %assign% statement to j
	sw $t0 4($sp) # returning j
	lw $t1 4($sp)
	# print register/var
	li $v0, 1
	move $a0, $t1
	syscall
	# print str
	li $v0, 4
	la $a0, D_7
	syscall
	# print str
	li $v0, 4
	la $a0, D_8
	syscall
	lw $t7 4($sp)
	# print register/var
	li $v0, 1
	move $a0, $t7
	syscall
	# print str
	li $v0, 4
	la $a0, D_9
	syscall
	lw $t2 4($sp) # <expr>::id j r-value id
	li $t6 3
	# $t2 + $t6 ?
	add $t2 $t2 $t6
	# %assign% statement to j
	sw $t2 4($sp) # returning j
	lw $t0 4($sp)
	# print register/var
	li $v0, 1
	move $a0, $t0
	syscall
	# print str
	li $v0, 4
	la $a0, D_10
	syscall
	# print str
	li $v0, 4
	la $a0, D_11
	syscall
	lw $t4 4($sp)
	# print register/var
	li $v0, 1
	move $a0, $t4
	syscall
	# print str
	li $v0, 4
	la $a0, D_12
	syscall
	lw $t3 4($sp) # <expr>::id j r-value id
	li $t1 30
	# $t3 - $t1 ?
	sub $t3 $t3 $t1
	# %assign% statement to j
	sw $t3 4($sp) # returning j
	lw $t2 4($sp)
	# print register/var
	li $v0, 1
	move $a0, $t2
	syscall
	# print str
	li $v0, 4
	la $a0, D_13
	syscall
	# var_decl dealloc
	addi $sp $sp 8
	# begin callee main ender
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
	# End Program
	li $v0, 10
	syscall
	# end callee main ender
