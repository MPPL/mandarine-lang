.MODEL SMALL
.STACK 100h
.DATA
	var1 db "Hello, Mandarine!", 10,"$"
	i db ?
.CODE
start:
	mov ax, @data
	mov ds, ax
	mov ah, 9
	mov dx, offset var1
	int 21h
	mov [i], 0
label14:
	mov bl, [i]
	mov ax, 5
	cmp ax, bx
	jl label31
	xor ax, ax
	mov ah, 9
	mov dx, offset var1
	int 21h
	xor ax, ax
	mov al, [i]
	add ax, 1
	mov [i], al
	jmp label14
label31:
	mov ah, 4Ch
	int 21h
END start