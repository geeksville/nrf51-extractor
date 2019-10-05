# Tools for reverse engineering NRF51 firmware

This is based on the great article at: https://www.pentestpartners.com/security-blog/nrf51822-code-readout-protection-bypass-a-how-to/

I'm mostly just making this for my own use but if useful for others then great.

# How to read from a protected NRF51

* (first read the article above)
* start OPENOCD with /usr/local/share/openocd/bin/openocd -f /usr/local/share/openocd/bin/../scripts/interface/stlink.cfg -f /usr/local/share/openocd/bin/../scripts/target/nrf51.cfg -c "init; reset init;"
* run "rungdb"
* inside the GDB shell run "uicrtofile" to save all the uicr registers to a bin file.  If you are cloning a device you'll want to use these later.
* run "dumpficr" to get a handy set of known memory values (when a device is protected most flash is not readable, but this is)

using the values from dumpficr do the following sequence:
* monitor reset halt (to put the PC at the start addr)
* regset 0x10000000 (or some other address with recognizable data in the FICR region) this fills all registers with that address
* si to step one instruction
* "i r" to dump all registers to see if the value you wanted was read into any register, if not try again by repeating regset/si/i r until you
see the value you are looking for (should happen within 10 instructions)
* Now you know where a load instruction is.  You'll use the PC address of that instrction later
* You also know which register that load instruction is loading into.
* set PC to that address again (so you can now find out WHICH register is being used as the source address register - probably the same)
* run "regset2 0x10000000" but this command (look at its implementation) is reading from the first 52 bytes of data into r0 through r12
* run "si" and "i r" - from the set of registers you see, you should be able to figure out WHICH register was used to contain the load address

Based on the instruction address you found, the register used to contain the address and the register used to contain the loaded value:
Edit readout.py

Run "python readout.py".  It will take about 30 minutes and will dump the entire 256KB of flash out of the device.

# How to write that image to a new device

```
telnet localhost 4444
reset halt 
nrf51 mass_erase
flash write_image dump.bin 0
flash write_image uicr.bin 0x10001000
```
