.data
str: .asciiz "\nSuccessful"
.text
main:
	addi $sp $sp -12 # scope variable allocation 2
	li $t2 10
	li $t6 4
	add $t2 $t2 $t6
	li $t3 10
	mult $t2 $t3
	mflo $t2
	li $t4 1
	li $t5 3
	sub $t4 $t4 $t5
	mult $t2 $t4
	mflo $t2
	
	# print(register)
	li $v0, 1
	move $a0, $t2
	syscall
	
	sw $t2 0($sp)
	li $t7 9
	sw $t7 8($sp)
	li $t8 6
	lw $t1 8($sp)
	add $t8 $t8 $t1
	sw $t8 4($sp)
	addi $sp $sp 12 # out of scope deallocation
	j end_program
end_program:
	# print(str1)
	li $v0, 4
	la $a0, str
	syscall 
	# end program
	li $v0, 10
	syscall
