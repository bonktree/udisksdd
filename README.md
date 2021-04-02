# udisksdd

This utility is intended to be called with CLI arguments suitable for `dd(1)`.
Its only job is to request a file descriptor to a block device which is unavailable to be opened for reading or writing directly and to pass it to `dd(1)`.
If the udisks API access is allowed by polkit policy, no privilege elevation is required.

### Details of Operation

If `udd(1)` is invoked with a block device node located in /dev as an input or output, it will try to ask udisks2 to open that device on its behalf.
udisks, in turn, will check if `udd(1)` is authorized to perform the polkit action `org.freedesktop.udisks2.open-device` (or `*.open-device-system`, see [udisks documentation](http://storaged.org/doc/udisks2-api/latest/udisks-polkit-actions.html)) on that device.
`udd(1)` understands enough `dd(1)` syntax to pass the relevant open(2)-style flags to `udisks`' `Block.OpenDevice` method.
If the descriptors is obtained successfully, `udd(1)` then forks off `dd(1)` and passes the descriptors as standard I/O.

If udd is invoked as uid 0, it executes `dd(1)` immediately.

### Installation

This utility only depends on Python 3, its standard library and `dbus`.

It can be packaged and installed with setuptools. Here's an example shell command sequence:
```sh
python3 -m build
pip3 install ./dist/udisksdd-*.whl
```
If you're on Linux, your distribution may or may not provide a package.

### TODO / Shortcomings

* If we have the Unix DAC permissions to open the device directly, we should do that.
* If both `if=` and `of=` are both block devices to be opened by `udisks(8)`, and polkit dictates interactive authorization, there will be 2 separate authentication prompts.
* We should hide Python tracebacks if the environment variable UDD_DEBUG is not set.
