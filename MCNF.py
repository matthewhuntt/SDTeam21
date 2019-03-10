from gurobipy import *
import csv
# import MCNF_Model

def arcDataReader(filename, m):
    # Reads in data
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)

    # Formats data into Network Components
    varDict = {}    # (tail, head, commodity): Gurobi Variable
    lagrangeDict = {} # node: multiplier
    nodeList = []
    commodityList = []
    for row in rows[1:]: # Removes Header
        if len(row) > 0:
            tail = (row[0], row[1], row[2]) # Origin Node
            head = (row[3], row[4], row[5]) # Destination Node
            commodity = row[6]              # Equipment Type
            lb = float(row[7])     # Lower Bound of Arc
            ub = float(row[8])     # Upper Bound of Arc
            cost = float(row[9])   # Cost/unit of Arc

            # Update nodeList: (Room_ID, Time_Echelon, Dummy)
            for node in [tail, head]:
                if node not in nodeList:
                    nodeList.append(node)

                    # TODO:
                    #   - Cleaner way, separate types of arcs
                    #   - Why set to 1?
                    if node[0][0] == "S":
                        lagrangeDict[node] = 1

            # Update commodityList
            if commodity not in commodityList:
                commodityList.append(commodity)

            # Updates varDict
            arc = (tail, head, commodity)
            varDict[arc] = makeVar(m, arc, lb, ub, cost)

    m.update()
    return varDict, lagrangeDict, nodeList, commodityList


def roomKeyReader(filename):
# TODO: Mix with Langrange Multiplier Dict/ Node list?
# This is static data only used for reference.
# Shift to system_statics.py
    with open (filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)

    roomKey = {}
    # eventRooms = {}
    # storageRooms = {}
    for row in rows[1:]:
        if len(row) > 0:
            roomKey[row[0]] = row[1]
    return roomKey


def modeler(m, varDict, lagrangeDict, nodeList, commodityList, roomKey, roomCapDict, commodityVolDict):
    '''
    # Pass in MCNF Object instead of all the individual dicts.
    # Cleaner? See OO Principle: Encapsulation
    '''

### TO BE REMOVED
    ## MOVED TO ARCDATAREADER()
    # m = Model("m")
    # varDict = {}
    # for arc in arcDict:
        # lowerBound = float(arcDict[arc][0])
        # upperBound = float(arcDict[arc][1])
        # cost = float(arcDict[arc][2]) # Useles rn
        # TODO:
        # It then follows that, since the costs come from
        # the Dijkstra Matrix, its redundant to have it in
        # the arcDict. (unless we prioritize elevators/large
        # movements in evenings)

        # TODO: Cleaner Way? Toss to a helper function to create var and document?
        # name = "(({}, {}, {}), ({}, {}, {}), {})".format(arc[0][0], arc[0][1], arc[0][2], arc[1][0], arc[1][1], arc[1][2], arc[2])
        # varDict[arc] = m.addVar(lb=lowerBound, ub=upperBound, obj=cost, name=name)

        # TODO:
        # I've reworked it so we never use arcDict after this
        # ArcDict is only used to create varDict.
        # To improve efficiency, we can just create the varDict in arcDataReader.
    # m.update()
    ##
### End TO BE REMOVED

### LAGRANGE & OBJ: REFACTORED
    # FOR TESTING
    # for i in range(objective.size()):
    #     print(objective.getVar(i), objective.getCoeff(i))

    # EFFICIENCY
    # create a mapping of node to vars to make (Ax-b) easier to calculate
        # Create mapping in one helper

        # Update the penatly term using the mapping as a reference
### END LANGRANGE & OBJ


    capTermDict = capTermMapper(nodeList, commodityList, varDict, commodityVolDict, lagrangeDict)
    mcnfObj = create_mcnfObj(varDict)
    objective = update_objective(mcnfObj, capTermDict, lagrangeDict)

# TODO: Read through, document and reformat if needed.
    for commodity in commodityList:
        for node in nodeList:
            if node[0] != "s" and (node[0] != "t"): ## TODO: Remove S and T, they just force us to have another echelon
                inDict = {}
                outDict = {}
                for arc in varDict:
                    if (arc[1] == node) and (arc[2] == commodity):
                        inDict[arc] = varDict[arc]
                    elif (arc[0] == node) and (arc[2] == commodity):
                        outDict[arc] = varDict[arc]
                inDict = tupledict(inDict)
                outDict = tupledict(outDict)
                m.addConstr(inDict.sum() == outDict.sum())
                #print("\n\n", node, ":  \ninDict: \n", inDict, "\noutDict\n", outDict)

    m.setObjective(objective, GRB.MINIMIZE) # Move to SUBGRADIENT ASCENT with helpers
    m.optimize() # Move to SUBGRADIENT ASCENT

    ## TODO: Refactor so this ONLY creates the framework of the model
    ## subgradient_ascent() will solve, and then update the model and repeat

    return m

