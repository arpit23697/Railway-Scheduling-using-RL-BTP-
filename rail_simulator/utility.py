import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
import random
import time
from network import *
import simpy
import logging


def create_resource_usage_graph (trains , N):
    '''
    Creates the resource usage graph based on current position of train and network
    @Parameters
    trains : All the train in the network
    N :      Railway network
    '''
    #Creating a directed graph, that shows the resource usage 
    G = nx.DiGraph()

    '''
    Iterate through each train:
    If the train is currently using some resource, then retrieve that resource using t.current attribute of train
    If the train is waiting for some resource, then retrieve that resource using t.waiting attribute of train
    '''
    #For better drawing
    train_nodes = set()
    station_nodes = set()
    track_nodes = set()


    for t in trains:
        #If the train is currently running or reached the destination but not freed the resource 
        if (t.running or (t.done == False and t.resource is not None) ):


            current = t.current
            #Check if the resource is track, then have the tuple in ascending order
            train_nodes.add(t.name)
            if type(t.current) is not str:

                if not (t.current[0] < t.current[1]):
                    current = (t.current[1] , t.current[0])

                track_nodes.add(current)
            else:
                station_nodes.add(current)

            #Add the edge to the directed graph
            G.add_edge(current , t.name)



        #If the train is waiting for some resource
        if not t.waiting == '-':
            waiting = t.waiting

            #Check if the resource is track or station
            if type(t.waiting) is not str:

                if not (t.waiting[0] < t.waiting[1]):
                    waiting = (t.waiting[1] , t.waiting[0])
                track_nodes.add(waiting)
            else:
                station_nodes.add(waiting)
            #Add the edge
            G.add_edge (t.name , waiting)

    return G,train_nodes , station_nodes , track_nodes

def draw_network_usage_graph(G , train_nodes , station_nodes , track_nodes , N , ax):
    '''
    Takes the resource usage graph and then draws
    @ Parameters
    G : Resource Usage graph
    ax : axes on which to draw the graph    
    train_nodes : nodes which are train
    station_nodes : nodes which are station
    track_nodes : nodes which are tracks
    N : railway network
    '''
    pos = nx.drawing.layout.planar_layout(G)

    '''Get the node attributes and the node color'''
    size_factor = 200
    labels = {}
    node_size = []
    node_color = []

    for n in list(G.nodes):

        #if node is train node
        if n in train_nodes:
            labels[n] = n
            node_size.append(300)
            node_color.append('pink')

        #If node is station
        elif n in station_nodes:
            s = N.G.nodes[n]['details']
            labels[n] = "{}\n{}/{}".format(n , s.total_free ,s.n_parallel_tracks)
            node_size.append(size_factor  * s.n_parallel_tracks)
            node_color.append('skyblue')

        #If node is track
        else:
            t = N.G[n[0]][n[1]]['details']
            labels[n] = "{} - {}\n{}/{}".format(n[0] , n[1] , t.total_free ,t.n_parallel_track)
            node_size.append(size_factor * t.n_parallel_track)
            node_color.append('yellowgreen')

    #Draw the labels
    nx.draw_networkx_labels(G , pos ,  labels = labels , font_size=8 , font_color='red' ,ax = ax)

    #Draw the nodes
    nx.draw_networkx_nodes(G , pos , node_size = node_size , node_color = node_color ,ax=ax )

    #Draw the edges
    nx.draw_networkx_edges(G, pos , width = 1 , arrowsize =10 , arrows = True , node_size = node_size ,ax=ax)

    ax.set_title('Resource Usage Graph')

