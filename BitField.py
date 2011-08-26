class BitField(object):
    def __init__(self, value=0, nbits=32, signed=False):
        self._n = nbits
        self._d = value & (2**nbits - 1)
        self.signed = signed
    
    def invert(self):
        self._d = (~self._d) & (2**self._n - 1)

    def __len__(self):
        return self._n

    def __setitem__(self, s, value):
 
		if isinstance(s, int):
		    if s >= self._n:
		        raise IndexError("only " + str(self._n) + " bits available")
		    
		    s = (self._n + s) if s < 0 else s

		    value    = (value&1L)<<s
		    mask     = (1L)<<s
		    self._d  = (self._d & ~mask) | value
		else:
			start = s.start
			end = s.stop or (self._n - 1)
			start = (self._n + start) if start < 0 else start
			end   = (self._n + end) if end < 0 else end

			if start >= self._n or end >= self._n:
				raise IndexError("only " + str(self._n) + " bits available")
            
			for i in range(start, end+1):
				self[i] = value
				 
            
    
    def  __getitem__(self, s):
        if isinstance(s, slice):
            start = s.start
            end = s.stop or (self._n - 1)
            start = (self._n + start) if start < 0 else start
            end   = (self._n + end) if end < 0 else end

            if start >= self._n or end >= self._n:
                raise IndexError("only " + str(self._n) + " bits available")
            
            mask = 2L**(end - start + 1) -1
            return (self._d >> start) & mask
        else:
            if s >= self._n:
                raise IndexError("only " + str(self._n) + " bits available")
            s = (self._n + s) if s < 0 else s
            return (self._d >> s) & 1

    def __int__(self):
        if self.signed:
            if self[-1] == 1:
                return -(~self._d & (2**self._n - 1)) - 1
            else:
                return self._d & (2**(self._n -1) -1)
        else:
            return self._d
    
    def __repr__(self):
        s = bin(self._d)[2:]
        s = "0" * (self._n - len(s)) + s
        return "0b" + s
        
