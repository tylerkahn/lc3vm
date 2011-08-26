#!/usr/bin/python

from BitField import BitField
from array import array
import time
import sys
import getopt
from getch import getch



MEMSIZE = 0xFFFF
reg = array('H', [0]*8)
mem = array('H', [0b1101]*MEMSIZE)
pc = 0
running = True
flags = 0b111 # Flags all on as per definition that BRnzp is treated as uncondtional jump

Squelch = False


def resetState():
	global reg
	global mem
	global pc
	global running
	global flags

	reg = array('H', [0]*8)
	mem = array('H', [0b1101]*MEMSIZE)
	pc = 0
	running = True
	flags = 0b111
	
	


def main():
	global pc
	global Squelch
	
		

	try:
		opts, args = getopt.getopt(sys.argv[1:], "hs", ["help", "squelch"])
		if len(args) == 0:
			print "Please specify an input file."
			usage()
			sys.exit(-1)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(-1)	
	
	for o, a in opts:
		if o in ("-s", "--squelch"):
			Squelch = True
		elif o in ("-h", "--help"):
			usage()
			sys.exit(-1)
		
	with open(args[0], 'rb') as f:
		k = f.read()
		loadProgram(k)
	
	run()

def run():
	global pc

	op = {		0b0000 : br,
			0b0001 : add,
			0b0010 : ld,
			0b0100 : jsr,
			0b0101 : and_,
			0b0110 : ldr,
			0b1010 : ldi,
			0b1100 : jmp,
			0b1110 : lea,
			0b1001 : not_,
			0b0011 : st,
			0b1011 : sti,
			0b0111 : str_,
			0b1111 : trap,
			0b1101 : nop }

	while running:
		if pc >= MEMSIZE:
			break
		ir = BitField(mem[pc], 16)
		pc += 1
		opcode = ir[12:15]
		op[opcode](ir)
		
def usage():
	print "Usage: {0} <input_file.obj>".format(sys.argv[0].split('/')[-1])
	print "-h, --help: print this message"
	print "-s, --squelch: only print user output"
	
def loadProgram(binString):
	def makeShort(hi, lo):
		return (hi << 8) + lo

	def shortStream(k):
		for i in xrange(0, len(k), 2):
			yield makeShort(k[i], k[i+1])
	
	bytes = map(ord, binString)

	origAddress = apply(makeShort, bytes[0:2]) # first two bytes in .obj file contain 
						   # starting address of program
	
	for i, ir in enumerate(shortStream(bytes[2:])):
		mem[origAddress + i] = ir & 0xFFFF
	

def setcc(v):
	global flags
	
	f = BitField(flags, 3)
	v = BitField(v, 16, True)
	f[0] = 1 if int(v) > 0 else 0
	f[1] = 1 if int(v) == 0 else 0
	f[2] = 1 if int(v) < 0 else 0
	flags = int(f)
		
def sext(v, sigbit):
	v = BitField(v, 16, True)
	if v[sigbit]:
		v[sigbit:15] = 1
	
	return int(v)
	
def nop(ir):
	pass

def trap(ir):
	global running
	
	def getc():
		k = getch()
		if ord(k) in [3, 4]: # Ctrl+C or Ctrl+D
			print "\n"
			sys.exit(-1)
		if ord(k) is 13:
			k = '\n'
		reg[0] = ord(k)
	def in_():
		if not Squelch:
			sys.stdout.write("Enter character: ")
		reg[0] = ord(sys.stdin.read(1))
	def out():
		sys.stdout.write(chr(reg[0] & 0x7F))
	def puts():
		k = reg[0]
		while k < MEMSIZE:
			c = mem[k]
			if c == 0:
				break
			else:
				sys.stdout.write(chr(c & 0x7F))			
			k += 1			
		if k == MEMSIZE:
			if not Squelch:
				print "ERROR: Unterminated string at ", hex(reg[0])
			
	def putsp():
		k = reg[0]
		while k < MEMSIZE:
			b = BitField(mem[k])
			lo,hi = b[0:7],b[8:15]
			
			if hi == 0 and lo == 0:
				break
			else:
				sys.stdout.write(chr(lo) + chr(hi))
			
			k += 1
		if k == MEMSIZE:
			if not Squelch:
				print "ERROR: Unterminated string at ", hex(reg[0])
	def halt():
		global running
		if not Squelch:
			print "Execution halting."
		running = False
	
	trapvect8 = ir[0:7]
	
	trap = { 0x20 : getc,
			 0x21 : out,
			 0x22 : puts,
			 0x23 : in_,
			 0x24 : putsp,
			 0x25 : halt }
	
	trap[trapvect8]()
		

def st(ir):
	sr = ir[9:11]
	pcOffset9 = ir[0:8]
	
	mem[pc + sext(pcOffset9, 8)] = reg[sr]	
	

def str_(ir):
	sr = ir[9:11]
	baseR = ir[6:8]
	offset6 = ir[0:5]
	
	address = reg[baseR] + sext(offset6, 5)

	mem[address & 0xFFFF] = reg[sr]

def sti(ir):
		sr = ir[9:11]
		pcOffset9 = ir[0:8]
		
		mem[mem[pc + sext(pcOffset9, 8)]] = reg[sr]

def not_(ir):
	dr = ir[9:11]
	sr = ir[6:8]
	
	reg[dr] = ~reg[sr] & 0xFFFF
	setcc(reg[dr])

def lea(ir):
	dr = ir[9:11]
	pcOffset9 = ir[0:8]
	
	reg[dr] = (pc + sext(pcOffset9, 8)) & 0xFFFF
	setcc(reg[dr])	

def ldr(ir):
	dr = ir[9:11]
	baseR = ir[6:8]
	offset6 = ir[0:5]
	
	address = reg[baseR] + sext(offset6, 5)
	reg[dr] = mem[address & 0xFFFF]
	setcc(reg[dr])

def ldi(ir):
	dr = ir[9:11]
	pcOffset9 = ir[0:8]
	reg[dr] = mem[mem[pc + sext(pcOffset9, 8)]]
	
	setcc(reg[dr])	

def ld(ir):
	dr = ir[9:11]
	pcOffset9 = ir[0:8]
	
	reg[dr] = mem[pc + sext(pcOffset9, 8)]
	setcc(reg[dr])

def jsr(ir):
	global pc
	
	reg[7] = pc
	if ir[11]: # jsr
		pc = pc + sext(ir[0:10], 10)
	else: # jsrr
		pc = reg[ir[6:8]]

def jmp(ir):
	global pc
	
	pc = reg[ir[6:8]]

def br(ir):
	global pc
	
	jmpFlags = ir[9:11]
	if jmpFlags & flags:
		pc = pc + sext(ir[0:8], 8)
	
def add(ir):
	__addand(lambda a,b: a + b, ir)
def and_(ir):
	__addand(lambda a,b: a & b, ir)

def __addand(f, ir):
	dr = ir[9:11]
	sr1 = ir[6:8]
	
	if ir[5]: # immediate mode
		# reg[dr] = apply(f, [reg[sr1], sext(ir[0:4], 4)]) & 0xFFFF
		reg[dr] = f(reg[sr1], sext(ir[0:4], 4)) & 0xFFFF
	else:
		sr2 = ir[0:2]
		# reg[dr] = apply(f, [reg[sr1], reg[sr2]]) & 0xFFFF
		reg[dr] = f(reg[sr1], reg[sr2]) & 0xFFFF
    
	setcc(reg[dr])

if __name__ == '__main__':
	resetState()
	main()
