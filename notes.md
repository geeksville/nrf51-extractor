
yay! I think this bluetooth only initial thing will finally work. Eyebysickle sent me one more SW102 (really nice of him) so I could try a new approach. I when I tried before I could only really "test" my approach once because the factory SW102s have the read-protection bit set in their config flash - so you aren't supposed to be able to read anything from jtag and all writes must first erase the entire flash. (cc @lowPerformer) This is a bummer because it only gave me one test to install and run our bootloader & softdevice on the device and for some reason it failed - and I couldn't use a debugger to see why.

But when googling I found that apprently the NF51 has a bug in their implementation and if you are tricky it is possible to slowly leak out the contents of flash. So I just wrote a tool (almost entirely based on this great web article): https://github.com/geeksville/nrf51-extractor

It works! The image I pulled out of the new device (which I'm going to carefully leave virgin btw) I could then successfully program onto my development SW102 and it happily now boots the factory load (which I never previously had access to). I can even now turn off the read-protect bit before programming . So I should be able to try our approach and now be able to debug why it didn't work. I bet it will be fairly quick to find the problem now that I can test more than one time per device ;-)

---
Update 2:
Interesting!  About 25% of the time updating the virginmotized SW102 to our bootloader _works_.  The bootloader successfully comes up and
happily then upgrades to our appload.  75% of the time the uploaded bootloader just seems dead.  Okay, now we can debug!
---
reaching our bootloader!

(gdb) b main
Breakpoint 1 at 0x3cfc4: file ./nRF5_SDK_12.3.0/components/drivers_nrf/hal/nrf_gpio.h, line 514.
(gdb) cont
Continuing.
Note: automatically using hardware breakpoints for read-only addresses.

Breakpoint 1, main () at ./src/main.c:50
50	  nrf_gpio_cfg_input(BUTTON_M__PIN, NRF_GPIO_PIN_PULLUP);
(gdb)

But later we die in ble_stack_init() when it calls sd_softdevice_vector_table_base_set.  Unfortunately the failure is deep inside softdevice
code which I don't have source for.

but doing a raw diff of the entire flash - the programming of our softdevice into the flash seems _very_ slightly corrupted:

diff --suppress-common-lines -y <(xxd -e failed-upgrade.bin) <(xxd -e working-scratch-install.bin)  | less
00000300: 4601bd70 04922201 42906848 2009d901  p..F."..Hh.B.. | 00000300: 4601bd70 04122201 42906848 2009d901  p..F."..Hh.B..
00000800: 00000000 00031fe0 00000e40 00000000  ........@..... | 00000800: ffffffff ffffffff ffffffff ffffffff  ..............

The only diffs are here, the one on the left is the non working version (after upgrading the target using my OTA transitional)
The cols on the right are what they should be.  So I know that the sdk9 bootloader properly installed our bootloader and new softdevice (ALMOST).

I checked the hex softdevice file we built into our image:
arm-none-eabi-objdump -s `find . -name s130_nrf51_2.0.1_softdevice.hex` | less

The contents match what is on the right (as expected)

The values at 0x800 seem to be wrong because that portion of the softdevice.hex file ends right at 0x7ff, so the original rev9 bootloader
chooses not to erase the page at 0x800 (I guess).  

Possibly the failure is due to a single bit error in the 04922201 vs 04122201 (correct) at 0x304.  This is softdevice code and it seems like
the sdk9 bluetooth upgrade made a mistake.

Next step #1: is to manually fix that single bit error and confirm that the board then boots and updates the appload.  This will let me know
that this bit corruption was the cause of the problem.

Next step #2: reinstall the virgin image and re OTA upgrade to our transitional bootloader zip file (and make sure this is one of the 75% failure cases).  Then copy the flash back to my computer and see if there is another single bit error and at a different random address (likely).  
Then dive into sdk9 bootloader source
again to see if there is a way we can add an optional CRC to the files inside the zip - because it seems like something is probably flaky in their
bluetooth download.
