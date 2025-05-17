.MODEL SMALL
.STACK 100h
.DATA
	vhexTest db "HEX_TEST", 10,"$"
	voct_str db "OCT: $"
	vbin_str db "BIN: $"
	vhex_str db "HEX: $"
	vdec_str db "DEC: $"
	vinput db 255,256 dup (0)
	vbin db 255,256 dup (0)
	vdec db 16,17 dup (0)
	vhex db 16,17 dup (0)
	voct db 16,17 dup (0)
	vdv dw ?
	vdt dw ?
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
;; -- VARDEF vdv --
	mov di, offset vdv
	mov word ptr [di], 0
;; -- VARDEF vdt --
	mov di, offset vdt
	mov word ptr [di], 0
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
;; -- ADD --
	add ax, 1
;; -- VARDEF vi --
	mov [vi], al
;; -- VARDEF vj --
	mov di, offset vj
	mov si, offset vi
	movsb
;; -- DOS -- 9 --
	mov si, offset voct_str
	mov dx, si
	mov ah, 9
	int 21h
label0:
;; -- WHILE --
	xor bx, bx
	mov bl, [vi]
	mov ax, 0
	cmp bx, ax
	jg bar79
	jmp label1
bar79:
;; -- ADD --
	mov si, offset vinput
	mov ax, si
	add al, [vj]
;; -- ADD --
	add ax, 2
;; -- SUB --
	sub al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- DOS -- 2 --
	mov dl, al
	mov ah, 2
	int 21h
;; -- SUB --
	mov al, [vi]
	sub ax, 1
;; -- VARDEF vi --
	mov [vi], al
	jmp label0
label1:
;; -- DOS -- 2 --
	mov dx, 10
	mov ah, 2
	int 21h
;; -- ADD --
	mov si, offset vinput
	mov ax, si
	add ax, 1
;; -- MEMREAD --
	mov si, ax
	mov ax, [si]
;; -- VARDEF vi --
	mov [vi], al
;; -- VARDEF vj --
	mov [vj], 0
;; -- VARDEF vtmp1 --
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
;; -- VARDEF vtmp2 --
	mov [vtmp2], ax
;; -- VARDEF vtmp3 --
	mov [vtmp3], 0
label2:
;; -- WHILE --
	xor bx, bx
	mov bl, [vi]
	mov ax, 0
	cmp bx, ax
	jg bar137
	jmp label3
bar137:
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
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
;; -- VARDEF vj --
	mov [vj], 3
label4:
;; -- WHILE --
	xor bx, bx
	mov bl, [vj]
	mov ax, 0
	cmp bx, ax
	jg bar158
	jmp label5
bar158:
;; -- SUB --
	mov ax, [vtmp2]
	sub ax, 1
;; -- VARDEF vtmp2 --
	mov [vtmp2], ax
;; -- MOD --
	mov al, [vtmp1]
	mov dl, 2
	div dl
	mov al, ah
	xor ah, ah
;; -- ADD --
	add ax, 48
;; -- VARDEF vtmp3 --
	mov [vtmp3], al
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov si, offset vtmp3
	movsb
;; -- DIV --
	mov al, [vtmp1]
	mov dl, 2
	div dl
	xor ah, ah
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
;; -- SUB --
	mov al, [vj]
	sub ax, 1
;; -- VARDEF vj --
	mov [vj], al
	jmp label4
label5:
;; -- SUB --
	mov al, [vi]
	sub ax, 1
;; -- VARDEF vi --
	mov [vi], al
	jmp label2
label3:
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
;; -- VARDEF vtmp2 --
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
;; -- SUB --
	sub ax, 1
;; -- VARDEF vi --
	mov [vi], al
;; -- VARDEF vtmp2 --
	mov si, offset vhex
	mov di, offset vtmp2
	mov [di], si
;; -- VARDEF vtmp3 --
	mov [vtmp3], 0
