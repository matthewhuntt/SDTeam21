

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
        arcDict[(row[0], row[1], row[2])] = (row[3], row[4], row[5])
    return arcDict

def modeler(arcDict):
    m = Model("m")

    for arc in arcDict:
        lowerBound = arcDict[arc][0]
        upperBound = arcDict[arc][1]
        cost = arcDict[arc][2]
        m.addVar(lb=lowerBound, ub=upperBound, obj=cost, name=arc)

    for

def main(args):
    print(csvReader("MCNFData.csv"))
    modelr(arcDict)



if __name__ == '__main__':
    import sys
    main(sys.argv)
