.MODEL SMALL
.STACK 100h
.DATA
	vvar1 db "Hello", 10,"$"
	vvar2 db 6,7 dup (0)
	vnothing db "     $"
	vi db ?
.CODE
start:
	mov ax, @data
	mov ds, ax
	mov ah, 10
	mov dx, offset vvar2
	int 21h
	mov [vi], 2
label22:
;; -- WHILE --
;; -- SUB --
	xor ax, ax
	mov al, [vi]
	sub ax, 2
;; -- ADD --
	add al, offset vvar1
;; -- MEMREAD --
	mov si, ax
	xor ax, ax
	mov al, [si]
	mov bx, ax
;; -- ADD --
	xor ax, ax
	mov al, offset vvar2
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
	cmp ax, bx
	jne label42
;; -- ADD --
	xor ax, ax
	mov al, [vi]
	add ax, 1
	mov [vi], al
	jmp label22
label42:
;; -- IF --
	mov bl, [vi]
	mov ax, 7
	cmp ax, bx
	jne label57
	xor ax, ax
	mov ah, 9
	mov dx, offset vvar1
	int 21h
	jmp label62
label57:
	xor ax, ax
	mov ah, 9
	mov dx, offset vnothing
	int 21h
label62:
	mov ah, 4Ch
	int 21h
END start