import struct

pkt=b'\x00\x00\x1e\x00.@\x00\xa0 \x08\x00\xa0 \x08\x00\x00\x00\x0c<\x14@\x01\xb7\x00\x00\x00\xb7\x00\xb3\x01\xd4\x00\x00\x00\x02\x9f\xc2\xa5X\xb6'
pkt=b"\x00\x00@\x00*@p\xa0 \x08\x00\xa0 \x08\x00\x00\x10\x00\x99\x16@\x01\xdc\x00\x00\x00\x00\x00Q~\x00\x00\x00\x00\x00\x00e\x00\x04\x00r\x00\x00\x00\x01\x00\x00\x001hmK\x00\x00\x00\x00\x16\x00\x11\x03\xdc\x00\xdb\x01\x88K0\x000#\x03\x96\xfaI*\xf5\xa2\xb0\xa34\xe8\xf4\x08l\x9d\xeb\x10tH\xb0-\x15\xd9p\x00\x00\xe8\xa9\x00 \x01\x00\x00\x00\xc4\xf3Y\x9a\x13\xfb\x11H\xb7\xcfK\xcb%_2\x8f\x8dz\xe8\x18\xabQ.I\x00I\xa0d4\x90\xe7\xd5C\\\xbay)\xbe&\x8e\x8d\xa8[Jv\x85\xaa\xf6\x13\x18RZEQ;\xec\x02.\xad;u}>\xfb (\xb8\x0f'\xb9\xcfG\xd9\xbb%i\x08\xec \xe7\x1aWI\xf0\xe0\xa2\xc2L\xb7'\xd1\xa9\x83S1x\x80\x96#\x01\xe4\x04}\xe4\xbd\xe5\xd4_\x8afa\xd4@\xa7\xf5\xd7\xf6\xc5\x96\n"
rt_length = struct.unpack("<h", pkt[2:4])[0]
parser = "<cxhhbxhbBbB"
parser = "<cbbbbbbbbbbbbb"
parser = "<cBBBBBBBBBBBBB"
parser = "<cxhhbxhbBbB"
parser = "<xhhhhhhx"
parser = "<cxhhbxhbBbB"
import pdb;pdb.set_trace()


struct.unpack(parser, pkt[16:rt_length])