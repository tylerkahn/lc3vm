from BitField import BitField
from StringIO import StringIO
import sys
import unittest
import vm

class TestSequenceFunctions(unittest.TestCase):

	def setUp(self):
		vm.resetState()

	def test_add(self):
		vm.reg[2] = 23
		vm.reg[4] = 90
		vm.reg[7] = 4
		vm.mem[0] = 0b0001111010000100 # ADD R7, R2, R4
		vm.run()

		self.assertTrue(vm.reg[7] == (23+90))

	def test_add_negative(self):
		vm.reg[2] = -23 & 0xFFFF
		vm.reg[4] = 10
		vm.reg[7] = 10
		vm.mem[0] = 0b0001111010000100 # ADD R7, R2, R4
	
		vm.reg[0] = -99 & 0xFFFF
		vm.reg[3] = -2 & 0xFFFF
		vm.mem[1] = 0b0001101000000011 # ADD R5, R0, R3

		vm.run()

		self.assertTrue(vm.reg[7] == ((-23+10) & 0xFFFF))
		self.assertTrue(vm.reg[5] == ((-99-2) & 0xFFFF))
    	
	def test_add_immediate(self):
		vm.reg[0] = 44
		vm.mem[0] = 0b0001100000101111 # ADD R4, R0, #15
    	
		vm.reg[1] = -23 & 0xFFFF
		vm.mem[1] = 0b0001101001110000 # ADD R5, R1, #-16
		
		vm.run()
		
		self.assertTrue(vm.reg[4] == (44 + 15))
		self.assertTrue(vm.reg[5] == ((-23 - 16) & 0xFFFF))
	
	def test_add_setcc(self):
		vm.reg[0] = 44
		vm.reg[1] = 56
		vm.mem[0] = 0b0001101000000001 # ADD R5, R0, R1
		
		vm.run()
		
		f = BitField(vm.flags, 3)
		self.assertTrue(f[0] == 1) # Positive
		self.assertTrue(f[1] == 0) # Zero
		self.assertTrue(f[2] == 0) # Negative

	def test_and(self):
		vm.reg[0] = 0b1010111001101010
		vm.reg[1] = 0b0111010111011100
		vm.mem[0] = 0b0101011000000001 # AND R3, R0, R1
		
		vm.run()
		
		self.assertTrue(vm.reg[3] == 0b0010010001001000)
		
	def test_and_immediate(self):
		vm.reg[0] = 0b1010111001101010
		vm.mem[0] = 0b0101010000100111 # AND R2, R0, #7
		
		vm.reg[1] = 0b1010111001101010
		vm.mem[1] = 0b0101011001110010 # AND R3, R1, #-14
		
		vm.run()
		
		self.assertTrue(vm.reg[2] == 0b0000000000000010)
		self.assertTrue(vm.reg[3] == 0b1010111001100010)

	def test_and_setcc(self):
		vm.reg[1] = 0b1010111001101010
		vm.mem[1] = 0b0101011001110010 # AND R3, R1, #-14
		
		vm.run()
		f = BitField(vm.flags, 3)
		self.assertTrue(f[0] == 0) # Positive
		self.assertTrue(f[1] == 0) # Zero
		self.assertTrue(f[2] == 1) # Negative
	
	def test_br_1(self):
		vm.flags = 0b001 # Positive
		vm.mem[0] = 0b0000001000001010 # BRp 10
		vm.mem[4] = 0b1111000000100101 # HALT (TRAP 0x25)
		vm.mem[11] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		self.assertTrue(vm.pc == 12)
		
	def test_br_2(self):
		vm.flags = 0b000 # No Flags Set
		vm.mem[0] = 0b0000001000001010 # BRp 10
		vm.mem[4] = 0b1111000000100101 # HALT (TRAP 0x25)
		vm.mem[11] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		self.assertTrue(vm.pc == 5)
	
	def test_br_3(self):
		vm.flags = 0b010 # Zero
		vm.mem[0] = 0b0000011000001010 # BRpz 10
		vm.mem[4] = 0b1111000000100101 # HALT (TRAP 0x25)
		vm.mem[11] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		self.assertTrue(vm.pc == 12)
	
	def test_br_4(self):
		vm.mem[0] = 0b0001000000111011 # ADD R0, R0, #-5
		vm.mem[1] = 0b0000100000001010 # BRn 10
		vm.mem[4] = 0b1111000000100101 # HALT (TRAP 0x25)
		vm.mem[12] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()

		self.assertTrue(vm.pc == 13)
		
	def test_jmp(self):
		vm.reg[3] = 7
		vm.mem[0] =	0b1100000011000000 # JMP R3
		vm.mem[4] = 0b1111000000100101 # HALT (TRAP 0x25)
		vm.mem[7] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()

		self.assertTrue(vm.pc == 8)
	
	def test_jsr(self):
		vm.reg[7] = 0b100
		vm.mem[20] = 0b0100100000101000 # JSR #40
		vm.mem[61] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		
		self.assertTrue(vm.pc == 62)
		self.assertTrue(vm.reg[7] == 21)
		
	def test_jsrr(self):
		vm.reg[4] = 42
		vm.reg[7] = 0b100
		vm.mem[20] = 0b0100000100000000 # JSRR R4
		vm.mem[63] = 0b1111000000100101 # HALT (TRAP 0x25)
	
		vm.run()
		
		self.assertTrue(vm.pc == 64)
		self.assertTrue(vm.reg[7] == 21)
	
	def test_ld(self):
		vm.flags = 0b000
		vm.mem[4] = -400 & 0xFFFF
		
		vm.mem[0] = 0b0100100000100111 # JSR #39
		vm.mem[40] = 0b0010011111011011 # LD R3, -37 
		
		vm.run()
		
		self.assertTrue(vm.reg[3] == (-400 & 0xFFFF))
		self.assertTrue(vm.flags == 0b100) # Negative
		
	def test_ldi(self):
		vm.flags = 0b000
		vm.mem[70] = 80
		vm.mem[80] = -20 & 0xFFFF
	
		vm.mem[0] = 0b1010100001000101 # LDI R4, 69
		vm.mem[20] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		
		self.assertTrue(vm.reg[4] == (-20 & 0xFFFF))
		self.assertTrue(vm.flags == 0b100) # Negative
		
	def test_ldr(self):
		vm.flags = 0b000
		vm.mem[80] = 0
		vm.reg[5] = 65
		
		vm.mem[0] = 0b0110001101001111 # LDR R1, R5, #15
		vm.mem[2] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		
		self.assertTrue(vm.reg[1] == 0)
		self.assertTrue(vm.flags == 0b010) # Zero
	
	def test_lea(self):
		vm.flags = 0b000
		
		vm.mem[0] = 0b1110010011100110 # LEA R2, #230
		
		vm.mem[4] = 0b1110001100000001 # LEA R1, #-255
		
		vm.run()
		self.assertTrue(vm.reg[2] == 231)
		self.assertTrue(vm.reg[1] == ((5 - 255) & 0xFFFF))
		self.assertTrue(vm.flags == 0b100) # Negative
	
	def test_not(self):
		vm.flags = 0b000
		vm.reg[4] = 0b0111111111001110

		vm.mem[0] = 0b1001010100111111 # NOT R2, R4
		
		vm.run()
		
		self.assertTrue(vm.reg[2] == 0b1000000000110001)
		self.assertTrue(vm.flags == 0b100) # Negative
		
	def test_st(self):
		vm.reg[6] = -9000 & 0xFFFF
		
		vm.mem[4] = 0b0011110000011001 # ST R6, #25
		vm.mem[5] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		
		self.assertTrue(vm.mem[30] == (-9000 & 0xFFFF))
		
	def test_sti(self):
		vm.mem[5] = 40
		vm.reg[7] = 80
		
		vm.mem[0] = 0b0000111000010011 # BRnzp #19 
		vm.mem[20] = 0b1011111111110000 # STI R7, #-16
		vm.mem[21] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		
		self.assertTrue(vm.mem[40] == 80)
		
	def test_str(self):
		vm.reg[3] = -20 & 0xFFFF
		vm.reg[5] = 0
		
		vm.mem[20] = 0b0111101011011001 # STR R5, R3, #25
		
		vm.run()
		
		self.assertTrue(vm.mem[5] == 0)
		
	def test_trap_0x21_out(self):
		capture = StringIO()
		save_stdout = sys.stdout
		sys.stdout = capture
		
		vm.reg[0] = ord('J')
		
		vm.mem[0] = 0b1111000000100001 # TRAP 0x21 (OUT)
		vm.mem[1] = 0b0001000000100001 # ADD R0, R0, #1
		vm.mem[2] = 0b1111000000100001 # TRAP 0x21 (OUT)
		
		
		vm.run()
		sys.stdout = save_stdout
		
		self.assertTrue(capture.getvalue() == "JK")
	
	def test_trap_0x24_putsp(self):
		capture = StringIO()
		save_stdout = sys.stdout
		sys.stdout = capture
	
		vm.mem[10] = ord('A') + (ord('p') << 8) 
		vm.mem[11] = ord('p') + (ord('l') << 8)
		vm.mem[12] = ord('e')
		vm.mem[13] = 0x0
		
		vm.mem[14] = ord('A') + (ord('p') << 8) 
		vm.mem[15] = ord('p') + (ord('l') << 8)
		vm.mem[16] = ord('e') + (ord('s') << 8)
		vm.mem[17] = 0x0
		
		vm.mem[0] = 0b1110000000001001 # LEA R0, #9
		vm.mem[1] = 0b1111000000100100 # TRAP 0x24 (PUTSP)
		vm.mem[2] = 0b1110000000001011 # LEA R0, #11
		vm.mem[3] = 0b1111000000100100 # TRAP 0x23 (PUTSP) 
		vm.mem[4] = 0b1111000000100101 # HALT (TRAP 0x25)
		
		vm.run()
		sys.stdout = save_stdout
		self.assertTrue(capture.getvalue()[:12] == "Apple\0Apples")
		
if __name__ == '__main__':
    unittest.main()
