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
	lb $t0 None($sp) # r-value id
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
	li $t1 1
	lw $t3 44($sp) # r-value id
	lw $t6 44($sp) # r-value id
	sw None 0($sp)
	lw $t4 0($sp) # r-value id
	li $t5 1
	sb $t5 None($sp)
	li $t7 16
	li $t2 4
	sw None None($sp)
