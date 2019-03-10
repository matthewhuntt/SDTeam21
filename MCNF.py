from gurobipy import *
import csv
import math

class DataStorage:
    ''' Class to store network data '''
    pass


def csvReader(filename):
    ''' Reads csv file and returns non-empty rows'''

    with open (filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            if len(row) > 0: # Handles Empty Lines from OS swap
                rows.append(row)
    return rows


def construct_network(arc_data, mcnf):
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

    for row in arc_data[1:]: # Removes Header
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
                # TODO:
                #   - Cleaner way,
                #       - use roomKey
                #       - separate types of arcs into diff csv?
                #   - Why set to 1?
                if node[0] not in ['s','t'] and int(node[0]) >= 27 and node[2] == 'b':
                    lagrange_mults[node] = 1

        # Update commodityList
        if commodity not in commodityList:
            commodityList.append(commodity)

        # Updates varDict
        arc = (tail, head, commodity)
        varDict[arc] = makeVar(mcnf.m, arc, lb, ub, cost)

    mcnf.m.update()
    mcnf.unrelaxed_objective = mcnf.m.getObjective()
    mcnf.varDict = varDict
    mcnf.lagrange_mults = lagrange_mults
    mcnf.nodeList = nodeList
    mcnf.commodityList = commodityList


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

    # TODO: Read through, document and reformat if needed.
    for commodity in mcnf.commodityList:
        for node in mcnf.nodeList:
            # TODO: Remove S and T,
            #   - they just force us to have another echelon
            #   - can pull initial locations from csv table
            if node[0] != "s" and (node[0] != "t"):
                inDict = {}
                outDict = {}
                for arc in mcnf.varDict:
                    if (arc[1] == node) and (arc[2] == commodity):
                        inDict[arc] = mcnf.varDict[arc]
                    elif (arc[0] == node) and (arc[2] == commodity):
                        outDict[arc] = mcnf.varDict[arc]
                inDict = tupledict(inDict)
                outDict = tupledict(outDict)
                mcnf.m.addConstr(inDict.sum() == outDict.sum())


def cap_constr_mapper(mcnf, statics):
    '''
    Maps the storage room nodes to thier respective
    relaxed capacity constraints.
    Capacity Term mapping: node -> LinExpr(Ax-b)
    '''

    commodity_vols = statics.commodity_vols
    room_caps = statics.room_caps
    cap_constrs = {}
    for node in mcnf.nodeList: # TODO - EFFICIENCY: partition nodelist, storage and not, a vs b
        if ((node[0][0]) == "S" and node[2] == "b"): # TODO: Use RoomKey!
            vol_node_i = LinExpr()
            for commodity in mcnf.commodityList:
                for arc in mcnf.varDict: # TODO - EFFICIENCY: Can cut by only looking at (a->b for that node for all coms)
                    if arc[1] == node and arc[2] == commodity:
                        vol_node_i.add(mcnf.varDict[arc], commodity_vols[commodity])
            # vol_node_i.add(-room_caps[node]) ## TODO: SUBTRACT ROOM CAPACITY
            cap_constrs[node] = vol_node_i
    mcnf.cap_constrs = cap_constrs
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


def subgradient_ascent(mcnf):
    update_objective(mcnf)
    mcnf.m.optimize()
    # counter = 1.0 ## TODO: not sure what to initiallize this as.
    # stepsize = math.sqrt(1/counter)
    # vector = []
    # print("===============================================")
    # for node in mcnf.lagrange_mults:
    #     steepest_ascent = mcnf.cap_constrs[node].getValue()
    #     print(steepest_ascent)
    #     updated_lagrange_mults[node] = max(lagrange_mults[node] + stepsize * steepest_ascent, 0)
    #     vector.append((updated_lagrange_mults[node] - lagrange_mults[node])/counter) # TODO: not sure if this is the correct function
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
    sum = 0
    for x in vector:
        sum += x**2
    return math.sqrt(sum)

def greedy_swap(mcnf):
    print("\nGreedy Swap\n")
    #  pull all storage nodes in a single echelon
    #  check Ax - b:
    #      if Ax-b > 0, then over capacity
    #      if Ax-b < 0, under capacity
    #  minimize the added cost to the model
    #      minimize the cost change on inflow + cost change for outflow.
    #      if we shift both inflow and outflow of both rooms by Ax-b issues shouldnt propogate
    #      Assignment optimization model?


def printSolution(m):
    if m.status == GRB.Status.OPTIMAL:
        print('\nObjective Value: %g' % m.objVal)
        for var in m.getVars():
            if var.X > 0.0:
                # TODO: remove dummy arcs
                # TODO: Convert Echelons to Time
                # TODO: Order by:
                #           - Time
                #           - Room
                #           - Commodity
                #
                # Schedule:
                # Time, origin, destination, commodity, quantity
                print("{:<55s}| {:>8.0f}".format(var.VarName, var.X))
    else:
        print('No solution;', m.status)


def main(args):
    mcnf = DataStorage()
    mcnf.m = Model("m")
    arc_data = csvReader("MCNFDataTest.csv")
    construct_network(arc_data, mcnf)

    statics = DataStorage()
    # Commodity Volume Dictionary | commodityVolDict
    # Stroage Room Capacity Dictionary | roomCapDict
    # Room ID Mapping | roomKey
    # Equipment Initial Loaction
    # Dijkstra's Matrix

    # TODO: What is the purpose for this?
    # statics.roomKey = roomKeyReader("roomDictionary.csv")
    statics.room_caps = {"1": 10000}
    statics.commodity_vols = {"1": 2, "2": 3}

    flow_constraints(mcnf)
    cap_constr_mapper(mcnf, statics)

    subgradient_ascent(mcnf)
    greedy_swap(mcnf)
    printSolution(mcnf.m)


if __name__ == '__main__':
    import sys
    main(sys.argv)

################################################
# def roomKeyReader(filename):
# # TODO: REIMPLEMENT
# #   - This is static data only used for reference.
# #   - Shift to system_statics.py
#     rows = csvReader(filename)
#     roomKey = {}
#     for row in rows[1:]:
#         if len(row) > 0:
#             roomKey[row[0]] = row[1]
#     return roomKey

################################################
# unrelaxed_objective taken after all vars added in
#   construct_network()
#
# def unrelaxed_mcnf_objective(mcnf):
#     ''' Creates cTx term of the objective.
#     store in model object
#
#     TODO:
#     might be able to pull this from the original model,
#     after vars are added would save us a trip though the
#     varDict
#
#     KEEP THIS as a constant (in mcnf object) for easy
#     rewriting
#     '''
#     mcnfObj = LinExpr()
#     varDict = mcnf.varDict
#     for arc in varDict.keys():
#         mcnfObj.add(varDict[arc], varDict[arc].Obj)
#     mcnf.mcnfObj = mcnfObj
