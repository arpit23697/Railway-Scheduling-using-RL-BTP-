#Creating the train class
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
import random
import time
from network import *
from utility import *
import config
import simpy
import logging


class Train:
    id_ = 0
    def __init__ (self  , name , avg_speed , priority , route  , env , network , logger):
        '''
        @parameters 
        name         : name of the train
        avg_speed    : average speed of the train
        priority     : priority of the train, later will be used in the algorithm
        route        : a python list of tuples of three elements that gives the stations on the route along with 
                        the expected time of arrival and departure
        env          : Simpy environment where simulation is done
        network      : network on which the train is running 
        logger       : For creating the log of each train. Can be none : In which case no log will be created 
        
        TODO
        ____________________________________
        
        Notes :
        1. Time is just an integer for now. It can change in the future.
        2. Simmulation starts at time 0. So the time in the route should always be greater than 0
        3. self.current : gives the name of the station or the track train is currently using
        4. Arrival and departure time are coded in the route 
        
        5. There are two sets of functions : Simulate and non_simulate
                                            Simulate Wait for the resource till it is free
                                            Non Simulate return -1 if the resource is not free.
        '''
        #Global variables
        
        #initialise the variables
        self.__class__.id_ += 1
        self.id = self.__class__.id_
        self.name = name
        self.speed = avg_speed
        self.priority = priority
        self.route = route
        self.env = env              
        self.network = network

        #for the current status of the train
        self.running = False                        #True if the train is running                        
        self.station_or_not = False                 #True if standing on station
        self.current = '_'                          #Current station name or the track (tuple)
        self.current_index = -1                     #upto which point the route is travelled
        self.current_track = -1                     #current track number on the particular station or track  
        self.done = False                           #indicate wether the journey is complete or not
        
        #resource that the train is acquiring currently
        self.resource = None   
        self.request = None
        
        #for storing the log
        self.log = [(d , -1 , -1) for d,t_a , t_d in route]          #(station_name , arrival , departure)
        self.logger = logger
        
        #resource that the train is waiting for
        self.waiting = '-'                         #name of the station or track : train is waiting for
        
        #All the resources that the train will acquire in it's journey
        self.all_resources = []
        for i in range(len(route)):
            self.all_resources.append(route[i][0])
            if (i + 1 < len(route)):
                self.all_resources.append((route[i][0] , route[i+1][0]))

    def reset (self , env , N):
        ''' 
            Resets the train and update the environment
        '''
        self.env = env 
        self.network = N 

        self.running = False                        #True if the train is running                        
        self.station_or_not = False                 #True if standing on station
        self.current = '_'                          #Current station name or the track (tuple)
        self.current_index = -1                     #upto which point the route is travelled
        self.current_track = -1                     #current track number on the particular station or track  
        self.done = False                           #indicate wether the journey is complete or not

        self.resource = None   
        self.request = None
        
        #for storing the log
        self.log = [(d , -1 , -1) for d,t_a , t_d in self.route]          #(station_name , arrival , departure)
        self.waiting = '-'                         #name of the station or track : train is waiting for


    def compute_time (self , distance):
        '''
        returns the time needed to travel the distance  
        @paramters :
        distance : to be travelled
        
        '''
        return distance/self.speed
        
    def create_log (self , s):
        '''
        Takes the string as argument
        Creates the log : if logger is not None
        '''
        if (self.logger is not None):
            self.logger.info(s)
            
        
    def put_train_on_track (self , env):
        '''
        This function takes the train, see the arrival time of the train at the first station and
        generates the event that corresponds to time 
        that now is the time to put the train in the network.
        '''
        
        self.create_log ("Time : {} -- Train {} Putting in the network".format(env.now, self.name))
        
        start_station , start_time , _ = self.route[0]
        #wait till the right time comes to put the train in the network
        wait = max (0 , start_time - env.now)
        yield env.timeout(wait)
        
        self.create_log("Time : {} -- Train {} Can be put in the network".format(env.now , self.name))
        #Put the train in the event list
        config.TRAINS_NEEDING_ACTION.append(( env.now, self.name))
        
            
    def wait_train (self, env):
        '''
        This function waits for one unit time
        '''
        self.create_log("Time : {} -- Train {} Wait for 1 unit time".format(env.now , self.name))
        yield env.timeout(1)
            
    def move_train_simulate (self , env):
        '''
        ONLY FOR SIMULATION
        This function runs the train
        This function is only used for simulation purpose
        It will start the whole train and then finishes the journey
        The actions are always to move
        '''
        #Create the relevant processes
        initiate_train_proc = env.process (self.initiate_train_simulate(self.env))
        yield initiate_train_proc

        while self.done == False:
            move_train_one_step_proc = env.process (self.move_train_one_step_simulate(env))
            yield move_train_one_step_proc
            
        
        finish_journey_process = env.process (self.finish_journey_simulate(self.env))
        yield finish_journey_process
    
    def act_simulate (self , env , action):
        '''
        Depending on the action given the train will either move or stop
        Only two actions are there : move or stop
        move:
             If the train is not yet started then put it on the track
             If train is running then move one step
             If train has completed the journey but not freed resource then free it.
             If train has completed the journey and freed resource then do nothing.
        wait:
            wait for 1 unit time
            
        NOTE : The action taken are for simulation. If the resource is not free, then instead of returning
              it will wait till the resource is free.
        '''
        
        assert action in ['move' , 'wait']
        
        self.create_log("Time : {} -- Acting for train {}".format(env.now , self.name))
        if action == 'move':
            
            #Train is not yet started
            if (self.done == False and self.running == False):
                initiate_train_proc = env.process (self.initiate_train_simulate(self.env))
                yield initiate_train_proc
                
                #Put the train in line for taking action at a particular time
                config.TRAINS_NEEDING_ACTION.append(( env.now, self.name))
                
            #Train is running
            elif (self.running == True):
                move_train_one_step_proc = env.process (self.move_train_one_step_simulate(env))
                yield move_train_one_step_proc
                
                config.TRAINS_NEEDING_ACTION.append(( env.now, self.name))
            
            #train has completed the journey but the resource is not freed
            elif (self.done == True and self.resource is not None):
                finish_journey_process = env.process (self.finish_journey_simulate(self.env))
                yield finish_journey_process
        
                #Since the journey is complete no need of taking further action
            else:
                self.create_log('Time : {} -- Train {} has completed the journey'.format(env.now , self.name))
        
            
        #wait for one unit time
        else:
            
            #Warning if train has completed the journey
            if (self.done == True and self.resource is None):
                self.create_log('Time : {} -- Train {} has completed the journey'.format(env.now , self.name))
            
            #Wait for 1 minute
            wait_train_proc = env.process(self.wait_train(self.env))
            yield wait_train_proc
            #Put the train in the list
            config.TRAINS_NEEDING_ACTION.append(( env.now, self.name))

    def initiate_train_simulate (self , env):
        '''
        This function puts the train on the track
        @parameters
        env : simpy environment
        
        Note : If the resource is not free, then it will wait till the resource is free.
        '''
        self.create_log("Time : {} -- Train {} initiating".format(env.now, self.name) )
        start_station , start_time , depart_time = self.route[0]
        
        #wait till the right time comes to be on track
        #wait = max (0 , start_time - env.now)
        #yield env.timeout(wait)
        
        
        #try to acquire the resource related to the station
        #It may be possible that the station is all full and the train cannot be put there.
        #In that case, we have to wait to put train on the station
        resource = self.network.get_station_resource (start_station)
        request = resource.request()
        
        #put in the waiting list
        self.waiting = start_station
        yield request                            #wait for the station to be free
        #out of waiting list
        self.waiting = '-'
        self.resource = resource                 
        self.request = request
        
        #acuire the station
        self.current_track = self.network.lock_station (start_station , self.name)
        
        #update the current status
        self.current_index = 0 
        self.current = start_station
        self.station_or_not = True
        self.running = True
        
        #update the log
        self.log[self.current_index] = (start_station , env.now , -1)
        
        self.create_log("Time : {} -- Train {} initiated. On Track {}".format(env.now , self.name , start_station) )
        
        #wait for the halt time : depart_time - start_time
        wait = depart_time - start_time
        yield env.timeout(wait)

        #waiting on the track till the depart time, then only we can take the action for the train
        wait = max (0 , depart_time - env.now)
        yield env.timeout(wait)
              
    def move_train_one_step_simulate (self, env):
        '''
        Move the train
        This function does not move the train before the tentative time table
        If already reached destination then returns -1
        
        Note : If the resource is not free, then it will wait till the resource is free.
        '''
        #if the train is not running return -1
        if (self.running == False):
            return -1
        
        
        #If the train is on the station and ready to depart
        if (self.station_or_not):
             
            '''
            Since the train is on the station
                  - If already reached the final station then return -1
                  - if not, then leave the station track and try to acuire the next track in between the stations
                 
            Assumes when the train make this move: then already it is the right time, so no need to wait
            '''
            
            #if the train has completed the journey
            if (self.done):
                return -1

            
            current_station , start_time , depart_time = self.route[self.current_index]
            next_station , _ , _ = self.route[self.current_index + 1]
            current_time = env.now
            track = self.network.G[current_station][next_station]['details']
            self.create_log("Time : {} -- Train {} Try to depart to track {}-{}".format( env.now, self.name ,
                                                                              current_station , next_station) )
            
            #wait If reached the station before the depart time
            #wait = max(0 , depart_time - current_time)
            #yield env.timeout (wait)
            
            #now try to acquire the track in between the station
            resource = self.network.get_track_resource (current_station , next_station)
            request = resource.request()
            
            self.waiting = (current_station , next_station)
            yield request
            self.waiting = '-'
            
            prev_track = self.current_track
            self.current_track = self.network.lock_track(current_station , next_station , self.name)
            
            #release the current resource
            self.resource.release(self.request)
            self.network.free_station(current_station , prev_track)
            self.resource =  resource
            self.request = request
            
            self.create_log("Time : {} -- Train {} On track {}-{}".format( env.now , self.name , 
                                                                              current_station , next_station) )
            #update the log ; depart time
            self.log[self.current_index] = (self.log[self.current_index][0] , self.log[self.current_index][1] ,  env.now) 
        
            #update the current_status 
            self.current = (current_station , next_station) 
            self.station_or_not = False                       #on the track
            
            #travel down the track
            len_of_track = track.length_of_tracks[self.current_track]
            time_to_travel = self.compute_time(len_of_track)
            
            #Yielding of this event corresponds to number 2 in the list.
            yield env.timeout (time_to_travel)
            
            
            self.create_log("Time : {} -- Train {} Travelled on track {}-{}".format(env.now , self.name ,
                                                                              current_station , next_station) )
            
        else:
            '''
            Train has travelled down the track and waiting to arrive to the station
            '''
            #we are moving from station_x to station_y 
            station_x , station_y  = self.current
            self.create_log("Time : {} -- Train {} Try to arrive at station {}".format( env.now ,self.name , 
                                                                              station_y ) )
            #try to acquire the track on the next station
            resource = self.network.get_station_resource(station_y)
            request = resource.request()
            #put in wait list
            self.waiting = station_y
            #request for resource
            yield request
            #out of wait list
            self.waiting = '-'
            prev_track = self.current_track
            self.current_track = self.network.lock_station (station_y , self.name)
            
            #release the current resource
            self.resource.release(self.request)
            self.network.free_track (station_x , station_y , prev_track)
            self.resource = resource
            self.request = request
            
            self.create_log("Time : {} -- Train {} Arrived at station {}".format(env.now , self.name ,
                                                                              station_y ) )
            self.current = station_y
            self.station_or_not = True
            self.current_index += 1
            
            #arrival time
            self.log[self.current_index] = (self.log[self.current_index][0] , env.now ,  -1 ) 
            
            #if completed the journey
            if (self.current_index == len(self.route) - 1):
                self.create_log("Time : {} -- Train {} On last Station.".format(env.now ,self.name ) )
                self.done = True
                self.running = False
            
            #wait If reached the station before the depart time
            _ , start_time , depart_time = self.route[self.current_index]
            
            #wait for the halt time : depart_time - start_time
            wait = depart_time - start_time
            yield env.timeout(wait)
            
            #dont depart before time.
            wait = max(0 , depart_time - env.now)
            yield env.timeout (wait)
            
            #For now it is standing on the station
            #Instead of standing here wait for the time until it can reach depart from the station.
        return 0
                
    def finish_journey_simulate (self , env):
        '''
        This function is used when the train finishes it's journey.
        Note : Instead of releasing the resource immediately, wait for the departure time at the station
            and then free the resource
            
        Note : If the resource is not free, then it will wait till the resource is free.
        '''
        if (self.done == True):
            
            #Wait for the departure time at the station
            station , arrive_time , depart_time = self.route[self.current_index]
            wait_time = max(0 , depart_time - env.now)
            yield env.timeout(wait_time)
            
            #update the log : correct depart time
            self.log[self.current_index] = (self.log[self.current_index][0] , self.log[self.current_index][1] ,  env.now) 
            
            #release all the resource
            self.resource.release(self.request)
            self.network.free_station(self.route[-1][0] , self.current_track)
            
            #update the status of the train
            self.current = '_'                          
            self.current_index = -1                     #upto which point the route is travelled
            self.current_track = -1                     #current track number on the particular station or track  
            
            #not acquiring any resource
            self.resource = None
            self.request = None

            #logging 
            self.create_log("Time : {} -- Train :{} Completed Journey : Released all the resources ".format(env.now , self.name)) 
        
    def is_move_valid(self , env):
        '''
        Check if the 'move' step is valid for the train or not
        'move' step can be invalid if the resource train is trying to acquire is not free.
        
        If move is invalid : update the status of train to be waiting and return False
                           : return True (i.e. the move is valid) 
        
        '''
        
        #Train is not yet started
        if (self.done == False and self.running == False):
            '''
            Train is not yet started so get the start station and see if
            the resource is free on that station or not
            '''
            start_station ,_ , _ = self.route[0]

            #If the resource is free then return True
            if (self.network.is_station_resource_free (start_station)):
                self.create_log("Time -- {} : {} move Valid".format(env.now , self.name))
                return True
            #If the resource is not free return False
            else:
                self.waiting = start_station
                self.create_log("Time -- {} : {} move Invalid. Waiting for {}".format(env.now ,
                                                                 self.name , start_station))
                return False

        #Train is running
        elif (self.running == True):
            
            #Train is on the station, so extract the next track 
            #and see if the resource is free on that track.
            if (self.station_or_not):

                #if the train has completed the journey
                if (self.done):
                    return False

                current_station , _ , _ = self.route[self.current_index]
                next_station , _ , _ = self.route[self.current_index + 1]

                #If the resource is free return True
                if (self.network.is_track_resource_free (current_station , next_station)):
                    self.create_log("Time -- {} : {} move Valid".format(env.now , self.name))
                    return True

                #If resource is free
                else:
                    self.waiting = (current_station , next_station)
                    self.create_log("Time -- {} : {} move Invalid. Waiting for {} - {}".format(env.now 
                                                            , self.name , current_station , next_station))
                    return False
            #Train is on the track so get the next station and 
            #see if the resource is free on that station or not
            else:
                
                                
                station_x , station_y  = self.current

                #If the resource is free then return True
                if (self.network.is_station_resource_free (station_y)):
                    self.create_log("Time -- {} : {} move Valid".format(env.now , self.name))
                    return True
                #If the resource is not free return False
                else:
                    self.waiting = station_y
                    self.create_log("Time -- {} : {} move Invalid. Waiting for {}".format(env.now , 
                                                            self.name , station_y))
                    return False


        #train has completed the journey but the resource is not freed
        elif (self.done == True and self.resource is not None):
            #move is always valid. Since train is not going to wait for any resource
            #but free the last resource
            self.create_log("Time -- {} : {} move Valid".format(env.now , self.name))
            return True

        #Since the journey is complete no need of taking further action
        else:
            self.create_log('Time : {} -- {} Move Invalid. Journey is completed the journey'.format(env.now , self.name))
            return True
        
    def status (self):
        '''
        Returns the status of train.
        
        '''
        #Train is not yet started
        if (self.done == False and self.running == False):
            return "not_yet_started"

        #Train is running
        elif (self.running == True):
            return "running"
        
        #train has completed the journey but the resource is not freed
        elif (self.done == True and self.resource is not None):
            return "Completed_resource_not_freed"

        #train has completed the journey and freed all the resource.
        else:
            return "Completed"
        
    
    def print_details (self):
        '''
        Prints all the information of the train
        '''
        print(50 * '*')
        print("Train ID : {}".format(self.id_))
        print("Name :{}".format(self.name))
        print("Priority : {}".format(self.priority))
        print("Average speed : {}".format(self.speed))
        
        print("Route of the train")
        for d,t_a , t_d  in self.route:
            print("            {} : {} - {} ".format(d , t_a , t_d ))

        #print the waiting
        if not self.waiting == '-':
            if (type(self.waiting) == str):
                print("Waiting for {}".format(self.waiting))
            else:
                print("Waiting for {} - {}".format(self.waiting[0] , self.waiting[1]))
                
        #train not yet started
        if (self.running== False and self.done == False):
            print("Train not yet started")
        #Train is currently running
        elif (self.running):
            print("Train is running")
            if (self.station_or_not):
                print("Currently at station {}".format(self.current))
            else:
                print("Currently on track {}-{}".format(self.current[0] , self.current[1]))
        
        #train has reached final station but had not left the final station
        elif (self.done == True and self.resource is not None):
            print('Train reached the destination : about to leave the station')
            
        #train completed the journey
        else:
            print("Train has completed the journey")
            print ("______Printing log________")
            for d, t_a , t_d in self.log:
                print("            {} : {} {} ".format(d , t_a , t_d))
                
        print(50 * '*')
        
            