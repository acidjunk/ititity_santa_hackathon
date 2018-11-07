from __future__ import print_function
import csv
import structlog
from math import radians, cos, sin, asin, sqrt

from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
# import os.path


logger = structlog.get_logger()
logger.info("Started")

_roundLimit = 100

# Debug counters.
_distanceCounter = 0
_demandCounter = 0


# Setup the data model
# - Parse the CSV to locations.
def create_data_model():
    # Load in first 29 items of data set.
    _limit = 29
    _locations = [(90, 0), ]
    demands = [0, ]

    with open('gifts.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        counter = 0
        for row in reader:
            if counter < _limit:
                counter += 1
                _locations.append((float(row["Latitude"]), float(row["Longitude"])))
                demands.append(float(row["Weight"]))

    logger.info("locations", locations=_locations)
    logger.info("weights", weights=demands)
    logger.info("locations", locations=len(_locations))
    logger.info("weights", weights=len(demands))
    
    data = {}

    capacities = [500, ]
    
    data["locations"] = _locations
    data["num_locations"] = len(data["locations"])
    data["num_vehicles"] = 1
    data["depot"] = 0
    data["demands"] = demands
    data["vehicle_capacities"] = capacities

    logger.info("Created data model with {0} entries.".format(counter))
    return data


# Creates callback to return distance between all points of all locations.
def create_distance_callback(data):
    global _distanceCounter
    """"""
    _distances = {}

    # Only determine haver distances once and store in a file.
    # Else we have to calculate haversine each restart.
    # distance_file = 'distance.csv'
    # if os.path.isfile(distance_file):
    #     logger.info('[create_distance_callback] Found distance file .')
    #     with open(distance_file) as distance_csv_file:
    #         reader = csv.DictReader(distance_csv_file)
    #         for row in reader:
    #             from_node = row["from_node"]
    #             to_node = row["to_node"]
    #             _distances[from_node][to_node] = row["calculated_haversine"]
    #     logger.info('[create_distance_callback] Parsed distance file .')
    # else:
    #     logger.info('[create_distance_callback] No distance file, calculating haver sins.')
    #     with open(distance_file, 'w') as write_distance_csv_file:
    #         write_distance_csv_file.write('from_node, to_node, calculated_haversine\n')
    for from_node in range(data["num_locations"]):
        _distances[from_node] = {}
        for to_node in range(data["num_locations"]):
            if from_node == to_node:
                _distances[from_node][to_node] = 0
                # write_distance_csv_file.write('{0},{1},{2}\n'.format(from_node, to_node, 0))
            else:
                calculated_haversine = haversine(data["locations"][from_node][1],
                                    data["locations"][from_node][0],
                                    data["locations"][to_node][1],
                                    data["locations"][to_node][0])
                _distances[from_node][to_node] = calculated_haversine
                # write_distance_csv_file.write('{0},{1},{2}\n'.format(from_node, to_node, calculated_haversine))
    logger.info('[create_distance_callback] Haversins parsed ') # & stored for future runs

    # Returns calculated (stored) distance between the two nodes
    def distance_callback(from_node, to_node):
        outDist = _distances[from_node][to_node]
        # logger.info('[Inner] Distance_callback {0} -> {1}: {3}'.format(from_node, to_node, outDist))
        return outDist

    _distanceCounter += 1
    logger.info('[Outer] Distance callback called {0}'.format(_distanceCounter))
    return distance_callback


def create_demand_callback(data):
    global _demandCounter

    # Creates callback to get demands at each location
    def demand_callback(from_node, to_node):
        return data["demands"][from_node]
    
    _demandCounter += 1
    logger.info("Create demands callback called {0}".format(_demandCounter))
    return demand_callback


def add_capacity_constraints(routing, data, demand_callback):
    # Adds capacity constraint
    capacity = "Capacity"
    routing.AddDimensionWithVehicleCapacity(
        demand_callback,
        0,  # null capacity slack
        data["vehicle_capacities"],  # vehicle maximum capacities
        True,  # start cumul to zero
        capacity)
    logger.info('Add capacity constraints done.')


# Calculate the great circle distance between two points on the earth (specified in decimal degrees)
def haversine(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    out = c * r
    # logger.info('haversine {0},{1} {2},{3} distance {4}'.format(lon1, lat1, lon2, lat2, out))
    return out


# Print routes on console.
def print_solution(data, routing, assignment):
    total_dist = 0
    for vehicle_id in range(data["num_vehicles"]):
        logger.info('Print solution vehicle {0}'.format(vehicle_id))
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {0}:\n'.format(vehicle_id)
        route_dist = 0
        route_load = 0
        while not routing.IsEnd(index):
            logger.info('Route {0}'.format(index))
            node_index = routing.IndexToNode(index)
            next_node_index = routing.IndexToNode(assignment.Value(routing.NextVar(index)))
            route_dist += haversine(
                data["locations"][node_index][1],
                data["locations"][node_index][0],
                data["locations"][next_node_index][1],
                data["locations"][next_node_index][0]
            )
            logger.info('Route distance {0}'.format(route_dist))
            route_load += data["demands"][node_index]
            plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
            index = assignment.Value(routing.NextVar(index))
            # ############### Break after first full parse ##############
            #break
            # ############### Break after first ##############

        node_index = routing.IndexToNode(index)
        total_dist += route_dist
        plan_output += ' {0} Load({1})\n'.format(node_index, route_load)
        plan_output += 'Distance of the route: {0}m\n'.format(route_dist)
        plan_output += 'Load of the route: {0}\n'.format(route_load)
        logger.info(plan_output)
    logger.info('Total Distance of all routes: {0}m'.format(total_dist))


# Main function
def main():
    logger.info("Main Start")
    # Instantiate the data problem.
    data = create_data_model()
    logger.info("Data model loaded")
    # Create Routing Model
    routing = pywrapcp.RoutingModel(
        data["num_locations"],
        data["num_vehicles"],
        data["depot"])
    # Define weight of each edge
    distance_callback = create_distance_callback(data)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)
    # Add Capacity constraint
    demand_callback = create_demand_callback(data)
    add_capacity_constraints(routing, data, demand_callback)
    # Setting first solution heuristic (cheapest addition).
    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)
    logger.info('Done routing.SolveWithParameters')
    if assignment:
        print_solution(data, routing, assignment)
    logger.info("Main Done")

if __name__ == '__main__':
    main()
