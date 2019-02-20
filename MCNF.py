

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

def modeler(arcDict, nodeList, commodityList, roomDict):
    m = Model("m")
    varDict = {}
    for arc in arcDict:
        lowerBound = float(arcDict[arc][0])
        upperBound = float(arcDict[arc][1])
        cost = float(arcDict[arc][2])
        name = "(({}, {}, {}), ({}, {}, {}), {})".format(arc[0][0], arc[0][1], arc[0][2], arc[1][0], arc[1][1], arc[1][2], arc[2])
        varDict[arc] = m.addVar(lb=lowerBound, ub=upperBound, obj=cost, name=name)

    lagrangeDict = {}
    for room in roomDict.values():
        if room[0] == "S":
            lagrangeDict[room] = 0

    # print(lagrangeDict)

    for commodity in commodityList:
        for node in nodeList:
            if node[0] != "s" and (node[0] != "t" and node[2] != "b"):
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
    m.setObjective(varDict.sum(), GRB.MINIMIZE)
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
            print (var, var.obj)
    else:
        print('No solution;', m.status)


def main(args):
    arcDict, nodeList, commodityList = arcDataReader("MCNFData.csv")
    roomDict = roomDictReader("RoomDictionary.csv")
    #print(arcDict)
    #print("\n\n")
    #print(nodeList)
    m = modeler(arcDict, nodeList, commodityList, roomDict)
    #printSolution(m)



if __name__ == '__main__':
    import sys
    main(sys.argv)





