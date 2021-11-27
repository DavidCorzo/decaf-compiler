.data
	endl: .asciiz "\n"
main:
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
	addi $sp $sp -9 # field_decl alloc
	lb $t4 0($sp) # <expr>::id a r-value id
	# $t4 + $t5 ?
	add $t4 $t4 $t5
	# $t4 * $t1 ?
	mult $t4 $t1
	mflo $t4
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
	jr $ra
method_exp: # method tag
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
	li $t7 1
	lw $t0 44($sp) # <expr>::id num r-value id
	lw $t6 44($sp) # <expr>::id num r-value id
	# $t0 * $t6 ?
	mult $t0 $t6
	mflo $t0
	# %assign% statement to n
	sw $t0 0($sp) # returning n
	lw $t5 44($sp) # <expr>::id num r-value id
	lw $t1 44($sp) # <expr>::id num r-value id
	# $t5 > $t1 ?
	blt $t5 $t1 T_0_gt_false
	beq $t5 $t1 T_0_gt_false
		li $t5 1
		j T_0_gt_fin
	T_0_gt_false:
		li $t5 0
		j T_0_gt_fin
	T_0_gt_fin:
	# %assign% statement to n
	sw $t5 0($sp) # returning n
	lw $t3 0($sp) # <expr>::id n r-value id
	move $t3 $v0 # return expr
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
method_y: # method tag
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
	li $t0 1
	# %assign% statement to a
	sb $t0 0($sp) # returning a
	li $t5 16
	li $t1 4
	# %assign% statement to b
	sw $t4 1($sp) # returning b
