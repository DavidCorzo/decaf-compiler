.data
	D_endl: .asciiz "\n"
	D_0: .asciiz "string hello world ???"
	D_1: .asciiz "num is equal to 2"
	D_2: .asciiz "num is not equal to 2"
main:
	# start callee main header
	addi $sp $sp -40
	move $sp $fp
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
	addi $sp $sp -9 # field_decl alloc
	# for loop
	# for init asignment statement
	li $t7 0
	# %assign% statement to i
	sw $t7 0($sp) # returning i
	T_0_for_begin:
	lw $t1 0($sp) # <expr>::id i r-value id
	li $t3 10
	# $t1 < $t3 ?
	bgt $t1 $t3 T_0_lt_false
	beq $t1 $t3 T_0_lt_false
		li $t1 1
		j T_0_lt_fin
	T_0_lt_false:
		li $t1 0
		j T_0_lt_fin
	T_0_lt_fin:
	beq $t1 $zero T_0_for_end
	lw $t2 0($sp)
	# print register/var
	li $v0, 1
	move $a0, $t2
	syscall
	# print endl
	li $v0, 4
	la $a0, D_endl
	syscall
	li $t6 1
	# %assign_inc% statement to i
	lw $t0 0($sp) # fetching i
	add $t0 $t0 $t6
	sw $t0 0($sp) # returning i
	j T_0_for_begin
	li $t4 0
	move $t4 $v0 # return expr
	j T_3_calle_ender
	# begin callee main ender
	T_3_calle_ender:
	addi $sp $sp 9 # field_decl dealloc
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
	move $fp $sp
	# End Program
	li $v0, 10
	syscall
	# end callee main ender
method_exp: # method tag
	# begin callee header
	addi $sp $sp -40
	move $sp $fp
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
	# end callee header
	lw $t4 40($sp) # <expr>::id num r-value id
	li $t7 1
	# $t4 + $t7 ?
	add $t4 $t4 $t7
	# %assign% statement to num
	sw $t4 40($sp) # returning num
	lw $t1 40($sp)
	# print register/var
	li $v0, 1
	move $a0, $t1
	syscall
	# print endl
	li $v0, 4
	la $a0, D_endl
	syscall
	# print str
	li $v0, 4
	la $a0, D_0
	syscall
	lw $t2 40($sp) # <expr>::id num r-value id
	li $t3 2
	# $t2 == $t3 ?
	bne $t2 $t3 T_0_eq_false
		li $t2 1
		j T_0_eq_fin
	T_0_eq_false:
		li $t2 0
		j T_0_eq_fin
	T_0_eq_fin:
	# if $t2 ?
	beq $t2 $zero T_0_if_false
	# print str
	li $v0, 4
	la $a0, D_1
	syscall
	# else or end_if
	T_0_if_false:
	# print str
	li $v0, 4
	la $a0, D_2
	syscall
	lw $t6 40($sp) # <expr>::id num r-value id
	move $t6 $v0 # return expr
	j T_0_calle_ender
	# begin callee ender
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
	move $fp $sp
	jr $ra
	# end callee ender
method_y: # method tag
	# begin callee header
	addi $sp $sp -40
	move $sp $fp
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
	# end callee header
	lw $t0 5($sp)
	# print register/var
	li $v0, 1
	move $a0, $t0
	syscall
	# print endl
	li $v0, 4
	la $a0, D_endl
	syscall
	# begin callee ender
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
	move $fp $sp
	jr $ra
	# end callee ender
method_j: # method tag
	# begin callee header
	addi $sp $sp -40
	move $sp $fp
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
	# end callee header
	lw $t4 1($sp)
	# print register/var
	li $v0, 1
	move $a0, $t4
	syscall
	# print endl
	li $v0, 4
	la $a0, D_endl
	syscall
	# begin callee ender
	T_2_calle_ender:
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
	move $fp $sp
	jr $ra
	# end callee ender
