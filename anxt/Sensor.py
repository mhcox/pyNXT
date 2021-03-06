# anxt/Sensor.py
#  pyNXT - Python wrappers for aNXT
#  Copyright (C) 2011  Janosch Gräf <janosch.graef@gmx.net>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from ctypes import CDLL, c_int, c_float, c_void_p, c_char_p, Structure, byref
from .NXT import NXT
from .I2C import I2C, DEFAULT_I2C_ADDR
from .Libanxt import Libanxt
from math import ceil

DEFAULT_DIGITAL_PORT = 4

class Sensor:
    types = {"NONE":           0x00,
             None:             0x00,
             "SWITCH":         0x01,
             "TEMPERATURE":    0x02,
             "REFLECTION":     0x03,
             "ANGLE":          0x04,
             "LIGHT_ACTIVE":   0x05,
             "LIGHT_INACTIVE": 0x06,
             "SOUND_DB":       0x07,
             "SOUND_DBA":      0x08,
             "CUSTOM":         0x09,
             "LOWSPEED":       0x0A,
             "LOWSPEED_9V":    0x0B}
    modes = {"RAW":              0x00,
             None:               0x00,
             "BOOLEAN":          0x20,
             "TRANSITION_COUNT": 0x40,
             "PERIOD_COUNT":     0x60,
             "PERCENT":          0x80,
             "CELSIUS":          0xA0,
             "FAHRENHEIT":       0xC0,
             "ANGLE_STEP":       0xE0,
             "SLOPE_MASK":       0x1F,
             "MODE_MASK":        0xE0}
    valid_ports = (1, 2, 3, 4)

    def __init__(self, nxt, port = None):
        if (not port in self.valid_ports):
            port = self.valid_ports[0]

        self.nxt = nxt
        self.port = port
        self.type = None
        self.mode = None

    def __del__(self):
        self.set_sensor_typemode(None, None)

    def set_sensor_type(self, type):
        if (self.nxt!=None and self.nxt.handle!=None and type in self.types):
            return self.set_sensor_typemode(type, self.mode)
        else:
            return False

    def set_sensor_mode(self, mode):
        if (self.nxt!=None and self.nxt.handle!=None and mode in self.modes):
            return self.set_sensor_typemode(self.type, mode)
        else:
            return False

    def set_sensor_typemode(self, type, mode):
        if (self.nxt!=None and self.nxt.handle!=None):
            if (int(self.nxt.libanxt.nxt_set_sensor_mode(self.nxt.handle, self.port-1, self.types[type], self.modes[mode]))==0):
                self.type = type
                self.mode = mode
        else:
            return False

    def get_values(self, update_type = True, update_mode = True):
        if (self.nxt!=None and self.nxt.handle!=None):
            values = Libanxt.AnalogSensorValues()
            v = int(self.nxt.libanxt.nxt_get_sensor_values(self.nxt.handle, self.port-1, byref(values)))
            if (v==0):
                if (update_type):
                    self.type = [k for k, v in self.types.items() if v == values.type][0]
                if (update_mode):
                    self.mode = [k for k, v in self.modes.items() if v == values.mode][0]
                return values
            else:
                return False
        else:
            return False


class AnalogSensor(Sensor):
    default_ports = {None:             1,
                     "LIGHT_ACTIVE":   3,
                     "LIGHT_INACTIVE": 3,
                     "SOUND_DB":       2,
                     "SOUND_DBA":      2}

    def __init__(self, nxt, port = None, type = None, mode = None):
        if (port==None):
            port = default_ports[mode]

        Sensor.__init__(self, nxt, port)
        self.set_sensor_typemode(type, mode)

    def __del__(self):
        Sensor.__del__(self)

    def read(self):
        values = self.get_values()
        if (values!=False):
            v = values.calibrated if values.is_calibrated else values.scaled
            if (self.mode=="BOOLEAN"):
                return (v==1)
            elif (self.mode=="PERCENT"):
                return v/100
            else:
                return v
        else:
            return False

class TouchSensor(AnalogSensor):
    def __init__(self, nxt, port = 1):
        AnalogSensor.__init__(self, nxt, port, "SWITCH", "BOOLEAN")

    def __del__(self):
        AnalogSensor.__del__(self)
    
class LightSensor(AnalogSensor):
    def __init__(self, nxt, port = 3, light = False):
        type = "LIGHT_"+("IN" if not light else "")+"ACTIVE"
        AnalogSensor.__init__(self, nxt, port, type, "PERCENT")

    def __del__(self):
        AnalogSensor.__del__(self)

    def set_light(self, on_off):
        type = "LIGHT_"+("IN" if not on_off else "")+"ACTIVE"
        self.set_sensor_type(type)
        
    def light_on(self):
        self.set_light(True)
        
    def light_off(self):
        self.set_light(False)

class SoundSensor(AnalogSensor):
    def __init__(self, nxt, port = 2, dba = False):
        type = "SOUND_DB"+("A" if dba else "")
        AnalogSensor.__init__(self, nxt, port, type, "PERCENT")

    def __del__(self):
        AnalogSensor.__del__(self)

    def set_dba(self, dba = True):
        type = "SOUND_DB"+("A" if dba else "")
        self.set_sensor_type(type)


class DigitalSensor(Sensor, I2C):
    def __init__(self, nxt, port = DEFAULT_DIGITAL_PORT, i2c_addr = DEFAULT_I2C_ADDR):
        Sensor.__init__(self, nxt, port)
        I2C.__init__(self, nxt, port, i2c_addr)

        self.set_sensor_typemode("LOWSPEED_9V", None)

    def __del__(self):
        Sensor.__del__(self)

    def set_addr_param(self, sensor_name):
        c_addr = c_int.in_dll(self.nxt.libanxt, "nxt_"+sensor_name+"_i2c_addr")
        c_addr = c_int(self.addr)
