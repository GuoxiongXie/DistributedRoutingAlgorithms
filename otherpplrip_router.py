from sim.api import *
from sim.basics import *
import time

class RIPRouter (Entity):
  """ A not simple hub """

  def __init__(self):
      self.dvTable = {}
      self.dvMinTable = {}
      
      
  def handle_rx (self, packet, port):
    """
    blah
    """
   # print "rip1"
    
    if isinstance(packet, RoutingUpdate):
        somethingChanged = False
        for k in packet.all_dests():
            
            if not (k,port) in self.dvTable.keys():
                self.dvTable[(k,port)] = 1+packet.get_distance(k)
                
            
                if k not in self.dvMinTable.keys(): 
                    self.dvMinTable[k] = (port, self.dvTable[k,port])
                    somethingChanged = True
                else:
                    if self.dvMinTable[k][1] > self.dvTable[(k,port)]:#a better distance has been found
                        self.dvMinTable[k] = (port, self.dvTable[k,port])
                        somethingChanged = True
                    
            else: #it's already in the table
                #if self.dvTable[(k,port)] > 1+packet.get_distance(k):
                self.dvTable[(k,port)] = 1+packet.get_distance(k)
                oldMinPort = self.dvMinTable[k][0]
                oldMinDist = self.dvMinTable[k][1]
                bestMinPort = None
                bestMinDist = 100
                for i in range(self.get_port_count()):
                    if (k,i) in self.dvTable.keys():
                        if bestMinDist > self.dvTable[(k,i)]:
                            bestMinDist = self.dvTable[(k,i)]
                            bestMinPort = i

                if (bestMinPort != oldMinPort) or (bestMinDist != oldMinDist):
                    somethingChanged = True
                    self.dvMinTable[k] = (bestMinPort, bestMinDist)
                if (bestMinPort!=oldMinPort and bestMinDist==oldMinDist) or (bestMinPort==oldMinPort and bestMinDist!=oldMinDist):
                    print "i don't know what's going on"
                    
                print "ultimate debug " + str(self) + str(oldMinPort) + " " + str(oldMinDist) + " " + str(bestMinPort) + " " + str(bestMinDist)
                print "continued: " + str(self.dvTable)
                print "continued1: " + str(self.dvMinTable)
            
        if somethingChanged:
            #pa = RoutingUpdate()
            #for ke in self.dvMinTable.keys():
            #    pa.add_destination(ke, self.dvMinTable[ke][1])
            #self.send(pa, port, flood=True)
            
            
            for i in range(self.get_port_count()):
                pa = RoutingUpdate()
                for ke in self.dvMinTable.keys():
                    if i == self.dvMinTable[ke][0]:
                        pa.add_destination(ke, 100)
                    else:
                        pa.add_destination(ke, self.dvMinTable[ke][1])
                        self.send(pa, i, flood=False)
            
            
            
            
            print "hi1 " + str(self) + " " + str(self.dvMinTable)
    else:
        if not packet.dst in self.dvMinTable.keys():
            print "ASDF ERROR " + str(packet.dst) + " "  + str(self.dvMinTable.keys())
        else: 
            print "wtf " + str(packet.dst) + " " + str(self.dvMinTable[packet.dst])
            if self.dvMinTable[packet.dst][1] < 100:
                self.send(packet, self.dvMinTable[packet.dst][0], flood=False)
        
    
  def handle_link_up (self, port, entity):
    """
    adsfasfd
    """
    #print "ripup"
    if isinstance(entity, BasicHost):
        self.dvTable[entity, port] = 1
        self.dvMinTable[entity] = (port, 1)
    else:
        pa = RoutingUpdate()
        for ke in self.dvMinTable.keys():
            pa.add_destination(ke, self.dvMinTable[ke][1])
        self.send(pa, port, flood=False)
        
    
        
  def handle_link_down (self, port, entity):
    """
    asdffdsa
    """ 
    #self.dvTable[(entity,port)] = 100
    
    for key in self.dvTable.keys():
        p = key[1]
        if p == port:
            #it's the same as the port that went down!
            self.dvTable[key] = 100


    for key in self.dvMinTable.keys():
        p = self.dvMinTable[key][0]
        if p == port:
            #it's the same as the port that went down!

            bestMinPort = None
            bestMinDist = 100
            for i in range(self.get_port_count()):
                if (key,i) in self.dvTable.keys():
                    if bestMinDist > self.dvTable[(key,i)]:
                        bestMinDist = self.dvTable[(key,i)]
                        bestMinPort = i
        
            self.dvMinTable[key] = (bestMinPort, bestMinDist)
    
    
    
    
    
    for i in range(self.get_port_count()):
        pa = RoutingUpdate()
        for ke in self.dvMinTable.keys():
            if i == self.dvMinTable[ke][0]:
                pa.add_destination(ke, 100)
            else:
                pa.add_destination(ke, self.dvMinTable[ke][1])
        self.send(pa, i, flood=False)
    
    
    
    print "hi " + str(self) + " " + str(self.dvMinTable)


    #print "ripdown"