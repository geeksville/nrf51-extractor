import telnetlib
import re
import struct

HOST="127.0.0.1"
PORT="4444"

tn = telnetlib.Telnet(HOST, PORT)
tn.set_debuglevel(0)
tn.read_until(">")

def tncmd(cmd):
    tn.write(cmd + "\n")
    return tn.read_until(">")

tncmd("reset halt")

with open("dump.bin", "w") as outfile:
    for addr in xrange(0, int("0x40000", 16), 4):
        tncmd("reg pc 0x6d4")
        tncmd("reg r4 " + hex(addr))
        tncmd("step")
        resp = tncmd("reg r4")
        t = re.findall(r'0x[0-9a-fA-F]+', resp)
        if t:
            outfile.write(struct.pack("I", int(t[0], 16)))
        if (addr % int("0x400", 16)) == 0:
            print hex(addr)
