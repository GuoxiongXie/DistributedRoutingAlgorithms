from sim.api import *
from sim.basics import *
import time

class LearningSwitch (Entity):
  """ A simple hub -- floods all packets """
  def __init__ (self):
    self.enPoTable = {}    #enPoTable stores entity-port pairs
  
  def handle_rx (self, packet, port):
    self.enPoTable[packet.src] = port  #add a new entity-port pair
    
    destination = packet.dst
    if self.enPoTable.has_key(destination) == False: 
      self.send(packet, port, flood=True)
    else:
      self.send(packet,self.enPoTable[destination], flood=False)

  def handle_link_up (self, port, entity):
    """
    Do nothing
    """

  def handle_link_down (self, port, entity):
    """
    Do nothing
    """ 
