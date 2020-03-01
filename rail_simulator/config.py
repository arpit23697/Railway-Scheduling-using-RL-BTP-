#For the deadlock case
STATIONS_FILENAME = '/home/arpit/study/BTP/rail_simulator/Input_files/HYP4/Stations.txt'
RAILWAY_FILENAME = '/home/arpit/study/BTP/rail_simulator/Input_files/HYP4/Railways.txt'
TRAINS_FILENAME = '/home/arpit/study/BTP/rail_simulator/Input_files/HYP4/Trains.txt'

#GLOBAL VARIABLES
TOTAL_SIMULATION_TIME = 100000
CURRENT_SIMULATION_TIME = 0

#TRAINS NEEDING ACTION
TRAINS_NEEDING_ACTION = []                 #A list containing trains that need action at the given simulation time

#DEADLOCK 
DEADLOCK = True                          #Indicate wether the system is in deadlock or not

#ALL TRAINS_COMPLETED JOURNEY
TRAINS_COMPLETED_JOURNEY = False