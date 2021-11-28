.data
	# D_0: .asciiz "\n"
.text
main:
	li $t0 6
	# print(register)
	li $v0, 1
	move $a0, $t0
	syscall
	# End Program
	li $v0, 10
	syscall
	# start callee main header
	# addi $sp $sp -40
	# move $sp $fp
	# sw $fp 0($sp)
	# sw $ra 4($sp)
	# sw $s0 8($sp)
	# sw $s1 12($sp)
	# sw $s2 16($sp)
	# sw $s3 20($sp)
	# sw $s4 24($sp)
	# sw $s5 28($sp)
	# sw $s6 32($sp)
	# sw $s7 36($sp)
	# end callee main header
	# for loop
	# for init asignment statement
	# li $t7 0
	# # %assign% statement to i
	# sw $t7 0($sp) # returning i
	# T_0_for_begin:
	# lw $t6 0($sp) # <expr>::id i r-value id
	# li $t2 10
	# # $t6 < $t2 ?
	# bgt $t6 $t2 T_0_lt_false
	# beq $t6 $t2 T_0_lt_false
	# 	li $t6 1
	# 	j T_0_lt_fin
	# T_0_lt_false:
	# 	li $t6 0
	# 	j T_0_lt_fin
	# T_0_lt_fin:
	# beq $t6 $zero T_0_for_end
	# lw $t1 0($sp)
	# # print register/var
	# li $v0, 1
	# move $a0, $t1
	# syscall
	# # print str
	# li $v0, 4
	# la $a0, D_0
	# syscall
	# li $t3 1
	# move $t3 $v0 # return expr
	# j T_0_calle_ender
	# li $t0 1
	# # %assign_inc% statement to i
	# lw $t5 0($sp) # fetching i
	# add $t5 $t5 $t0
	# sw $t5 0($sp) # returning i
	# j T_0_for_begin
	# T_0_for_end:
	# li $t7 0
	# move $t7 $v0 # return expr
	# j T_0_calle_ender
	# # begin callee main ender
	# T_0_calle_ender:
	# addi $sp $sp 0 # field_decl dealloc
	# lw $fp 0($sp)
	# sw $ra 4($sp)
	# sw $s0 8($sp)
	# sw $s1 12($sp)
	# sw $s2 16($sp)
	# sw $s3 20($sp)
	# sw $s4 24($sp)
	# sw $s5 28($sp)
	# sw $s6 32($sp)
	# sw $s7 36($sp)
	# move $fp $sp
	# # End Program
	# li $v0, 10
	# syscall
	# end callee main ender
