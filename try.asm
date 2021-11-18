.data
    text:  .asciiz "Enter a number: "

.text
main:
    # Printing out the text
    li $v0, 4
    la $a0, text
    syscall

    # End Program
    li $v0, 10
    syscall
