import msvcrt

#enum constants
N = (0, -1)
S = (0, 1)
E = (1, 0)
W = (-1, 0)
NOP = (0, 0)
QUIT = "QUIT"
SELECT = "ENTER"
CANCEL = "ESCAPE"
OPTION_1 = "1"
OPTION_2 = "2"

#motion
ARROWOP = {b'H' : N,#"N",
	b'P' : S,#"S",
	b'M' : E,#"E",
	b'K' : W,#"W",
	b'Q' : S,#"S",
	b'I' : N,#"N",
	}

CARDDRS = [N, E, S, W]

ASCII_OP_DICT = {
	"1": OPTION_1,
	"2": OPTION_2,
	"Q": QUIT,
	"X": QUIT
}

def _get_ch_drop_zero():
	c = msvcrt.getch()
	while c == b'\x00':
		c = msvcrt.getch()
	return c

def get_input_op():
	x = msvcrt.kbhit()
	if x:
		try:
			inpraw = _get_ch_drop_zero()
			if inpraw == b'\xe0':
				arrow = _get_ch_drop_zero()
				op = ARROWOP[arrow]
			elif inpraw.decode() == chr(27):
				op = CANCEL
			elif inpraw.decode() == chr(13):
				op = SELECT
			else:
				i = inpraw.decode("ascii")
				if len(i) > 0 and i in "QX":
					return QUIT
				else:
					return ASCII_OP_DICT.get(i, NOP)
		except UnicodeDecodeError:
			op = NOP
		except KeyError:
			op = NOP
	else:
		op = NOP
	return op 