;; -- VARDEF vj --
	mov [vj], 0
label6:
;; -- WHILE --
	xor bx, bx
	mov bl, [vi]
	mov ax, 0
	cmp bx, ax
	jg bar254
	jmp label7
bar254:
;; -- ADD --
	mov al, [vi]
	add ax, 1
;; -- ADD --
	mov si, offset vbin
	add ax, si
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- SUB --
	sub ax, 48
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
;; -- IF --
	xor bx, bx
	mov bl, [vtmp1]
	mov ax, 1
	cmp bx, ax
	je bar270
	jmp label8
bar270:
;; -- SHL --
	mov ax, 1
	mov cl, [vj]
	shl al, cl
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
label8:
;; -- ADD --
	mov al, [vtmp3]
	add al, [vtmp1]
;; -- VARDEF vtmp3 --
	mov [vtmp3], al
;; -- IF --
	xor bx, bx
	mov bl, [vj]
	mov ax, 3
	cmp bx, ax
	je bar288
	jmp label9
bar288:
;; -- IF --
	xor bx, bx
	mov bl, [vtmp3]
	mov ax, 9
	cmp bx, ax
	jg bar293
	jmp label11
bar293:
;; -- ADD --
	mov al, [vtmp3]
	add ax, 7
;; -- VARDEF vtmp3 --
	mov [vtmp3], al
label11:
;; -- ADD --
	mov al, [vtmp3]
	add ax, 48
;; -- VARDEF vtmp3 --
	mov [vtmp3], al
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov si, offset vtmp3
	movsb
;; -- VARDEF vtmp3 --
	mov [vtmp3], 0
;; -- VARDEF vj --
	mov [vj], 0
;; -- ADD --
	mov ax, [vtmp2]
	add ax, 1
;; -- VARDEF vtmp2 --
	mov [vtmp2], ax
	jmp label10
label9:
;; -- ADD --
	mov al, [vj]
	add ax, 1
;; -- VARDEF vj --
	mov [vj], al
label10:
;; -- SUB --
	mov al, [vi]
	sub ax, 1
;; -- VARDEF vi --
	mov [vi], al
	jmp label6
label7:
;; -- IF --
	xor bx, bx
	mov bl, [vj]
	mov ax, 0
	cmp bx, ax
	jg bar346
	jmp label12
bar346:
;; -- IF --
	xor bx, bx
	mov bl, [vtmp3]
	mov ax, 9
	cmp bx, ax
	jg bar351
	jmp label13
bar351:
;; -- ADD --
	mov al, [vtmp3]
	add ax, 7
;; -- VARDEF vtmp3 --
	mov [vtmp3], al
label13:
;; -- ADD --
	mov al, [vtmp3]
	add ax, 48
;; -- VARDEF vtmp3 --
	mov [vtmp3], al
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov si, offset vtmp3
	movsb
;; -- VARDEF vtmp3 --
	mov [vtmp3], 0
;; -- ADD --
	mov ax, [vtmp2]
	add ax, 1
;; -- VARDEF vtmp2 --
	mov [vtmp2], ax
label12:
;; -- DOS -- 2 --
	mov dx, 10
	mov ah, 2
	int 21h
;; -- DOS -- 9 --
	mov si, offset vhex_str
	mov dx, si
	mov ah, 9
	int 21h
;; -- VARDEF vi --
	mov [vi], 0
;; -- ADD --
	mov si, offset vhex
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
label14:
;; -- WHILE --
	xor bx, bx
	mov bl, [vtmp1]
	mov ax, 0
	cmp bx, ax
	jg bar404
	jmp label15
bar404:
;; -- ADD --
	mov al, [vi]
	add ax, 1
;; -- VARDEF vi --
	mov [vi], al
;; -- ADD --
	mov si, offset vhex
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
	jmp label14
label15:
label16:
;; -- WHILE --
	xor bx, bx
	mov bl, [vi]
	mov ax, 0
	cmp bx, ax
	jg bar425
	jmp label17
