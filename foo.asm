.MODEL SMALL
.STACK 100h
.DATA
	vtest db "Test String", 10,"$"
	vinput db 255,256 dup (0)
	vbin db 255,256 dup (0)
	vdec db 16,17 dup (0)
	vhex db 16,17 dup (0)
	voct db 16,17 dup (0)
	vi db ?
	vj db ?
	vtmp1 db ?
	vtmp2 dw ?
	vtmp3 db ?
.CODE
start:
	mov ax, @data
	mov ds, ax
;; -- DOS -- 10 --
	mov dx, offset vinput
	mov ah, 10
	int 21h
;; -- ADD --
	mov si, offset vinput
	mov ax, si
	add ax, 1
;; -- MEMREAD --
	mov si, ax
	mov ax, [si]
	mov byte [vi], al
	mov byte [vj], 0
	mov byte [vtmp1], 0
;; -- MUL --
	mov al, byte [vi]
	mov dl, 3
	mul dl
;; -- ADD --
	add ax, 1
;; -- ADD --
	mov si, offset vbin
	add ax, si
	mov word [vtmp2], ax
	mov byte [vtmp3], 0
label63:
;; -- WHILE --
	mov bl, byte [vi]
	mov ax, 0
	cmp bx, ax
	jg bar67
	jmp label142
bar67:
;; -- DOS -- 9 --
	mov dx, offset vtest
	mov ah, 9
	int 21h
;; -- ADD --
	mov ax, 1
	add al, byte [vi]
;; -- ADD --
	mov si, offset vinput
	add ax, si
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- SUB --
	sub ax, 48
	mov byte [vtmp1], al
	mov byte [vj], 3
label88:
;; -- WHILE --
	mov bl, byte [vj]
	mov ax, 0
	cmp bx, ax
	jg bar92
	jmp label128
bar92:
;; -- SUB --
	mov ax, word [vtmp2]
	sub ax, 1
	mov word [vtmp2], ax
;; -- MOD --
	mov al, byte [vtmp1]
	mov dl, 2
	div dl
	mov al, ah
	xor ah, ah
;; -- ADD --
	add ax, 48
	mov byte [vtmp3], al
;; -- MEMWRITE --
	mov di, word [vtmp2]
	mov si, offset vtmp3
	mov si, offset vtmp3
	movsb
;; -- DIV --
	mov al, byte [vtmp1]
	mov dl, 2
	div dl
	xor ah, ah
	mov byte [vtmp1], al
;; -- SUB --
	mov al, byte [vj]
	sub ax, 1
	mov byte [vj], al
	jmp label88
label128:
;; -- SUB --
	mov al, byte [vi]
	sub ax, 1
	mov byte [vi], al
	jmp label63
label142:
;; -- ADD --
	mov si, offset vinput
	mov ax, si
	add ax, 1
;; -- MEMREAD --
	mov si, ax
	mov ax, [si]
;; -- MUL --
	mov dl, 3
	mul dl
;; -- ADD --
	add ax, 1
;; -- ADD --
	mov si, offset vbin
	add ax, si
	mov word [vtmp2], ax
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov word ptr [di], 36
;; -- ADD --
	mov si, offset vbin
	mov ax, si
	add ax, 1
;; -- DOS -- 9 --
	mov dx, ax
	mov ah, 9
	int 21h
	mov ah, 4Ch
	int 21h
END start