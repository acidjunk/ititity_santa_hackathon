from __future__ import print_function

import csv
import structlog
import helper

from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2


logger = structlog.get_logger()
logger.info("Started")



###########################
# Problem Data Definition #
###########################
def create_data_model():
    """Stores the data for the problem"""

    _limit = 100
    # _limit = 100000

    _locations = [(90, 0), ]
    demands = [0, ]

    with open('gifts.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        counter = 0
        for row in reader:
            if counter <= _limit:
                counter += 1
                _locations.append((float(row["Latitude"]), float(row["Longitude"])))
                demands.append(float(row["Weight"]))

    logger.debug("locations", locations=_locations)
    logger.debug("weights", weights=demands)
    logger.info("locations", locations=len(_locations))
    logger.info("weights", weights=len(demands))

    data = {}

    capacities = [500, ]

    # Multiply coordinates in block units by the dimensions of an average city block, 114m x 80m,
    # to get location coordinates.
    data["locations"] = _locations
    data["num_locations"] = len(data["locations"])
    data["num_vehicles"] = 1
    data["depot"] = 0
    data["demands"] = demands
    data["vehicle_capacities"] = capacities
    return data


#######################
# Problem Constraints #
#######################
def manhattan_distance(position_1, position_2):
    """Computes the Manhattan distance between two points"""
    return (
            abs(position_1[0] - position_2[0]) + abs(position_1[1] - position_2[1]))


def create_distance_callback(data):
    """Creates callback to return distance between points."""
    _distances = {}

    for from_node in range(data["num_locations"]):
        _distances[from_node] = {}
        for to_node in range(data["num_locations"]):
            if from_node == to_node:
                _distances[from_node][to_node] = 0
            else:
                _distances[from_node][to_node] = (
                    helper.haversine(data["locations"][from_node][0],
                                     data["locations"][from_node][1],
                                     data["locations"][to_node][0],
                                     data["locations"][to_node][1]))

    def distance_callback(from_node, to_node):
        """Returns the manhattan distance between the two nodes"""
        return _distances[from_node][to_node]

    return distance_callback


def create_demand_callback(data):
    """Creates callback to get demands at each location."""

    def demand_callback(from_node, to_node):
        return data["demands"][from_node]

    return demand_callback


def add_capacity_constraints(routing, data, demand_callback):
    """Adds capacity constraint"""
    capacity = "Capacity"
    routing.AddDimensionWithVehicleCapacity(
        demand_callback,
        0,  # null capacity slack
        data["vehicle_capacities"],  # vehicle maximum capacities
        True,  # start cumul to zero
        capacity)


###########
# Printer #
###########
def print_solution(data, routing, assignment):
    """Print routes on console."""
    total_dist = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {0}:\n'.format(vehicle_id)
        route_dist = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = routing.IndexToNode(index)
            next_node_index = routing.IndexToNode(assignment.Value(routing.NextVar(index)))
            route_dist += helper.haversine(
                data["locations"][node_index][0],
                data["locations"][node_index][1],
                data["locations"][next_node_index][0],
                data["locations"][next_node_index][1]
            )
            route_load += data["demands"][node_index]
            plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
            index = assignment.Value(routing.NextVar(index))

        node_index = routing.IndexToNode(index)
        total_dist += route_dist
        plan_output += ' {0} Load({1})\n'.format(node_index, route_load)
        plan_output += 'Distance of the route: {0}m\n'.format(route_dist)
        plan_output += 'Load of the route: {0}\n'.format(route_load)
        print(plan_output)
    print('Total Distance of all routes: {0}m'.format(total_dist))


########
# Main #
########
def main():
    """Entry point of the program"""
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
    if assignment:
        print_solution(data, routing, assignment)


if __name__ == '__main__':
    main()