bar425:
;; -- SUB --
	mov al, [vi]
	sub ax, 1
;; -- VARDEF vi --
	mov [vi], al
;; -- ADD --
	mov si, offset vhex
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
;; -- DOS -- 2 --
	mov dl, [vtmp1]
	mov ah, 2
	int 21h
	jmp label16
label17:
;; -- VARDEF vi --
	mov [vi], 0
;; -- VARDEF vtmp2 --
	mov si, offset vdec
	mov di, offset vtmp2
	mov [di], si
;; -- VARDEF vtmp3 --
	mov [vtmp3], 0
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
;; -- VARDEF vj --
	mov [vj], al
;; -- DOS -- 2 --
	mov dx, 10
	mov ah, 2
	int 21h
;; -- DOS -- 9 --
	mov si, offset vdec_str
	mov dx, si
	mov ah, 9
	int 21h
;; -- ADD --
	mov si, offset vbin
	mov ax, si
	add ax, 1
;; -- MEMREAD --
	mov si, ax
	mov ax, [si]
;; -- SUB --
	sub ax, 48
;; -- VARDEF vj --
	mov [vj], al
;; -- IF --
	xor bx, bx
	mov bl, [vj]
	mov ax, 1
	cmp bx, ax
	je bar487
	jmp label18
bar487:
;; -- DOS -- 2 --
	mov dx, 45
	mov ah, 2
	int 21h
;; -- VARDEF vi --
	mov [vi], 1
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
;; -- SUB --
	sub ax, 1
;; -- VARDEF vj --
	mov [vj], al
label20:
;; -- WHILE --
	xor bx, bx
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
;; -- ADD --
	add ax, 1
	cmp bx, ax
	jl bar519
	jmp label21
bar519:
;; -- ADD --
	mov si, offset vbin
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- SUB --
	sub ax, 48
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
;; -- IF --
	xor bx, bx
	mov bl, [vtmp1]
	mov ax, 0
	cmp bx, ax
	je bar533
	jmp label22
bar533:
;; -- SHL --
	mov ax, 1
	mov cl, [vj]
	shl al, cl
;; -- ADD --
	add ax, [vdv]
;; -- VARDEF vdv --
	mov [vdv], ax
label22:
;; -- ADD --
	mov al, [vi]
	add ax, 1
;; -- VARDEF vi --
	mov [vi], al
;; -- SUB --
	mov al, [vj]
	sub ax, 1
;; -- VARDEF vj --
	mov [vj], al
;; -- IF --
	xor bx, bx
	mov bl, [vi]
	mov ax, 15
	cmp bx, ax
	jg bar559
	jmp label23
bar559:
;; -- VARDEF vj --
	mov di, offset vj
	mov si, offset vi
	movsb
;; -- VARDEF vi --
	mov [vi], 255
label23:
	jmp label20
label21:
;; -- ADD --
	mov ax, [vdv]
	add ax, 1
;; -- VARDEF vdv --
	mov [vdv], ax
;; -- VARDEF vtmp1 --
	mov [vtmp1], 0
label24:
;; -- WHILE --
	xor bx, bx
	mov bx, [vdv]
	mov ax, 0
	cmp bx, ax
	jg bar586
	jmp label25
bar586:
;; -- MOD --
	mov ax, [vdv]
	mov dl, 10
	div dl
	mov al, ah
	xor ah, ah
;; -- VARDEF vi --
	mov [vi], al
;; -- ADD --
	mov al, [vi]
	add ax, 48
;; -- VARDEF vj --
	mov [vj], al
;; -- DIV --
	mov ax, [vdv]
	mov dl, 10
	div dl
	xor ah, ah
;; -- VARDEF vdv --
	mov [vdv], ax
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov si, offset vj
	movsb
;; -- ADD --
	mov ax, [vtmp2]
	add ax, 1
