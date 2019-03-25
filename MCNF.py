from gurobipy import *
import csv
import math
import time
import pandas as pd
from openpyxl import load_workbook

class DataStorage:
    '''Class to store network data.'''
    pass


def arcReader(filename):
    '''Reads arc csv file and returns list of non-empty rows.'''

    rows = []
    with open (filename, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if any(row): # Handles Empty Lines from OS swap
                rows.append(row)
    return rows

def csvReader(filename):
    '''Reads csv data into a dictionary. '''

    csv_data = {}
    with open (filename, "r") as f:
        reader = csv.reader(f)
        next(reader) # Handles Table Headers
        for row in reader:
            if any(row): # Handles Empty Lines from OS swap
                if row[1].isnumeric():
                    csv_data[row[0]] = float(row[1])
                else:
                    csv_data[row[0]] = row[1]
    return csv_data

def excelReader(filename, sheet_name):
    '''Reads supporting data from master excel file into a dictionary'''

    excel_data = {}
    xl = pd.ExcelFile(filename)
    inventory_df = xl.parse(sheet_name)
    inventory_rows = inventory_df.values.tolist()
    if sheet_name == 'Commodities':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[row[0]] = row[1]
    if sheet_name == 'Storage Rooms':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[row[0]] = row[3]
    if sheet_name == 'Room Dictionary':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[str(row[0])] = row[1]
    return excel_data

def construct_network(arc_data, mcnf, statics):
    '''
    Formats data into Network Components

    varDict - (tail, head, commodity): Gurobi Variable
    lagrange_mults - (tail, head, commodity): Lagrange Multiplier
    nodeList - List of all nodes: [(Room_ID, Time_Echelon, Dummy), ...]
    commodityList - List of commodities: [com0, ...]

    '''

    varDict = {}

    lagrange_mults = {}
    nodeList = []
    commodityList = []

    for arc_type in arc_data:
        var_partition = {}
        arc_rows = arc_data[arc_type]
        for row in arc_rows[1:]: # Removes Header
            tail = (row[0], row[1], row[2]) # Origin Node
            head = (row[3], row[4], row[5]) # Destination Node
            commodity = row[6]              # Equipment Type
            lb = float(row[7])     # Lower Bound of Arc
            ub = float(row[8])     # Upper Bound of Arc
            cost = float(row[9])   # Cost/unit of Arc

            # Update nodeList:
            for node in [tail, head]:
                if node not in nodeList:
                    nodeList.append(node)
                    if node[0] != 's' and node[0] != 't':
                        room_name = statics.roomKey[node[0]]
                        if room_name[0] == 'S' and node[2] == 'b':
                            lagrange_mults[node] = 0

            # Update commodityList
            if commodity not in commodityList:
                commodityList.append(commodity)

            # Updates var_partition
            arc = (tail, head, commodity)
            var_partition[arc] = makeVar(mcnf.m, arc, lb, ub, cost)

        # Updates varDict
        varDict[arc_type] = var_partition

    mcnf.m.update()
    mcnf.unrelaxed_objective = mcnf.m.getObjective()
    mcnf.lagrange_mults = lagrange_mults

    mcnf.varDict = varDict
    mcnf.nodeList = nodeList
    mcnf.commodityList = commodityList

# Prints for debugging
    # for x in varDict:
    #     print(x.upper())
    #     for y in varDict[x]:
    #         print(varDict[x][y].VarName)
    # for x in nodeList:
    #     print(str(x))
    # for x in commodityList:
    #     print(str(x))

def makeVar(m, arc, lb, ub, cost):
    '''Creates Gurobi Variable and adds it to the model.'''

    tail, head, commodity = arc
    name = "(({}, {}, {}), ({}, {}, {}), {})".format(
        tail[0], tail[1], tail[2],
        head[0], head[1], head[2],
        commodity )
    return m.addVar(lb=lb, ub=ub, obj=cost, name=name)


def flow_constraints(mcnf):
    '''
    Creates Flow Balance Constraints for all nodes in
    network, and adds them to the model.
    '''

    # TODO: Clean and Document
    for commodity in mcnf.commodityList:
        for node in mcnf.nodeList:
            if (node[0] != "s") and (node[0] != "t"):
                inDict = {}
                outDict = {}
                if True: # TODO: Clean up the Search
                    for arc_type in mcnf.varDict:
                        for arc in mcnf.varDict[arc_type]:
                            if (arc[1] == node) and (arc[2] == commodity):
                                inDict[arc] = mcnf.varDict[arc_type][arc]
                            elif (arc[0] == node) and (arc[2] == commodity):
                                outDict[arc] = mcnf.varDict[arc_type][arc]
                    inDict = tupledict(inDict)
                    outDict = tupledict(outDict)
                    mcnf.m.addConstr(inDict.sum() == outDict.sum())


def cap_constr_mapper(mcnf, statics):
    '''
    Maps the storage room nodes to thier respective
    relaxed capacity constraints.
    Capacity Term mapping: node -> LinExpr(Ax-b)
    Keys: Only Storage Room 'b' nodes
    '''

    commodity_vols = statics.commodity_vols
    room_caps = statics.room_caps
    cap_constrs = {}
    for node in mcnf.nodeList: # TODO - EFFICIENCY: partition nodelist, storage and not, a vs b
        if node[0] != 's' and node[0] != 't': # TODO: Remove 's' node.
            room_name = statics.roomKey[node[0]]
            if room_name[0] == "S" and node[2] == "b":
                vol_node_i = LinExpr()
                for commodity in mcnf.commodityList:
                    for arc_type in mcnf.varDict:
                        for arc in mcnf.varDict[arc_type]:
                    # TODO - EFFICIENCY: Can cut by only looking
                    # at (a->b for that node for all coms)
                    # we want:
                    # {((room_ID, t, a), (room_ID, t, b), k) :
                    #            k is element of commodidtyList}
                    # potentially cutting the # of items to
                    # iterate through
                            if arc[1] == node and arc[2] == commodity:
                                vol_node_i.add(mcnf.varDict[arc_type][arc], commodity_vols[commodity])
                vol_node_i.add(-room_caps[node[0]])
                cap_constrs[node] = vol_node_i
    mcnf.cap_constrs = cap_constrs

# Prints for debugging
    # for x in cap_constrs:
    #     string = ''
    #     for i in range(cap_constrs[x].size()):
    #         if i > 0:
    #             string = string + ' + '
    #         string = string + str(cap_constrs[x].getCoeff(i)) + ' * ' + str(cap_constrs[x].getVar(i).VarName)
    #     if cap_constrs[x].getConstant() > 0:
    #         string = string + ' + ' + str(cap_constrs[x].getConstant())
    #     elif cap_constrs[x].getConstant() < 0:
    #         string = string + ' - ' + str(abs(cap_constrs[x].getConstant()))
    #     print(string)

    return cap_constrs


def penalty_term(mcnf):
    '''
    Creates the Lagrangian Penalty Term.
    uses the capacity term (Ax-b)
    and the lagrangian multiplier (muT)

    penalty_term  = muT*(Ax-b)
    '''

    penalty = LinExpr()
    for node in mcnf.cap_constrs:
        penalty.add(mcnf.cap_constrs[node], mcnf.lagrange_mults[node])
    return penalty


def update_objective(mcnf):
    '''
    Creates the linear expression object to use as the
    objective function for the current iteration of the
    subgradient ascent.

    objective = unrelaxed_objective + penatly_term
    '''

    objective = LinExpr()
    objective.add(mcnf.unrelaxed_objective)
    objective.add(penalty_term(mcnf))
    mcnf.m.setObjective(objective, GRB.MINIMIZE)
    return objective


def subgradient_ascent(mcnf, statics, iterations=10000):
    '''
    Solves optimization model using a subgradient ascent
    algorithm, by itteratively solving and updating a
    relaxed formulation of the model.
    '''
# TODO: Clean and Document
    start = time.time()
    update_objective(mcnf)
    mcnf.m.setParam('OutputFlag', 0)
    mcnf.m.optimize()

    counter = 1
    while counter < iterations:
        stepsize = math.sqrt(1/counter)
        opt_check_vector = []
        updated_lagrange_mults = {}
        for node in mcnf.lagrange_mults:
            steepest_ascent = mcnf.cap_constrs[node].getValue()
            updated_lagrange_mults[node] = max(mcnf.lagrange_mults[node] + stepsize * steepest_ascent, 0)
            opt_check_vector.append((updated_lagrange_mults[node] - mcnf.lagrange_mults[node])/counter)
        if norm(opt_check_vector) > 0 : # TODO: Check Logic
        # Prints for debugging
            # print('\n--------------------------------------')
            # print('Iteration #' + str(counter) + ': ' + str(norm(opt_check_vector)))
            # print('--------------------------------------\n')

            mcnf.lagrange_mults = updated_lagrange_mults
            update_objective(mcnf)
            mcnf.m.optimize()
            counter += 1
        else:
            break
# Prints for debugging
    # print('--------------------------------------\n')
    # print('Iteration #' + str(counter) + ': ' + str(norm(opt_check_vector)))
    # end = time.time()
    # print('Subgradient Time: ' + str(end - start))
    # mcnf.m.setParam('OutputFlag', 1)
    # mcnf.m.optimize()

# Sudo Code
    # while ((norm(vector) > 0) OR (counter < 1,000,000)):
    #   counter++
    #   m.optimize()
    #   for all node in cap_constrs:
    #       check (Ax - b)
    #           stepest_ascent = cap_constrs[node]  | [sum over k( v_k*x_ijk) - V_j  where j is the storage room node]
    #       update multiplier with stepsize = sqrt(1/counter)
    #           lagrandeDict[node] = max(lagrandeDict[node] + stepsize * stepest_ascent, 0)
    #           (is max(new_mu, 0) needed?)
    #   Update objective function

def norm(vector):
    '''Returns the Norm of the vector arguement.'''
    sum = 0
    for x in vector:
        sum += x**2
    return math.sqrt(sum)

def greedy_swap(mcnf):
    '''
    Enforces capacity constrants by swapping equipment
    allocations from storage rooms over capacity to rooms
    under capacity.
    '''
    print("\nGreedy Swap\n")
    for node in mcnf.lagrange_mults:
        axb = mcnf.cap_constrs[node].getValue()
        if axb < 0:
            print('Room '+ str(node[0]) + ' is under capacity by ' + str(axb) + ' units in time echelon ' + str(node[1]) +'.')
        elif axb > 0:
            print('Room '+ str(node[0]) + ' is over capacity by ' + str(axb) + ' units in time echelon ' + str(node[1]) +'.')
        else:
            print('Room '+ str(node[0]) + ' is at capacity in time echelon ' + str(node[1]) +'.')

# Sudo Code
#     pull all storage nodes in a single echelon
#     check Ax - b:
#         if Ax-b > 0, then over capacity
#         if Ax-b < 0, under capacity
#     minimize the added cost to the model
#         minimize the cost change on inflow + cost change for outflow.
#         shift both inflow and outflow of both rooms by Ax-b
#             ?? Assignment optimization model ??


def printSolution(mcnf):
    if mcnf.m.status == GRB.Status.OPTIMAL:
        print('\nObjective Value: %g' % mcnf.m.objVal)
        for var in mcnf.varDict['movement']:
            if mcnf.varDict['movement'][var].X > 0.0:
                # TODO: Convert Echelons to Time
                # TODO: Order by:
                #           - Time
                #           - Room
                #           - Commodity
                #
                # Schedule:
                # Time, origin, destination, commodity, quantity
                print("{:<60s}| {:>8.0f}".format(str(var), mcnf.varDict['movement'][var].X))
    else:
        print('No solution;', m.status)

# def outputCsv(mcnf):
#     g_vars = mcnf.movement_arcs
#     with open('movement_schedule.csv', mode='w') as schedule_file:
#         employee_writer = csv.writer(schedule_file, delimiter=',') # other params? , quotechar='"', quoting=csv.QUOTE_MINIMAL)
#         for var in g_vars:
#             schedule_writer.writerow()

def main(args):
    # statics is used to store inmutable data from the
    # system, including:
    #   - Room ID Mapping | roomKey
    #   - Stroage Room Capacity Dictionary | roomCapDict
    #   - Commodity Volume Dictionary | commodityVolDict
    #   - Equipment Initial Loaction
    #   - Dijkstra's Matrix
    #
    # Only used for reference.
    statics = DataStorage()
    #statics.roomKey = csvReader("RoomDictionary.csv")
    #statics.room_caps = csvReader("RoomCapacities.csv")
    #statics.commodity_vols = csvReader("CommodityVolumes.csv")
    statics.roomKey = excelReader("EquipmentInventory.xlsx", "Room Dictionary")
    statics.room_caps = excelReader("EquipmentInventory.xlsx", "Storage Rooms")
    statics.commodity_vols = excelReader("EquipmentInventory.xlsx", "Commodities")
    print(statics.room_caps)
    print(statics.commodity_vols)
    print(statics.roomKey)
    # for x in statics.commodity_vols:
    #     print(x +': '+ str(statics.commodity_vols[x]))


# Prints for Debugging
    # print("\nRoom Key")
    # for x in statics.roomKey:
    #     print(str(x) + ": " + str(statics.roomKey[x]))
    # print("\nRoom Caps")
    # for x in statics.room_caps:
    #     print(str(x) + ": " + str(statics.room_caps[x]))
    # print("\nCommodity Volumes")
    # for x in statics.commodity_vols:
    #     print(str(x) + ": " + str(statics.commodity_vols[x]))
    # print()

    # mcnf is used to store mutable data about the current
    # state fo the optimization model, including:
    #   - Gurobi Model | m
    #   - Unrelaxed MCNF Objective | unrelaxed_objective
    #   - Mapping of arcs to variables | varDict
    #   - Mapping of storage nodes to Lagrange multipliers | lagrange_mults
    #   - List of all nodes present in MCNF | nodeList
    #   - List of all commodities present in MCNF | commodityList
    #   - Mapping of storage nodes to thier Capacity Constraints | cap_constrs
    #
    # To be updated as the state of the model changes.
    arc_data = {}
    arc_data["utility"] = arcReader("UtilityArcs.csv")
    arc_data["movement"] = arcReader("MovementArcs.csv")
    arc_data["event_req"] = arcReader("EventRequirementArcs.csv")
    arc_data["storage_cap"] = arcReader("StorageCapacityArcs.csv")

    mcnf = DataStorage()
    mcnf.m = Model("m")
    construct_network(arc_data, mcnf, statics)

    flow_constraints(mcnf)
    cap_constr_mapper(mcnf, statics)

    # subgradient_ascent(mcnf, statics)
    subgradient_ascent(mcnf, statics, 100) # REDUCED ITERATION COUNT FOR TESTING
    greedy_swap(mcnf)
    # printSolution(mcnf)


if __name__ == '__main__':
    import sys
    main(sys.argv)