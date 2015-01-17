import serial
import time
from collections import deque

class Conn(object):
  def __init__(self):
    self.device = self.open(location='/dev/ttyUSB0')
    self.reset()
  def open(self, location):
    s = serial.Serial(port=location, baudrate=115200, timeout=0.0004)
    return s
  def close(self):
    self.device.flush()
    self.device.close()
  def read(self):
    while True:
      b = self.device.read()
      if b:
        yield b
  def write(self, b):
    success = self.device.write(b)
    if not success:
      raise Exception("Failed to write to device")
    #time.sleep(.1)
  def reset(self):
    self.write('v')
    time.sleep(.1)
  def start_stream(self):
    self.write('b')
    stream = self.read()
    return stream
  def stop_stream(self):
    self.write('s')

class Decoder(object):
  '''
  Header = 0xA0, Seq
  Body = 30 bytes
  Footer = 0xC0
  '''
  def __init__(self, stream):
    self.stream = stream
    self.byte_buffer = deque([], 256)
    self.packet_buffer = deque([], 256)
  def packet(self):
    packet = []
    header_read = False
    while len(packet) < 33:
      b = self.stream.next()
      self.byte_buffer.append(b)
      if b == '\xa0':
        packet.append(b)
        header_read = True
        continue
      if header_read:
        packet.append(b)
        header_read = False
        continue
      packet.append(b)
      if len(packet) == 32 and b == '\xc0':
        packet.append(b)
    self.packet_buffer.append(b)
    return packet

def main():
  stream = c.start_stream()
  i = 0
  tk = deque([0,0], 2)
  while True:
    i += 1
    d = Decoder(stream)
    p = d.packet()
    if i % (250) == 0:
      tk.append(time.time())
      tbtwn = tk[1] - tk[0]
      print tbtwn, i, ','.join([str(ord(b)) for b in p])

if __name__ == '__main__':
  try:
    c = Conn()
    main()
  except Exception, e:
    print e
  finally:
    c.stop_stream()
