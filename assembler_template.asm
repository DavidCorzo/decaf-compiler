.text 
main:
    # and
    li $t0 0
    li $t1 1
    bne $t0 $zero true
    bne $t1 $zero true
        li $t0 0
        j fin
    true:
        li $t0 1
        j fin
    fin:
