# turtlife.py - Artistic License w/ Attribution -> "(evil) Dan of MOISEBRIDGE"
# note: press 'n' to advance frame, 'r' to run, 'p' to pause

from turtle import Screen, Turtle, mainloop
from itertools import islice, product, repeat, starmap
from random import randint
from time import sleep
from run import Conn, StreamDecoder, Packet
from decs import coroutine

class CellLogic(object):
  def __init__(self, rules='life'):
    self.rules = rules
  def evaluate(self, criteria):
    ret = None
    if self.rules == 'eeg':
      packet = criteria
      print("got packet")
    if self.rules == 'life':
      val, n = criteria
      if n == 2:
        destiny = val
      elif n == 3:
        destiny = 1
      else:
        destiny = 0
      ret = (destiny, n)
    elif self.rules == 'prime':
      val, n = criteria
      if n in (2, 3):
        destiny = 1
      elif n in (5, 7):
        destiny = val
      else:
        destiny = 0
      ret = (destiny, n)
    return ret
  def toggle(self):
    if self.rules == 'life':
      self.rules = 'prime'
    elif self.rules == 'prime':
      self.rules = 'life'

class EEG(object):
  def __init__(self):
    print("initializing EEG")
    try:
      self.c = Conn()
      self.receiver = self.do_stuff()
      self.stream = self.c.start_stream()
      print("We have a stream decoder")
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      traceback.print_exception(exc_type, exc_value, exc_traceback)
    finally:
      self.c.stop_stream()
  @coroutine
  def do_stuff(self):
    print("do_stuff about to loop / yield")
    while True:
      packet = yield
      print("we have a packet")
      raw_chan_1 = packet.CHAN1
      print(raw_chan_1)
  def read_eeg_packet(self):
    return self.stream.next()
    #self.stream_decoder.send_encoded_packet() 
    #return self.receiver.next()

class Cell(object):
  def __init__(self, colony, row, col):
    self.colony = colony
    self.row = row
    self.col = col
    self.val = 0
    self.extra = 0
    self.logic = colony.logic
    self._neighbors = None
  def neighbors(self):
    if self._neighbors is None:
      self._neighbors = list(self.colony.neighbormap(self))
    return self._neighbors
  def neighborsum(self):
    return sum(o.val for o in self.neighbors())
  def destiny(self):
    if self.logic.rules == 'eeg':
      criteria = self.colony.eeg.read_eeg_packet()
    elif self.logic.rules in ('prime', 'life'): 
      criteria = (self.val, self.neighborsum())
    return self.logic.evaluate(criteria)
  def value(self, val=None, extra=None):
    if val is not None:
      self.val = val
    if extra is not None:
      self.extra = extra
    return self.val
  def valchar(self):
    return (' ', 'o')[self.val]

class Raster(object):
  def __init__(self, logic, displaymode, rows, cols):
    self.logic = logic
    self.displaymode = displaymode
    self.eeg = EEG()
    self.rows = rows
    self.cols = cols
    self.cells = list(starmap(
      lambda x, y: Cell(self, x, y),
      product(range(rows), range(cols)) ))
    self.turtles = None
    self.state = State(self)
  def rowslice(self, r):
    i = r * self.cols
    return islice(self.cells, i, i + self.cols)
  def neighborhood(self, row, col):
    up = row - 1 if row else self.rows - 1
    down = row + 1 if row < self.rows - 1 else 0
    left = col - 1 if col else self.cols - 1
    right = col + 1 if col < self.cols - 1 else 0
    return ( (up, left), (up, col), (up, right),
             (row, left),             (row, right),
             (down, left), (down, col), (down, right) )
  def neighbormap(self, o):
    otype = type(o)
    if otype is Cell:
      sq = self.cells
    elif otype is CellularTurtle:
      sq = self.turtles
    else:
      sq = []
    return starmap(
      lambda x, y: sq[x * self.cols + y],
      self.neighborhood(o.row, o.col) )
  def turtledisplay(self):
    if self.turtles is None:
      self.turtles = list(starmap(
        lambda x, y: CellularTurtle(self, x, y),
        product(range(self.rows), range(self.cols)) ))
    for c, t in zip(self.cells, self.turtles):
      if c.val:
        if c.extra == 2:
          t.rgb = list(t.colors['blue'])
        elif c.extra == 3:
          t.rgb = list(t.colors['green'])
        elif c.extra == 5:
          t.rgb = list(t.colors['yellow'])
        elif c.extra == 7:
          t.rgb = list(t.colors['red'])
      else:
        if self.displaymode == 'ambient':
          t.rgb = list(t.ambience())
        elif self.displaymode == 'fade':
          for i in range(3):
            t.rgb[i] *= 0.618
        else:
          t.rgb = list(t.colors['black'])
      t.color(t.rgb)
  def textdisplay(self):
    # print(': '.join((self.logic.rules, hex(self.state.value()))))
    print(self.state.bitstring())
    for r in range(self.rows):
      print(''.join(map(lambda x: x.valchar(), self.rowslice(r))))
  def display(self):
    self.turtledisplay() 
    self.textdisplay() 