def makeVar(m, arc, lb, ub, cost):
    '''Creates Gurobi Variable and adds it to the model.'''
    tail, head, commodity = arc
    name = "(({}, {}, {}), ({}, {}, {}), {})".format(
        tail[0], tail[1], tail[2],
        head[0], head[1], head[2],
        commodity )
    return m.addVar(lb=lb, ub=ub, obj=cost, name=name)

def create_mcnfObj(varDict):
    ''' Creates cTx term of the objective.
    store in model object

    TODO:
    might be able to pull this from the original model, after vars are added
    would save us a trip though the varDict

    KEEP THIS as a constant (in mcnf object) for easy rewriting
    '''
    mcnfObj = LinExpr()
    for arc in varDict.keys():
        mcnfObj.add(varDict[arc], varDict[arc].Obj)
    return mcnfObj


def capTermMapper(nodeList, commodityList, varDict, commodityVolDict, lagrangeDict):
    '''
        Creates the Penatly Term for the Lagrangian Relaxation using
        the most recent lagrangian mulitpliers.

        Keyword Arguements:
        arg1 --
    '''
    # Capacity Term mapping;
    # node: LinExpr(Ax-b)
    capTermDict = {}

    for node in nodeList: # TODO - EFFICIENCY: partition nodelist, storage and not, a vs b
        if ((node[0][0]) == "S" and node[2] == "b"):
            vol_node_i = LinExpr()
            for commodity in commodityList:
                for arc in varDict: # TODO - EFFICIENCY: Can cut by only looking at (a->b for that node for all coms)
                    if arc[1] == node and arc[2] == commodity:
                        vol_node_i.add(varDict[arc], commodityVolDict[commodity])
            # vol_node_i.add() ## TODO: SUBTRACT ROOM CAPACITY
            capTermDict[node] = vol_node_i
    return capTermDict


def penalty_term(capTermDict, lagrangeDict):
    ''' Creates the Lagrangian Penalty Term.
    uses the capacity term (Ax-b)
    and the lagrangian multiplier (muT)

    penalty_term  = muT*(Ax-b)
    '''
    penalty = LinExpr()
    for node in capTermDict:
        penalty.add(capTermDict[node], lagrangeDict[node])
    return penalty

def update_objective(mcnfObj, capTermDict, lagrangeDict):
    '''
        Creates the linear expression object to use for the current iteration of the subgradient ascent

        Two parts: mcnfObj (constant) and penatly term.
        to rewrite, add constant and output from penalty_term() to new LinExpr and return
    '''
    objective = LinExpr()
    penalty = penalty_term(capTermDict, lagrangeDict)
    objective.add(mcnfObj)
    objective.add(penalty)
    return objective


def subgradient_ascent(m, capTermDict, lagrangeDict):
    print("subgradient ascent")
    # counter = 0
    # while ((|| (multiplier_(counter) - muliplier_(counter - 1))/ counter - 1) || > 0) OR (counter < ? 1,000,000 ?)):
    #   counter++
    #   m.optimize() | solve model
    #   for all node in capTermDict:
    #       check (Ax - b)
    #           stepest_ascent = capTermDict[node]  | [sum over k( v_k*x_ijk) - V_j  where j is the storage room node]
    #       update multiplier with stepsize = sqrt(1/counter)
    #           lagrandeDict[node] = max(lagrandeDict[node] + stepsize * stepest_ascent, 0)
    #   Update objective function


def greedy_swap(m, capTermDict):
    print("greedy swap")
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
                # TODO: Order by:
                #           - Time
                #           - Room
                #           - Commodity
                print("{:<55s}| {:>8.0f}".format(var.VarName, var.X))
    else:
        print('No solution;', m.status)



def main(args):
    # TODO: create Model object to pass in mutable model data
    # TODO: create system object to pass in inmutable data (dijksta, roomkey, roomCap, etc.)
    m = Model("m") # TODO: mcnf_object
    varDict, lagrangeDict, nodeList, commodityList = arcDataReader("MCNFDataTest.csv", m) # TODO: mcnf_object
    roomKey = roomKeyReader("roomDictionary.csv") # TODO: system_statics
    roomCapDict = {"1": 10000} # TODO: system_statics
    commodityVolDict = {"1": 2, "2": 3} # TODO: system_statics
    m = modeler(m, varDict, lagrangeDict, nodeList, commodityList, roomKey, roomCapDict, commodityVolDict)
    printSolution(m)


if __name__ == '__main__':
    import sys
    main(sys.argv)