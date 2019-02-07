

from gurobipy import *
import csv

def csvReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    arcDict = {}
    for row in rows[1:]:
        arcDict[((row[0], row[1], row[2]),(row[3], row[4], row[5]), row[6])] = (row[7], row[8], row[9])
    nodeList = []
    for arc in arcDict.keys():
        fromNode = arc[0]
        toNode = arc[1]
        if fromNode not in nodeList:
            nodeList.append(fromNode)
        if toNode not in nodeList:
            nodeList.append(toNode)
    return arcDict, nodeList

def modeler(arcDict):
    m = Model("m")

    for arc in arcDict:
        lowerBound = float(arcDict[arc][0])
        upperBound = float(arcDict[arc][1])
        cost = float(arcDict[arc][2])
        name = ''.join((''.join(arc[0]), ''.join(arc[1]), arc[2]))
        m.addVar(lb=lowerBound, ub=upperBound, obj=cost, name=name)

#        m.optimize()

# Print solution
#        if m.status == GRB.Status.OPTIMAL:
#            solution = m.getAttr('x', flow)
#            for h in commodities:
#                print('\nOptimal flows for %s:' % h)
#                for i,j in arcs:
#                    if solution[h,i,j] > 0:
#                        print('%s -> %s: %g' % (i, j, solution[h,i,j]))


def main(args):
    arcDict, nodeList = csvReader("MCNFData.csv")
    print(arcDict)
    print("\n\n")
    print(nodeList)
    modeler(arcDict)



if __name__ == '__main__':
    import sys
    main(sys.argv)
