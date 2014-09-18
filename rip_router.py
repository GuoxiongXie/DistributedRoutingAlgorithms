from sim.api import *
from sim.basics import *
import time

class RIPRouter (Entity):

  def __init__ (self):
    self.table = {}		#In table, key is (destination,port,distance);value is randomly set to be 0
    self.switchPortList	= []	#keep track of the ports to switches; only send RoutingUpdate packets to swithes,not hosts

  def handle_rx (self, packet, port):
    if isinstance(packet, RoutingUpdate):	#handle updatePacket(the packets sent between switches)
      
      """
      If RoutingUpdate, we have 2 cases: 1. link-down case; 2. just share update info(including the link-up and normal sharing case)
      """
      flag = 0			#flag is used for control the sending of RoutingUpdate packets. 0 means stop sending, 1 means sending.	
      
      allDest = packet.all_dests()	#allDest is a list of the destination in update packet;there maybe redundant dest here(link-up case)
      
      """
      case 1: link down 
      """
      print "allDest is %s" % allDest
      if isinstance(packet.get_distance(allDest[0]), tuple):
        #print "go in handle_rx link down part!!!"
        downTripleList = [(dest, port, packet.get_distance(dest)) for dest in allDest]
	downTripleList = filter(lambda x: x[2]<=30, downTripleList)

        """
        create a hash table version of downTripleList to make it work faster, only need first time overhead
        """
        downTripleTable = {}
        for triple in downTripleList:
          downTripleTable[triple] = 0
          
        keyList = self.table.keys()
        specificPortTripleList = filter(lambda x: x[1]==port, keyList)	#triples with a specific port in the forwarding table,works even keyList is empty
        print "specificPortTripleList is %s" % specificPortTripleList.keys()  
        if len(specificPortTripleList) != 0: 
          for triple in specificPortTripleList:
            if downTripleTable.has_key(triple) == False:	#don't have this path anymore
              flag = 1
              self.table.pop(triple)				#remove it from forwarding table
            else:						#if the switch table has it already
              downTripleTable.pop(triple)			#remove from the downPacket the triple already in the forwarding table
		
        newDownTripleList = downTripleTable.keys()
        if len(newDownTripleList) != 0:			#we need to add something to the table and send the update
          flag = 1
          for triple in newDownTripleList:
            self.table[triple] = 0			#add it to the forwarding table
              
        if flag == 1:				#the table has been modified, we need to send all info in the table to others
	    
          keyList = self.table.keys()
          print "keyList is %s and the switch is %s" % (keyList,self)
          PRupdatePacket = RoutingUpdate()
          updatePacket = RoutingUpdate()
          destList = [x[0] for x in keyList]  
          destList = list(set(destList))	#no duplicate destination in destList
          downOptimalKeyList = []		#stores those paths in downTripleList that's optimal
        
          for dest in destList:		# the dest is a triple
            sameDestKeyList = filter(lambda x: x[0]==dest, keyList)		#triples with same dest in table
            optimalKey = sameDestKeyList[0]			#randomly pick the first one as optimal key
            i=1				#a counter
            while i < len(sameDestKeyList):
              curDist = sameDestKeyList[i][2]
              if optimalKey[2] > curDist:
                optimalKey = sameDestKeyList[i]
                i=i+1
              elif optimalKey[2] == curDist:
                if optimalKey[1] > sameDestKeyList[i][1]:
                  optimalKey = sameDestKeyList[i]
                  i=i+1
                else:
                  i=i+1
                  continue
              else:
                i=i+1
                continue
            if optimalKey in downTripleList:
              downOptimalKeyList.append(optimalKey)

          if len(downOptimalKeyList) == 0:		#there's no optimal paths in downTripleList
            #print "keyList is %s" % keyList
            destDistPairs = [(x[0],x[2]) for x in keyList]   #a list of tuples (destination,distance) from table
            #print "the destDistPairs is %s" % destDistPairs
            for pair in destDistPairs:
              updatePacket.add_destination(pair[0],(pair[1]+1, 'down'))
            print "first case man!!!I'm %s and updatePacket dests are %s" % (self,updatePacket.all_dests())  
            self.send(updatePacket, port=self.switchPortList, flood=False) #send out all info

          else:
            for key in keyList:
              if key in downOptimalKeyList:
                PRupdatePacket.add_destination(key[0], (100,'down'))	# poison reverse; if we drop >30 hops, what's the point of doing poison reverse???
                updatePacket.add_destination(key[0], (key[2]+1,'down'))	# this one is send to switches except port
              else:
                PRupdatePacket.add_destination(key[0], (key[2]+1,'down'))
                updatePacket.add_destination(key[0], (key[2]+1,'down'))
            print "handle RX down1. I'm %s and updatePacket dests are %s" % (self,updatePacket.all_dests())   
            self.send(updatePacket, port, flood=True) #send out to the neigbor switches, only send the optimal path for each dest
            print "handle RX down2. I'm %s and PRupdatePacket dests are %s" % (self,PRupdatePacket.all_dests())
            self.send(PRupdatePacket, port, flood=False) #send out to the neigbor switches, only send the optimal path for each dest


      else:  #link-up
        originalKeyList = self.table.keys()
        upTripleList = [(dest, port, packet.get_distance(dest)) for dest in allDest]	#this can only be the list of optimal paths
        for triple in upTripleList:
          if triple[2] <= 30:			#drop hop count bigger than 30
            self.table[triple] = 0		#add it to the table

        latestKeyList = self.table.keys()
        if latestKeyList != originalKeyList:    #table changed
          keyList = self.table.keys()
          PRupdatePacket = RoutingUpdate()
          updatePacket = RoutingUpdate()
          destList = [x[0] for x in keyList]  
          destList = list(set(destList))	#no duplicate destination in destList
          
          for dest in destList:		# the dest is a triple
            sameDestKeyList = filter(lambda x: x[0]==dest, keyList)		#triples with same dest in table
            optimalKey = sameDestKeyList[0]			#randomly pick the first one as optimal key
            i=1				#a counter
            while i < len(sameDestKeyList):
              curDist = sameDestKeyList[i][2]
              if optimalKey[2] > curDist:
                optimalKey = sameDestKeyList[i]
                i=i+1
              elif optimalKey[2] == curDist:
                if optimalKey[1] > sameDestKeyList[i][1]:
                  optimalKey = sameDestKeyList[i]
                  i=i+1
                else:
                  i=i+1
                  continue
              else:
                i=i+1
                continue
            if optimalKey in upTripleList:		#my neigbor pass me the optimal path       
              PRupdatePacket.add_destination(optimalKey[0], 100)	# poison reverse; if we drop >30 hops, what's the point of doing poison reverse???
              updatePacket.add_destination(optimalKey[0], optimalKey[2]+1)	# this one is send to switches except port
              
            else:
              PRupdatePacket.add_destination(optimalKey[0], optimalKey[2]+1)	# +1 because we will store the distance value in this switch's neighbor
              updatePacket.add_destination(optimalKey[0], optimalKey[2]+1)	# +1 because we will store the distance value in this switch's neighbor
            """
            print "sending rx-up1: limited by 30s timer................."
            create_timer(30,self.send,recurring=True,args=(updatePacket, port,True))
	    #print "sending rx-up2: limited by 30s timer................."
            create_timer(30,self.send,recurring=True,args=(PRupdatePacket, port,False))
            """
          #print "sending rx-up1................."
          self.send(updatePacket, port, flood=True) #send out to the neigbor switches, only send the optimal path for each dest
          #print "sending rx-up2................."
          self.send(PRupdatePacket, port, flood=False) #send out to the neigbor switches, only send the optimal path for each dest   
            

    else:     #packets sent between hosts
      """
      find the port we send out the packet 
      """
      destination = packet.dst
      keyList = self.table.keys()
      destList = filter(lambda x: x[0] == destination, keyList)	#a list of (dest,port,distance)
      
      if len(destList) != 0:
        
        distanceList = [x[2] for x in destList]			#a list of distance
        minDistance = min(distanceList)
        
        destList = filter(lambda x: x[2] == minDistance, destList)	#now destList contains only the triple with shortest distance
	
        portList = [x[1] for x in destList]				#a list of port
        minPort = min(portList)						#minPort is what we want
    	
        """
        route the packet through minPort
        """
        #print "sending a normal packet................."
        self.send(packet, minPort, flood=False)



  def handle_link_up (self, port, entity):
    if isinstance(entity,HostEntity):		#if the switch connects to a host
      self.table[(entity,port,1)] = 0		#store the host in the forwarding table. Randomly pick the value to be 0 in the table.
      if len(self.switchPortList) != 0:	#switchPortList is not empty
        updatePacket = RoutingUpdate()	# declare an object of RoutingUpdate class
        
        keyList = self.table.keys()
        destList = [x[0] for x in keyList]  
        destList = list(set(destList))	#no duplicate destination in destList
        
        for dest in destList:		# the dest is a triple
          sameDestKeyList = filter(lambda x: x[0]==dest, keyList)		#triples with same dest in table
          optimalKey = sameDestKeyList[0]			#randomly pick the first one as optimal key
          i=1				#a counter
          while i < len(sameDestKeyList):
            curDist = sameDestKeyList[i][2]
            if optimalKey[2] > curDist:
              optimalKey = sameDestKeyList[i]
              i=i+1
            elif optimalKey[2] == curDist:
              if optimalKey[1] > sameDestKeyList[i][1]:
                optimalKey = sameDestKeyList[i]
                i=i+1
              else:
                i=i+1
                continue
            else:
              i=i+1
              continue
            
          updatePacket.add_destination(optimalKey[0], optimalKey[2]+1)	# +1 because we will store the distance value in this switch's neighbor
        #print "Fxn hadle_link_up sending: host case................."  
        self.send(updatePacket, self.switchPortList, flood=False) #send out to the neigbor switches, only send the optimal path for each dest
        
    else:  #if the entity is a switch
      self.switchPortList.append(port)		#add this port to switchPortList
      	
      keyList = self.table.keys()
      if len(keyList) != 0:			#if table is not empty, the switches should share info
        updatePacket = RoutingUpdate()	# declare an object of RoutingUpdate class
        
        destList = [x[0] for x in keyList]  
        destList = list(set(destList))	#no duplicate destination in destList
        
        for dest in destList:		# the dest is a triple,find the optimal paths for every destination
          sameDestKeyList = filter(lambda x: x[0]==dest, keyList)		#triples with same dest in table
          optimalKey = sameDestKeyList[0]			#randomly pick the first one as optimal key
          i=1
          while i < len(sameDestKeyList):
            curDist = sameDestKeyList[i][2]
            if optimalKey[2] > curDist:
              optimalKey = sameDestKeyList[i]
              i=i+1
            elif optimalKey[2] == curDist:		#equal distance
              if optimalKey[1] > sameDestKeyList[i][1]:	#prefer smaller port number
                optimalKey = sameDestKeyList[i]
                i=i+1
              else:
                i=i+1
                continue
            else:		#the current optimal path is unbeatable 
              i=i+1
              continue
            
          updatePacket.add_destination(optimalKey[0], optimalKey[2]+1)	# +1 because we will store the distance value in this switch's neighbor
        #print "Fxn hadle_link_up sending: switch case................."  
        self.send(updatePacket, self.switchPortList, flood=False) #send out to the neigbor switches, only send the optimal path for each dest


  def handle_link_down (self, port, entity):
    #print "I'm %s, the port number I have is %d" % (self,self.get_port_count())
    #print "switchPortList is %s" % self.switchPortList
    updatePacket = RoutingUpdate()
    if isinstance(entity,HostEntity) == False: 
      self.switchPortList.remove(port)
    #print "later, the port number I have is %d" % (self.get_port_count())
    #print "the new SwitchPortList is %s" % self.switchPortList
    deleteList = filter(lambda x: x[1] == port, self.table.keys())
    for deleteKey in deleteList:     #remove key in the table
      self.table.pop(deleteKey)
    keyList = self.table.keys()
    for key in keyList: #create packet
      updatePacket.add_destination(key[0], (key[2]+1, 'down'))
    #print "Fxn hadle_link_down sending................."
    #print "down..I'm %s and send to ports: %s" % (self, self.switchPortList)
    #print "updatePacket is %s" % updatePacket.all_dests()
    self.send(updatePacket, self.switchPortList, flood=False)   #send packet