class State(object):
  def __init__(self, colony):
    self.colony = colony
  def value(self):
    bits = 0
    for o in self.colony.cells:
      bits += o.val
      bits <<= 1
    return bits
  def context(self):
    return (self.colony.logic.rules, self.colony.rows, self.colony.cols)
  def bitstring(self):
    return '{0:0>b}'.format(self.value())

class CellularTurtle(Turtle):
  def __init__(self, colony, row, col):
    Turtle.__init__(self)
    self.colony = colony
    self.row = row
    self.col = col
    self.speed(0)
    # self.hideturtle()
    self.shape("turtle")
    self.settiltangle(45)
    self.resizemode("user")
    self.shapesize(1, 1, 0)
    self.penup()
    self.setx(col)
    self.sety(row)
    self.colors = dict( (
      ( 'black', (0.0, 0.0, 0.0) ),
      ( 'grey50', (0.5, 0.5, 0.5) ),
      ( 'white', (1.0, 1.0, 1.0) ),
      ( 'red', (0.7, 0.0, 0.0) ),
      ( 'yellow', (0.7, 0.7, 0.0) ),
      ( 'green', (0.0, 0.7, 0.0) ),
      ( 'blue', (0.0, 0.0, 0.7) ) ) )
    self.rgb = list(self.colors['black'])
    self.color(self.rgb)
    self._neighbors = None
  def neighbors(self):
    if self._neighbors is None:
      self._neighbors = list(self.colony.neighbormap(self))
    return self._neighbors
  def avg_rgb(self, turtles):
    rgb = [0.0, 0.0, 0.0]
    n = len(turtles)
    for t in turtles:
      for i in range(3):
        rgb[i] += t.rgb[i]
    return map(lambda x: x/n, rgb)
  def ambience(self):
    return self.avg_rgb(self.neighbors())

class CellRunner(object):
  def __init__(self, rules, displaymode, rows, cols):
    self.logic = CellLogic(rules)
    self.raster = Raster(self.logic, displaymode, rows, cols) 
    self.randomize()
  def randomize(self):
    list(map(lambda x: x.value(randint(0, 1)), self.raster.cells))
  def update(self, sync=True):
    dst = map(lambda x: x.destiny(), self.raster.cells)
    if sync:
      dst = list(dst)
    list(starmap(
       lambda x, y: x.value(*y),
      zip(self.raster.cells, dst) )) 
    self.raster.display() 
  def run(self, n=0, delay=0.1):  # delay in seconds
    f = (lambda: repeat(1, n)) if n else (lambda: repeat(1))
    for x in f():
      try:
        self.update(sync=True)
        if(delay):
          sleep(delay)
      except:
        break

class ScreenRunner(object):
  def __init__(self, rules='prime', displaymode='ambient', rows=16, cols=32):
    self.screen = self.initscreen(rows, cols)
    self.cellrunner = CellRunner(rules, displaymode, rows, cols)
    self.running = False
    self.next()
  def initscreen(self, rows, cols):
    screen = Screen()
    screen.delay(0)
    offset = map(lambda x: x - 0.3, (0, rows, cols, 0))
    screen.setworldcoordinates(*offset)
    screen.bgcolor(0.0, 0.0, 0.0)
    screen.tracer(n=rows*cols)
    self.bindkeys(screen)
    return screen
  def bindkeys(self, screen):
    screen.onkey(self.randomize, 'x')
    screen.onkey(self.mode, 'm')
    screen.onkey(self.next, 'n')
    screen.onkey(self.next, 'n')
    screen.onkey(self.run, 'r')
    screen.onkey(self.save, 's')
    screen.onkey(self.pause, 'p')
    screen.onkey(self.quit, 'q')
    screen.listen()
  def randomize(self):
    self.cellrunner.randomize()
    self.next()
  def mode(self):
    self.cellrunner.logic.toggle()
  def next(self):
    print("next")
    self.cellrunner.run(1, 0)
  def run(self):
    self.running = True
    self.timer()
  def save(self):
    self.pause()
    s = ''.join(str(o.val) for o in self.cellrunner.raster.cells)
    print(s)
  def pause(self):
    self.running = False
  def quit(self):
    exit()
  def timer(self, delay=100):  # delay in milliseconds
    if self.running:
      self.next()
      self.screen.ontimer(lambda: self.timer(delay), delay)

def main():
  sr = ScreenRunner(rules='eeg', displaymode='fade', rows=17, cols=31)
  return "EVENTLOOP"

if __name__ == "__main__":
  msg = main()
  print(msg)
  mainloop()