# Function to find the system is in 
# safe state or not 
def isSafe(avail, maxm, allot): 
    '''
    Check if there is deadlock in the given state or not
    
    @Parameter
        avail : A 1D numpy array of size R to keep track of the available resources.
        maxm : 2D numpy array P * R, where each row shows need of each process. 
        allot : 2D numpy array P * R , where each row shows allocated resource. 
    @Return
        True,- : If there is no deadlock detected
        False , [] : List of processes responsible for deadlock
    
    '''
    #Get number of processes and resources
    P , R = maxm.shape[0] , maxm.shape[1]
    Safe = True
    
    need = maxm - allot
    # Mark all processes as finish  
    finish = [True] * P 
    
    #Check if some resource is allocated to a process then mark it unfinish
    for i in range(P):
        for j in range(R):
            if (allot[i][j] > 0):
                finish[i] = False
                break

    # Make a copy of available resources  
    work = avail
    
    while True:

        #If all the process finish then break
        if all(finish):
            break
            
        # Find a process which is not finish  
        # and whose needs can be satisfied  
        # with current work[] resources.  
        found = False
        for p in range(P):  

            # First check if a process is finished,  
            # if no, go for next condition  
            if (finish[p] == False):  
              
                # Check if for all resources  
                # of current P need is less  
                # than work 
                need_satisfied = True
                for j in range(R): 
                    if (need[p][j] > work[j]):
                        need_satisfied = False
                        break
                      
                # If all needs of p were satisfied.  
                if need_satisfied:  
                  
                    # Add the allocated resources of  
                    # current P to the available/work  
                    # resources i.e.free the resources  
                    for k in range(R):  
                        work[k] += allot[p][k]  

                    # Mark this p as finished  
                    finish[p] = True  
                    found = True
                  
        # If we could not find a next process  
        # in safe sequence.  
        if (found == False):  
            Safe = False
            break
          
    # If system is in safe state then  
    # safe sequence will be as below  
    if (Safe):
        return Safe , []
    else:
        #See which processes are responsible for deadlock
        deadlock_processes= []
        for i in range(P):
            if (finish[i] == False):
                deadlock_processes.append(i)
        return Safe , deadlock_processes

def create_state_for_deadlock (N , trains):
    '''
    Create available, allocated and resource matrix required for deadlock detection (Bank's algorithm)
    @Parameters
    N : Network
    trains : list of trains running on the network    
    @Return 
    Available, allocated and requested numpy array
    '''

    #Creating available matrix
    available = []

    #Get stations and tracks
    stations = N.get_stations()
    tracks = N.get_tracks()

    #Resource and processes
    R , P = len(stations) + len(tracks) , len(trains)
    #Create a map from resource (Track and station) to integer
    resource_int_map = {}
    index = -1

    for s in stations:
        index+=1
        resource_int_map[s.name] = index

        #Available resources for station
        available.append(s.n_parallel_tracks - s.resource.count)


    for t in tracks:
        index+=1

        #Resource to int map
        if t.node_x < t.node_y:
            resource_int_map[(t.node_x , t.node_y)] = index
        else:
            resource_int_map[(t.node_y , t.node_x)] = index

        #Available resource for track
        available.append(t.n_parallel_track- t.resource.count)


    allot = np.zeros((P,R ))
    req = np.zeros( (P , R) )

    for p, t in enumerate(trains):
        #Train is running
        if (t.running or (t.done == False and t.resource is not None) ):

            #See if the current is station or track 
            current = t.current
            if type(t.current) is not str:
                if not (t.current[0] < t.current[1]):
                    current = (t.current[1] , t.current[0])

            #get the index and allocate the corresponding resource to train p
            index = resource_int_map[current]
            allot[p][index] = 1

        if not t.waiting == '-':
            waiting = t.waiting

            #Check if the resource is track or station
            if type(t.waiting) is not str:

                if not (t.waiting[0] < t.waiting[1]):
                    waiting = (t.waiting[1] , t.waiting[0])

            #get the index and request for the corresponding resource to train p
            index = resource_int_map[waiting]
            req[p][index] = 1
    
    return available , allot , req

def deadlock_detection (N , trains):
    '''
    Detects the deadlock in the network
    @Parameters:
        N : Network
        trains : trains running on the network
    '''
    available , allocated , requested = create_state_for_deadlock (N , trains)
    safe , deadlock_processes= isSafe(available , allocated + requested ,allocated )
    return safe , deadlock_processes
