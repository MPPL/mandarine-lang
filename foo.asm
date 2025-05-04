.MODEL SMALL
.STACK 100h
.DATA
	vtest db "Test String", 10,"$"
	vinput db 255,256 dup (0)
	vbin db 16,17 dup (0)
	vdec db 16,17 dup (0)
	vhex db 16,17 dup (0)
	voct db 16,17 dup (0)
	vi db ?
	vj db ?
	vtmp1 db ?
	vtmp2 db ?
	vtmp3 db ?
.CODE
start:
	mov ax, @data
	mov ds, ax
	mov ah, 10
	mov dx, offset vinput
	int 21h
	mov [vi], 0
	mov [vj], 0
	mov [vtmp1], 0
	mov [vtmp2], 0
	mov [vtmp3], 0
label54:
;; -- WHILE --
	xor bx, bx
	mov bl, [vi]
;; -- ADD --
	xor ax, ax
	mov ax, offset vinput
	add ax, 1
;; -- MEMREAD --
	mov si, ax
	xor ax, ax
	mov al, [si]
	cmp ax, bx
	jg bar61
	jmp label142
bar61:
	mov dx, offset vtest
	xor ax, ax
	mov ah, 9
	int 21h
;; -- ADD --
	mov ax, 2
	add al, [vi]
;; -- ADD --
	add ax, offset vinput
;; -- MEMREAD --
	mov si, ax
	xor ax, ax
	mov al, [si]
;; -- SUB --
	sub ax, 48
	mov [vtmp1], al
	mov [vj], 0
;; -- ADD --
	xor ax, ax
	mov ax, offset vbin
	add ax, 1
	mov [vtmp2], al
label88:
;; -- WHILE --
	xor bx, bx
	mov bl, [vj]
	mov ax, 3
	cmp ax, bx
	jg bar92
	jmp label128
bar92:
;; -- ADD --
	xor ax, ax
	mov al, [vtmp2]
	add ax, 1
	mov [vtmp2], al
;; -- MOD --
	xor ax, ax
	mov al, [vtmp1]
	mov cx, 2
	div cl
	mov al, ah
	xor ah, ah
;; -- ADD --
	add ax, 48
	mov [vtmp3], al
;; -- MEMWRITE --
	mov bl, [vtmp3]
	mov si, WORD PTR [vtmp2]
	mov BYTE PTR [si], bl
;; -- DIV --
	xor ax, ax
	mov al, [vtmp1]
	mov cx, 2
	div cl
	xor ah, ah
	mov [vtmp1], al
;; -- ADD --
	xor ax, ax
	mov al, [vj]
	add ax, 1
	mov [vj], al
	jmp label88
label128:
;; -- ADD --
	xor ax, ax
	mov al, [vi]
	add ax, 1
	mov [vi], al
	jmp label54
label142:
;; -- ADD --
	xor ax, ax
	mov al, [vtmp2]
	add ax, 1
	mov [vtmp2], al
;; -- MEMWRITE --
	mov si, WORD PTR [vtmp2]
	mov BYTE PTR [si], 36
;; -- ADD --
	xor ax, ax
	mov ax, offset vbin
	add ax, 2
	mov dx, ax
	xor ax, ax
	mov ah, 9
	int 21h
	mov ah, 4Ch
	int 21h
END start