.MODEL SMALL
.STACK 100h
.DATA
	vt db "asd$"
	vi db ?
.CODE
start:
	mov ax, @data
	mov ds, ax
	mov byte [vi], 123
;; -- ADD --
	mov ax, 1
	add ax, 1
;; -- ADD --
	add al, byte [vi]
	mov byte [vi], al
;; -- ADD --
	mov ax, 1
	add ax, 1
;; -- ADD --
	add al, byte [vi]
	mov byte [vi], al
	mov ah, 4Ch
	int 21h
END start