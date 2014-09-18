import sim
from sim.api import *
from sim.core import CreateEntity, topoOf
from sim.basics import BasicHost
from learning_switch import LearningSwitch
import sim.topo as topo

def create (switch_type = LearningSwitch, host_type = BasicHost):
    

    switch_type.create('s1')
    switch_type.create('s2')
    switch_type.create('s3')
    

    host_type.create('h1')
    host_type.create('h2')
    host_type.create('h3')
    host_type.create('h4')
    host_type.create('h5')
    host_type.create('h6')

    topo.link(s1, h1)
    topo.link(s1, h2)
    topo.link(s2, s1)
    topo.link(s1, s3)

    topo.link(s2, h3)
    topo.link(s2, h4)

    topo.link(s3, h5)
    topo.link(s3, h6)

    print "testing: type(h1)==HostEntity? should be True. The answer is %s" % isinstance(h1, HostEntity)
    print "testing: type(s1)==HostEntity? should be False. The answer is %s" % isinstance(s1, HostEntity)
    print "testing: type(s1)==Entity? should be True. The answer is %s" % isinstance(s1, Entity)
    print "testing: type(h1)==Entity? Should be True. the answer is %s" % isinstance(h1, Entity)
    
