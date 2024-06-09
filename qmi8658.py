# QMI8658C Accelerometer and Gyroscope

from machine import Pin, I2C

I2C_SDA = 6
I2C_SDL = 7

class QMI8658:
    def __init__(self, address=0x6B):
        self._address = address
        self._bus = I2C(id=1, scl=Pin(I2C_SDL), sda=Pin(I2C_SDA), freq=100000)
        if self.WhoAmI():
            self.Read_Revision()
        self.Config_apply()

    def _read_byte(self, cmd):
        return self._bus.readfrom_mem(self._address, cmd, 1)[0]

    def _read_block(self, reg, length=1):
        return self._bus.readfrom_mem(self._address, reg, length)

    def _write_byte(self, cmd, val):
        self._bus.writeto_mem(self._address, cmd, bytes([val]))

    def WhoAmI(self):
        return self._read_byte(0x00) == 0x05

    def Read_Revision(self):
        return self._read_byte(0x01)

    def Config_apply(self):
        self._write_byte(0x02, 0x60)
        self._write_byte(0x03, 0x23)
        self._write_byte(0x04, 0x53)
        self._write_byte(0x05, 0x00)
        self._write_byte(0x06, 0x11)
        self._write_byte(0x07, 0x00)
        self._write_byte(0x08, 0x03)

    def Read_XYZ(self):
        raw_xyz = self._read_block(0x35, 6)
        xyz = [(raw_xyz[i * 2 + 1] << 8) | raw_xyz[i * 2] for i in range(3)]
        for i in range(3):
            if xyz[i] >= 32767:
                xyz[i] -= 65535
            xyz[i] /= (1 << 12)  # QMI8658AccRange_8g
        return xyz