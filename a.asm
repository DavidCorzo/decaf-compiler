.data
 	endl: .asciiz "\n"

.text
main:
	# {'a': ['boolean', 0], 'b': ['int', 1]}
	addi $sp $sp -5 # field_decl & methods alloc
	# stack frame allocation
	sw $ra 0($sp)
	sw $s0 4($sp)
	sw $s1 8($sp)
	sw $s2 12($sp)
	sw $s3 16($sp)
	sw $s4 20($sp)
	sw $s5 24($sp)
	sw $s6 28($sp)
	sw $s7 32($sp)
	sw $fp 36($sp)
	# {'c': ['int', 0], 'e': ['boolean', 4]}
	addi $sp $sp -5 # var alloc
	li $t3 1
	sw $t3 13($sp)
	lw $t6 13($sp)
	li $t5 16
	add $t6 $t6 $t5
	li $t4 4
	mult $t6 $t4
	mflo $t6
	sw $t6 14($sp)
	addi $sp $sp 5 # out of scope deallocation
	addi $sp $sp 40 # frame dealloc
	j end_program
	addi $sp $sp 45 # out of scope deallocation
	j end_program
MBexp:
	addi $sp $sp -40
	# stack frame allocation
	sw $ra 0($sp)
	sw $s0 4($sp)
	sw $s1 8($sp)
	sw $s2 12($sp)
	sw $s3 16($sp)
	sw $s4 20($sp)
	sw $s5 24($sp)
	sw $s6 28($sp)
	sw $s7 32($sp)
	sw $fp 36($sp)
	# {'num': ['int', 0], 'n': ['int', 4]}
	addi $sp $sp -8 # var alloc
	lw $t7 0($sp)
	lw $t2 0($sp)
	mult $t7 $t2
	mflo $t7
	sw $t7 4($sp)
	lw $t0 4($sp)
	move $t0 $v1
	addi $sp $sp 8 # out of scope deallocation
	addi $sp $sp 40 # frame dealloc
	addi $sp $sp -40
end_program:
	# end program
	li $v0, 10
	syscall
