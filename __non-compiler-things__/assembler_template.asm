.data
    str: .asciiz "hello world\n"
.text 
main:
    li $t0 0
    beq $t0 $zero else 
        # something if true
        j end_if
    else:
        # something if false
        j end_if
    end_if:
