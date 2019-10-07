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
        if (t.running or (t.done == False and t.resouce is not None) ):


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
    size_factor = 500
    labels = {}
    node_size = []
    node_color = []

    for n in list(G.nodes):

        #if node is train node
        if n in train_nodes:
            labels[n] = n
            node_size.append(800)
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
    nx.draw_networkx_edges(G, pos , width = 1 , arrowsize =20 , arrows = True , node_size = node_size ,ax=ax)

    ax.set_title('Resource Usage Graph')
