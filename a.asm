
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
