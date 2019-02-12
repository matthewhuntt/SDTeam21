
import csv

def csvReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    echelonDict = {}
    for row in rows:
        if row[1] not in echelonDict.values():
            echelonDict[len(echelonDict) + 1] = row[1]
    return echelonDict

def constructor():
    return None

def main(args):
    print(csvReader("SetupData.csv"))

if __name__ == '__main__':
    import sys
    main(sys.argv)

