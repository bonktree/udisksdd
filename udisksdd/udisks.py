import logging
import os # for open flags
import dbus

from . import util

class UDisks:
    _udisks_prefix = 'org.freedesktop.UDisks2'
    _udisks_service = _udisks_prefix
    _object_prefix = '/org/freedesktop/UDisks2'
    _bus = None

    def __init__(self):
        self._bus = dbus.SystemBus()

    def _get_bus_object(self, *args, **kwargs):
        return self._bus.get_object(self._udisks_service, *args, **kwargs)

    def resolve_device_by_filenode(self, devpath):
        obj = '/'.join((self._object_prefix, 'Manager'))
        intf = '.'.join((self._udisks_prefix, 'Manager'))
        Manager = dbus.Interface(self._get_bus_object(obj), intf)
        ans = Manager.ResolveDevice({'path': devpath}, {})
        logging.debug('Manager.ResolveDevice: %s', ans)
        return ans

    @classmethod
    def _object_path_from_fn_fast(cls, dname):
        """Saves a call to org.fd.UDisks2.Manager.ResolveDevice if /dev/{dname}
           is a valid device name.

           Note: This function relies on the particular approach used by
           UDisks2 to generate DBus object paths for block devices.
        """
        return '/'.join((cls._object_prefix, 'block_devices', dname))

    def object_path_from_fn(self, fn):
        fna = fn.lstrip('/dev/')
        if fna.find('/') < 0 and util.is_blockdev(fn):
            fastpath = self._object_path_from_fn_fast(fna)
            logging.debug("Assuming {}; skipping Manager.ResolveDevice call"
                    .format(fastpath))
            return fastpath
        else:
            dl = self.resolve_device_by_filenode(fn)
            return dl[0] if dl else dl

    def open_device(self, devicefn, flag):
        # OpenForBackup: O_EXCL
        # OpenForRestore: O_EXCL, O_SYNC
        blockdev_path = self.object_path_from_fn(devicefn)
        blockdev_object = self._get_bus_object(blockdev_path)
        intf = '.'.join((self._udisks_prefix, 'Block'))
        Block = dbus.Interface(blockdev_object, intf)

        modeflag = flag & (os.O_RDWR | os.O_RDONLY | os.O_WRONLY)
        if modeflag == os.O_RDWR:
            mode = 'rw'
        elif modeflag == os.O_RDONLY:
            mode = 'r'
        elif modeflag == os.O_WRONLY:
            mode = 'w'
        else:
            # We default to O_RDWR.
            mode = 'rw'
        openflags = flag & ~(os.O_RDWR | os.O_RDONLY | os.O_WRONLY)

        logging.debug("Opening {} with flags: {!r} / {}"
                      .format(blockdev_path, mode, util.repr_flag(flag)))
        return Block.OpenDevice(mode, {'flags': openflags})
