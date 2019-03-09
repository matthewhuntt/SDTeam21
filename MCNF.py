from gurobipy import *
import csv

def arcDataReader(filename):
    # Reads in data
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)

    # Formats data into Network Components
    arcDict = {}    # (tail, head, commodity): (lb, ub, cost)
    lagrangeDict = {} # node: multiplier
    nodeList = []
    commodityList = []
    for row in rows[1:]: # Removes Header
        if len(row) > 0:
            tail = (row[0], row[1], row[2]) # Origin Node
            head = (row[3], row[4], row[5]) # Destination Node
            commodity = row[6]              # Equipment Type
            lb = row[7]     # Lower Bound of Arc
            ub= row[8]      # Upper Bound of Arc
            cost = row[9]   # Cost/unit of Arc

            # Update nodeList: (Room_ID, Time_Echelon, Dummy)
            for node in [tail, head]:
                if node not in nodeList:
                    nodeList.append(node)

                    # TODO: Cleaner way, & why set to 1?
                    if node[0][0] == "S":
                        lagrangeDict[node] = 1

            # Update commodityList
            if commodity not in commodityList:
                commodityList.append(commodity)

            # Updates arcDict
            arcDict[(tail, head, commodity)] = (lb, ub, cost)

    return arcDict, lagrangeDict, nodeList, commodityList


# TODO: Mix with Langrange Multiplier Dict/ Node list?
def roomKeyReader(filename):
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


# Pass in MCNF Object instead of all the individual dicts.
# Cleaner? See OO Principle: Encapsulation
def modeler(arcDict, lagrangeDict, nodeList, commodityList, roomKey, roomCapDict, commodityVolDict):
    m = Model("m")
    varDict = {}
    for arc in arcDict:
        lowerBound = float(arcDict[arc][0])
        upperBound = float(arcDict[arc][1])
        cost = float(arcDict[arc][2]) # Useles rn
        # TODO:
        # If we can figure out how to access the cost from
        # the variable, then it can be useful. Otherwise its
        # a waste.
        # It then follows that, since the costs come from
        # the Dijkstra Matrix, its redundant to have it in
        # the arcDict.
        # Is there a more concise way to create arcs?

        # TODO: Cleaner Way? Toss to a helper function to create var and document?
        name = "(({}, {}, {}), ({}, {}, {}), {})".format(arc[0][0], arc[0][1], arc[0][2], arc[1][0], arc[1][1], arc[1][2], arc[2])
        varDict[arc] = m.addVar(lb=lowerBound, ub=upperBound, obj=cost, name=name)

        # TODO:
        # Puropose of both Var and Arc Dicts?
        # We run through one two create the other, so why
        # not create varDict from the start?
        # If its just for ease of accesing data, we should
        # figure out how to do it with just varDict.

### LAGRANGE & OBJ
# MOVED TO arcDictReader
    # lagrangeDict = {}
    # for node in nodeList:
    #     if node[0][0] == "S":
    #         lagrangeDict[node] = 1
    # print(lagrangeDict)

    # Two parts: mcnfObj and penatly term.
    # to rewrite, add constant to output from penalty_term()
    # rewrite in quick helper funct. ***
    objective = LinExpr() #***

    # KEEP THIS as a constant for easy rewriting
    mcnfObj = LinExpr()
    for arc in arcDict.keys():
        mcnfObj.add(varDict[arc], arcDict[arc][2])

    # for i in range(objective.size()):
    #     print(objective.getVar(i), objective.getCoeff(i))

    ## create a mapping of node to vars to make (Ax-b) easier to calculate
    penalty = penalty_term(nodeList, commodityList, arcDict, varDict, commodityVolDict, lagrangeDict)

    objective.add(mcnfObj) #***
    objective.add(penalty) #***
### END LANGRANGE & OBJ

