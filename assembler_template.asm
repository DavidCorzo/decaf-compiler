.text 
main:
    li $t0 3
    li $t1 4

    bgt $t0 $t1 false
        li $t0 1
        j fin
    false:
        li $t1 0
        j fin
    fin:
