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
	vtmp1 dw ?
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
	add ax, 1
;; -- MEMREAD --
	mov byte [vi], al
	mov byte [vj], 0
	mov word [vtmp1], 0
;; -- ADD --
	add ax, 1
;; -- MEMREAD --
;; -- MUL --
	mov dx, 3
	mul dx
;; -- ADD --
	add ax, 1
;; -- ADD --
	add ax, offset vbin
	mov word [vtmp2], ax
	mov byte [vtmp3], 0
label66:
;; -- WHILE --
	xor bx, bx
	mov bl, byte [vi]
	mov ax, 0
	cmp bx, ax
	jg bar70
	jmp label147
bar70:
;; -- DOS -- 9 --
	mov dx, offset vtest
	mov ah, 9
	int 21h
;; -- SUB --
	sub ax, 1
;; -- ADD --
	xor ax, ax
	add al, byte [vi]
;; -- ADD --
	add ax, 2
;; -- MEMREAD --
;; -- SUB --
	sub ax, 48
	mov word [vtmp1], ax
	mov byte [vj], 3
label93:
;; -- WHILE --
	xor bx, bx
	mov bl, byte [vj]
	mov ax, 0
	cmp bx, ax
	jg bar97
	jmp label133
bar97:
;; -- SUB --
	sub ax, 1
	mov di, offset vtmp2
	mov si, offset vtmp2
	mov word [di], si
;; -- MOD --
	mov dl, 2
	div dl
	mov al, ah
	xor ah, ah
;; -- ADD --
	add ax, vtmp1
	mov byte [vtmp3], 48
;; -- MEMWRITE --
;; -- DIV --
	mov dl, 2
	div dl
	xor ah, ah
	mov di, offset vtmp1
	mov si, offset vtmp1
	mov word [di], si
;; -- SUB --
	sub ax, 1
	mov di, offset vj
	mov si, offset vj
	movsb
	jmp label93
label133:
;; -- SUB --
	sub ax, 1
	mov di, offset vi
	mov si, offset vi
	movsb
	jmp label66
label147:
;; -- ADD --
	add ax, 1
;; -- MEMREAD --
;; -- MUL --
	mov dx, 3
	mul dx
;; -- ADD --
	add ax, 1
;; -- ADD --
	add ax, offset vbin
	mov word [vtmp2], ax
;; -- MEMWRITE --
;; -- ADD --
	add ax, 1
;; -- DOS -- 9 --
	mov dx, offset vbin
	mov ah, 9
	int 21h
	mov ah, 4Ch
	int 21h
END start