.MODEL SMALL
.STACK 100h
.DATA
	vbin_str db "BIN: $"
	vhex_str db "HEX: $"
	vdec_str db "DEC: $"
	vnl db "", 10,"$"
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
	mov es, ax
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
	mov [vi], al
	mov [vj], 0
	mov [vtmp1], 0
;; -- MUL --
	mov al, [vi]
	mov dl, 3
	mul dl
;; -- ADD --
	add ax, 1
;; -- ADD --
	mov si, offset vbin
	add ax, si
	mov [vtmp2], ax
	mov [vtmp3], 0
label75:
;; -- WHILE --
	mov bl, [vi]
	mov ax, 0
	cmp bx, ax
	jg bar79
	jmp label150
bar79:
;; -- ADD --
	mov ax, 1
	add al, [vi]
;; -- ADD --
	mov si, offset vinput
	add ax, si
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- SUB --
	sub ax, 48
	mov [vtmp1], al
	mov [vj], 3
label96:
;; -- WHILE --
	mov bl, [vj]
	mov ax, 0
	cmp bx, ax
	jg bar100
	jmp label136
bar100:
;; -- SUB --
	mov ax, [vtmp2]
	sub ax, 1
	mov [vtmp2], ax
;; -- MOD --
	mov al, [vtmp1]
	mov dl, 2
	div dl
	mov al, ah
	xor ah, ah
;; -- ADD --
	add ax, 48
	mov [vtmp3], al
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov si, offset vtmp3
	mov si, offset vtmp3
	movsb
;; -- DIV --
	mov al, [vtmp1]
	mov dl, 2
	div dl
	xor ah, ah
	mov [vtmp1], al
;; -- SUB --
	mov al, [vj]
	sub ax, 1
	mov [vj], al
	jmp label96
label136:
;; -- SUB --
	mov al, [vi]
	sub ax, 1
	mov [vi], al
	jmp label75
label150:
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
	mov [vtmp2], ax
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov word ptr [di], 36
;; -- DOS -- 9 --
	mov si, offset vbin_str
	mov dx, si
	mov ah, 9
	int 21h
;; -- ADD --
	mov si, offset vbin
	mov ax, si
	add ax, 1
;; -- DOS -- 9 --
	mov dx, ax
	mov ah, 9
	int 21h
	mov [vi], 0
	mov si, offset vhex
	mov di, offset vtmp2
	mov word [di], si
	mov [vtmp3], 0
	mov [vj], 4
label197:
;; -- WHILE --
	mov bl, [vi]
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
	cmp bx, ax
	jl bar194
	jmp label337
bar194:
;; -- ADD --
	mov si, offset vbin
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, byte [si]
;; -- SUB --
	sub ax, 48
	mov [vtmp1], al
;; -- MUL --
	mov al, [vtmp1]
	mul byte [vj]
;; -- ADD --
	add al, [vtmp3]
	mov [vtmp3], al
;; -- IF --
	mov bl, [vj]
	mov ax, 2
	cmp bx, ax
	jl bar216
	jmp label310
bar216:
;; -- IF --
	mov bl, [vtmp3]
	mov ax, 9
	cmp bx, ax
	jg bar221
	jmp label274
bar221:
;; -- ADD --
	mov al, [vtmp3]
	add ax, 8
	mov [vtmp3], al
label274:
;; -- ADD --
	mov al, [vtmp3]
	add ax, 48
	mov [vtmp3], al
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov si, offset vtmp3
	mov si, offset vtmp3
	movsb
	mov [vj], 4
;; -- ADD --
	mov ax, [vtmp2]
	add ax, 1
	mov [vtmp2], ax
label310:
;; -- ADD --
	mov al, [vi]
	add ax, 1
	mov [vi], al
;; -- SUB --
	mov al, [vj]
	sub ax, 1
	mov [vj], al
	jmp label197
label337:
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov word ptr [di], 36
;; -- DOS -- 9 --
	mov si, offset vnl
	mov dx, si
	mov ah, 9
	int 21h
;; -- DOS -- 9 --
	mov si, offset vhex_str
	mov dx, si
	mov ah, 9
	int 21h
;; -- DOS -- 9 --
	mov si, offset vhex
	mov dx, si
	mov ah, 9
	int 21h
	mov ah, 4Ch
	int 21h
END start