# TODO: Read through, document and reformat if needed.
    for commodity in commodityList:
        for node in nodeList:
            if node[0] != "s" and (node[0] != "t"):
                inDict = {}
                outDict = {}
                for arc in arcDict:
                    if (arc[1] == node) and (arc[2] == commodity):
                        inDict[arc] = varDict[arc]
                    elif (arc[0] == node) and (arc[2] == commodity):
                        outDict[arc] = varDict[arc]
                inDict = tupledict(inDict)
                outDict = tupledict(outDict)
                m.addConstr(inDict.sum() == outDict.sum())
                #print("\n\n", node, ":  \ninDict: \n", inDict, "\noutDict\n", outDict)

    varDict = tupledict(varDict) # TODO: Purpose?? not used again
    m.setObjective(objective, GRB.MINIMIZE)
    m.optimize()

    return m

def penalty_term(nodeList, commodityList, arcDict, varDict, commodityVolDict, lagrangeDict):
    '''
        Creates the Penatly Term for the Lagrangian Relaxation using
        the most recent lagrangian mulitpliers.

        Keyword Arguements:
        arg1 --
    '''
    penalty = LinExpr()
    for node in nodeList:
        if ((node[0][0]) == "S" and node[2] == "b"):
            vol_i = LinExpr()
            for commodity in commodityList:
                for arc in arcDict: # Can cut by only looking at (a->b for that node for all coms)
                    if arc[1] == node and arc[2] == commodity:
                        vol_i.add(varDict[arc], commodityVolDict[commodity])
            penalty.add(vol_i, lagrangeDict[node])
    return penalty

def subgradient_ascent(model, lagrangeDict):
    print("subgradient ascent")
    # counter = 0
    # while ((|| (multiplier_(counter) - muliplier_(counter - 1))/ counter - 1) || > 0) OR (counter < ? 1,000,000 ?)):
    #   counter++
    #   solve model
    #   for all Stroage Room nodes (j)
    #       check (Ax - b)
    #           stepest_ascent = sum over k( v_k*x_ijk) - V_j ; where j is the storage room node
    #       update multiplier with stepsize = sqrt(1/counter)
    #           multiplier_j = multiplier_j + stepsize * stepest_ascent
    # Update objective function

def greedy_swap(model):
    print("greedy swap")
    #  pull all storage nodes in a single echelon
    #  check Ax - b:
    #      if Ax-b > 0, then over capacity
    #      if Ax-b < 0, under capacity
    #  minimize the added cost to the model
    #      minimize the cost change on inflow + cost change for outflow.
    #      if we shift both inflow and outflow of both rooms by Ax-b issues shouldnt propogate
    #      Assignment optimization model?

# Print solution
    # if m.status == GRB.Status.OPTIMAL:
    #     solution = m.getAttr('varDict', )
    #     for h in commodities:
    #         print('\nOptimal flows for %s:' % h)
    #         for i,j in arcs:
    #             if solution[h,i,j] > 0:
    #                 print('%s -> %s: %g' % (i, j, solution[h,i,j]))
    #

def printSolution(m):
    if m.status == GRB.Status.OPTIMAL:
        print('\nObjective Value: %g' % m.objVal)
        for var in m.getVars():
            if var.X > 0.0:
                # TODO: remove dummy arcs
                print("{:<55s}| {:>8.0f}".format(var.VarName, var.X))
    else:
        print('No solution;', m.status)



def main(args):
    arcDict, lagrangeDict, nodeList, commodityList = arcDataReader("MCNFDataTest.csv")
    roomKey = roomKeyReader("roomDictionary.csv")
    #print(arcDict)
    #print("\n\n")
    #print(nodeList)
    #roomCapDict = {"S1": 100000, "S2": 100000, "S3": 100000, "S4": 100000, "S5": 100000, "S6": 100000, "S7": 100000, "S8": 100000, "S9": 100000, "S10": 100000}
    roomCapDict = {"1": 10000}
    commodityVolDict = {"1": 2, "2": 3}
    m = modeler(arcDict, lagrangeDict, nodeList, commodityList, roomKey, roomCapDict, commodityVolDict)
    printSolution(m)


if __name__ == '__main__':
    import sys
    main(sys.argv)