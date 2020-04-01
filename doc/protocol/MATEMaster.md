# MATE Master Duties

The MATE itself periodically sends commands by itself to other devices in the system.

In particular it has the following duties:

- Time synchronization
- FBX (Battery Recharging)
- AGS (Automatic Generator System)
- FN-DC Net AH charge stop feature


If you are replacing the MATE with pyMATE, I recommend you implement the below features, or connect pyMATE as a 2nd mate.

## Time Synchronization ##

The command [`4004`] is sent every 30 sec to MX/DC devices (not FX), encoded in a particular format:

```
Bits 15..11 : Hour (24h)
Bits 10..5  : Minute
Bits 4..0   : Second (*2)
```

9:09:49 PM would encode as `(21<<11) | (09<<5) | (49>>1) ==  0xA938`.

Presumably this is used to synchronize the MX/DC's internal clock to the MATE, so they know when to do things like resetting counters at midnight. Without this they still seem to be able to function properly, but I imagine they would get out of sync over time.


