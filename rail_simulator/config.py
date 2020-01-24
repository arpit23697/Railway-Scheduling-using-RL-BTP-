#For the Normal case
# STATIONS_FILENAME = 'Input_files/stations.txt'
# RAILWAY_FILENAME = 'Input_files/railway.txt'
# TRAINS_FILENAME = 'Input_files/trains.txt'


#For the deadlock case
STATIONS_FILENAME = 'Input_files/toy_stations3.txt'
RAILWAY_FILENAME = 'Input_files/toy_railway3.txt'
TRAINS_FILENAME = 'Input_files/toy_trains3.txt'

#GLOBAL VARIABLES
TOTAL_SIMULATION_TIME = 1000
CURRENT_SIMULATION_TIME = 0

#TRAINS NEEDING ACTION
TRAINS_NEEDING_ACTION = []                 #A list containing trains that need action at the given simulation time

#DEADLOCK 
DEADLOCK = True                          #Indicate wether the system is in deadlock or not

#ALL TRAINS_COMPLETED JOURNEY
TRAINS_COMPLETED_JOURNEY = False