;; -- VARDEF vtmp2 --
	mov [vtmp2], ax
;; -- ADD --
	mov al, [vtmp1]
	add ax, 1
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
	jmp label24
label25:
	jmp label19
label18:
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
;; -- VARDEF vj --
	mov [vj], al
label26:
;; -- WHILE --
	xor bx, bx
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
;; -- ADD --
	add ax, 1
	cmp bx, ax
	jl bar646
	jmp label27
bar646:
;; -- ADD --
	mov si, offset vbin
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- SUB --
	sub ax, 48
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
;; -- IF --
	xor bx, bx
	mov bl, [vtmp1]
	mov ax, 1
	cmp bx, ax
	je bar660
	jmp label28
bar660:
;; -- SHL --
	mov ax, 1
	mov cl, [vj]
	shl al, cl
;; -- ADD --
	add ax, [vdv]
;; -- VARDEF vdv --
	mov [vdv], ax
label28:
;; -- ADD --
	mov al, [vi]
	add ax, 1
;; -- VARDEF vi --
	mov [vi], al
;; -- SUB --
	mov al, [vj]
	sub ax, 1
;; -- VARDEF vj --
	mov [vj], al
;; -- IF --
	xor bx, bx
	mov bl, [vi]
	mov ax, 15
	cmp bx, ax
	jg bar686
	jmp label29
bar686:
;; -- VARDEF vj --
	mov di, offset vj
	mov si, offset vi
	movsb
;; -- VARDEF vi --
	mov [vi], 255
label29:
	jmp label26
label27:
;; -- VARDEF vtmp1 --
	mov [vtmp1], 0
label30:
;; -- WHILE --
	xor bx, bx
	mov bx, [vdv]
	mov ax, 0
	cmp bx, ax
	jg bar707
	jmp label31
bar707:
;; -- MOD --
	mov ax, [vdv]
	mov dl, 10
	div dl
	mov al, ah
	xor ah, ah
;; -- VARDEF vi --
	mov [vi], al
;; -- ADD --
	mov al, [vi]
	add ax, 48
;; -- VARDEF vj --
	mov [vj], al
;; -- DIV --
	mov ax, [vdv]
	mov dl, 10
	div dl
	xor ah, ah
;; -- VARDEF vdv --
	mov [vdv], ax
;; -- MEMWRITE --
	mov di, [vtmp2]
	mov si, offset vj
	movsb
;; -- ADD --
	mov ax, [vtmp2]
	add ax, 1
;; -- VARDEF vtmp2 --
	mov [vtmp2], ax
;; -- ADD --
	mov al, [vtmp1]
	add ax, 1
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
	jmp label30
label31:
label19:
;; -- VARDEF vi --
	mov [vi], 0
;; -- ADD --
	mov si, offset vdec
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
label32:
;; -- WHILE --
	xor bx, bx
	mov bl, [vtmp1]
	mov ax, 0
	cmp bx, ax
	jg bar761
	jmp label33
bar761:
;; -- ADD --
	mov al, [vi]
	add ax, 1
;; -- VARDEF vi --
	mov [vi], al
;; -- ADD --
	mov si, offset vdec
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
	jmp label32
label33:
label34:
;; -- WHILE --
	xor bx, bx
	mov bl, [vi]
	mov ax, 0
	cmp bx, ax
	jg bar782
	jmp label35
bar782:
;; -- SUB --
	mov al, [vi]
	sub ax, 1
;; -- VARDEF vi --
	mov [vi], al
;; -- ADD --
	mov si, offset vdec
	mov ax, si
	add al, [vi]
;; -- MEMREAD --
	mov si, ax
	mov al, [si]
;; -- VARDEF vtmp1 --
	mov [vtmp1], al
;; -- DOS -- 2 --
	mov dl, [vtmp1]
	mov ah, 2
	int 21h
	jmp label34
label35:
	mov ah, 4Ch
	int 21h
END start