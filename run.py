import serial
import time
from collections import deque
import struct
import decs

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
  def reset(self):
    self.device.flush()
    self.write('v')
    time.sleep(.1)
  def start_stream(self):
    self.write('b')
    stream = self.read()
    return stream
  def stop_stream(self):
    self.write('s')

class Packet(object):
  HEADER = '\xa0'
  FOOTER = '\xc0'
  SEQ    = ord('\x00') #Any number between 0 and 255
  LEN    = 33
  CHAN1  = ['\x00', '\x00', '\x00']
  CHAN2  = ['\x00', '\x00', '\x00']
  CHAN3  = ['\x00', '\x00', '\x00']
  CHAN4  = ['\x00', '\x00', '\x00']
  CHAN5  = ['\x00', '\x00', '\x00']
  CHAN6  = ['\x00', '\x00', '\x00']
  CHAN7  = ['\x00', '\x00', '\x00']
  CHAN8  = ['\x00', '\x00', '\x00']
  ACC_X  = ['\x00', '\x00']
  ACC_Y  = ['\x00', '\x00']
  ACC_Z  = ['\x00', '\x00']
  def convert_24_bit_to_int(self, raw_chan):
    MSB = raw_chan[0]
    if ord(MSB) > 126:
      prefix = '\xff'
    else:
      prefix = '\x00'
    new_int = struct.unpack('>i', prefix + ''.join(raw_chan))[0]
    return new_int
  def convert_16_bit_to_int(self, raw_acc):
    new_int = struct.unpack('h', ''.join(raw_acc))[0]
    return new_int

class StreamDecoder(object):
  '''
  Decodes the serial data stream and encodes packets to send to self.receiver
  Header = 0xA0, Seq
  Body = 30 bytes
  Footer = 0xC0
  '''
  def __init__(self, stream=None, receiver=None):
    self.stream = stream
    self.receiver = receiver
    self.sample_packet = Packet()
    self.byte_buffer = deque([], 256)
    self.packet_buffer = deque([self.sample_packet], 256)
    self.compile_methods()
  def compile_methods(self):
    self.bbappend = self.byte_buffer.append
    self.pbappend = self.packet_buffer.append
  def read_one_off_stream(self):
    b = self.stream.next()
    self.bbappend(b)
    return b
  def is_sequence_number_aligned(self, seq_num):
    if seq_num == 0:
      return self.packet_buffer[-1].SEQ == 255
    else:
      return self.packet_buffer[-1].SEQ + 1 == seq_num
  def encode_packet(self, packet_list):
    p = Packet()
    p.SEQ    = packet_list[1]
    p.CHAN1  = p.convert_24_bit_to_int(packet_list[2:5])
    p.CHAN2  = p.convert_24_bit_to_int(packet_list[5:8])
    p.CHAN3  = p.convert_24_bit_to_int(packet_list[8:11])
    p.CHAN4  = p.convert_24_bit_to_int(packet_list[11:14])
    p.CHAN5  = p.convert_24_bit_to_int(packet_list[14:17])
    p.CHAN6  = p.convert_24_bit_to_int(packet_list[17:20])
    p.CHAN7  = p.convert_24_bit_to_int(packet_list[20:23])
    p.CHAN8  = p.convert_24_bit_to_int(packet_list[23:26])
    p.ACC_X  = p.convert_16_bit_to_int(packet_list[26:28])
    p.ACC_Y  = p.convert_16_bit_to_int(packet_list[28:30])
    p.ACC_Z  = p.convert_16_bit_to_int(packet_list[30:32])
    return p
  def send_encoded_packet(self):
    p_list = range(self.sample_packet.LEN)
    while p_list[0] != '\xa0':
      b = self.read_one_off_stream()
      if b == '\xa0':
        p_list[0] = b 
        p_list[1] = ord(self.read_one_off_stream())
        seq_num_aligned = self.is_sequence_number_aligned(p_list[1])
        for i in range(31): #Fill the packet with data from stream, and check footer
          p_list[i+2] = self.read_one_off_stream()
        footer_aligned = p_list[32] == '\xc0'
    #if not foot_aligned: We need to figure on what to do when the footer is not aligned
    #  do_something() possibly flushing the buffers and reseting the connection
    #  this sounds extream but the event is potentially catistrophic
    if seq_num_aligned: #Send encoded packet to the receiver
      p = self.encode_packet(p_list)
      self.pbappend(p)
      self.receiver.send(p)
    else: #Send last encoded packet to receiver until the sequence number aligns
      this_seq_num = p_list[1]
      last_known_seq_num = self.packet_buffer[-1].SEQ
      for n in range(this_seq_num - last_known_seq_num):
        p = self.packet_buffer[-1]
        p.SEQ = last_known_seq_num + n + 1
        self.pbappend(p)
        self.receiver.send(p)

@decs.coroutine
def do_stuff():
  """
  This is an example receiver of encoded packets
  perhaps this function is a sanity test for sample rate
  we should see approx 1 second between every N samples where N is sample rate in Hz
  """
  i = 0
  tk = deque([0,0], 2)
  sample_rate = 250
  while True:
    p = yield
    i += 1
    if i % (sample_rate) == 0:
      tk.append(time.time())
      tbtwn = tk[1] - tk[0]
      print tbtwn, i, p.CHAN1, p.CHAN2

def main():
  stream = c.start_stream()
  receiver = do_stuff()
  d = StreamDecoder(stream=stream, receiver=receiver)
  while True:
    d.send_encoded_packet()

if __name__ == '__main__':
  try:
    c = Conn()
    main()
  except Exception, e:
    print e.args, e.message
  finally:
    c.stop_stream()
