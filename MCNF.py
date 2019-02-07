

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
    return arcDict

def modeler(arcDict):
    m = Model("m")

    for arc in arcDict:
        lowerBound = float(arcDict[arc][0])
        upperBound = float(arcDict[arc][1])
        cost = float(arcDict[arc][2])
        name = ''.join((''.join(arc[0]), ''.join(arc[1]), arc[2]))
        m.addVar(lb=lowerBound, ub=upperBound, obj=cost, name=name)



def main(args):
    arcDict = csvReader("MCNFData.csv")
    print(arcDict)
    modeler(arcDict)



if __name__ == '__main__':
    import sys
    main(sys.argv)
