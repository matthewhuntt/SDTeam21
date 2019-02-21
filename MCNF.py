

from gurobipy import *
import csv

def arcDataReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    arcDict = {}
    for row in rows[1:]:
        if len(row) > 0:
            arcDict[((row[0], row[1], row[2]),(row[3], row[4], row[5]), row[6])] = (row[7], row[8], row[9])
    nodeList = []
    commodityList = []
    for arc in arcDict.keys():
        fromNode = arc[0]
        toNode = arc[1]
        commodity = arc[2]
        if fromNode not in nodeList:
            nodeList.append(fromNode)
        if toNode not in nodeList:
            nodeList.append(toNode)
        if commodity not in commodityList:
            commodityList.append(commodity)
    return arcDict, nodeList, commodityList

def roomDictReader(filename):
    with open (filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    roomDict = {}
    for row in rows[1:]:
        if len(row) > 0:
            roomDict[row[0]] = row[1]
    return roomDict

def modeler(arcDict, nodeList, commodityList, roomDict, roomCapDict, commodityVolDict):
    m = Model("m")
    varDict = {}
    for arc in arcDict:
        lowerBound = float(arcDict[arc][0])
        upperBound = float(arcDict[arc][1])
        cost = float(arcDict[arc][2])
        name = "(({}, {}, {}), ({}, {}, {}), {})".format(arc[0][0], arc[0][1], arc[0][2], arc[1][0], arc[1][1], arc[1][2], arc[2])
        varDict[arc] = m.addVar(lb=lowerBound, ub=upperBound, obj=cost, name=name)

    lagrangeDict = {}
    for node in nodeList:
        if node[0][0] == "S":
            lagrangeDict[node] = 1
    # print(lagrangeDict)

    objective = LinExpr()
    for arc in arcDict.keys():
        # print(varDict[arc], arcDict[arc][2])
        objective.add(varDict[arc], arcDict[arc][2])

    # for i in range(objective.size()):
    #     print(objective.getVar(i), objective.getCoeff(i))

    p = LinExpr()
    for node in nodeList:
        if ((node[0][0]) == "S" and node[2] == "b"):
            vol_i = LinExpr()
            for commodity in commodityList:
                for arc in arcDict: # Can cut by only looking at (a->b for that node for all coms)
                    if arc[1] == node and arc[2] == commodity:
                        vol_i.add(varDict[arc], commodityVolDict[commodity])
            p.add(vol_i, lagrangeDict[node])
    objective.add(p)



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
    varDict = tupledict(varDict)
    # m.setObjective(varDict.sum(), GRB.MINIMIZE)
    m.setObjective(objective, GRB.MINIMIZE)
    m.optimize()

    return m

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
                print("{:<55s}| {:>8.0f}".format(var.VarName, var.X))
    else:
        print('No solution;', m.status)


def main(args):
    arcDict, nodeList, commodityList = arcDataReader("MCNFDataTest.csv")
    roomDict = roomDictReader("RoomDictionary.csv")
    #print(arcDict)
    #print("\n\n")
    #print(nodeList)
    #roomCapDict = {"S1": 100000, "S2": 100000, "S3": 100000, "S4": 100000, "S5": 100000, "S6": 100000, "S7": 100000, "S8": 100000, "S9": 100000, "S10": 100000}
    roomCapDict = {"1": 10000}
    commodityVolDict = {"1": 2, "2": 3}
    m = modeler(arcDict, nodeList, commodityList, roomDict, roomCapDict, commodityVolDict)
    printSolution(m)



if __name__ == '__main__':
    import sys
    main(sys.argv)





