.data
	D_0: .asciiz "\n"
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
	addi $sp $sp -4
	# for loop
	# for init asignment statement
	li $t1 0
	# %assign% statement to i
	sw $t1 0($sp) # returning i
	T_0_for_begin:
	lw $t2 0($sp) # <expr>::id i r-value id
	li $t0 10
	# $t2 < $t0 ?
	bgt $t2 $t0 T_0_lt_false
	beq $t2 $t0 T_0_lt_false
		li $t2 1
		j T_0_lt_fin
	T_0_lt_false:
		li $t2 0
		j T_0_lt_fin
	T_0_lt_fin:
	beq $t2 $zero T_0_for_end
	lw $t3 0($sp) # <expr>::id i r-value id
	li $t6 2
	# $t3 % $t6 ?
	div $t3 $t6
	mfhi $t3
	li $t7 0
	# $t3 == $t7 ?
	bne $t3 $t7 T_0_eq_false
		li $t3 1
		j T_0_eq_fin
	T_0_eq_false:
		li $t3 0
		j T_0_eq_fin
	T_0_eq_fin:
	# if $t3 ?
	beq $t3 $zero T_0_if_false
	lw $t5 0($sp)
	# print register/var
	li $v0, 1
	move $a0, $t5
	syscall
	# print str
	li $v0, 4
	la $a0, D_0
	syscall
	# else or end_if
	T_0_if_false:
	li $t1 1
	# %assign_inc% statement to i
	lw $t4 0($sp) # fetching i
	add $t4 $t4 $t1
	sw $t4 0($sp) # returning i
	j T_0_for_begin
	T_0_for_end:
	# var_decl dealloc
	addi $sp $sp 4
	# begin callee main ender
	T_0_calle_ender:
	addi $sp $sp 0 # field_decl dealloc
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
	# End Program
	li $v0, 10
	syscall
	# end callee main ender
