
import csv
import re
import datetime

def setupDataReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    echelonDict = {}
    eventRoomList = []
    itemList = []
    for row in rows:
        if row[1] not in echelonDict.values():
            echelonDict[len(echelonDict) + 1] = row[1]
        if row[4] not in eventRoomList:
            eventRoomList.append(row[4])
        if row[5] not in itemList:
            itemList.append(row[5])
    for echelon in echelonDict:
        echelonDict[echelon] = datetimeReader(echelonDict[echelon])
    return (echelonDict, eventRoomList, itemList)

def costDataReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    costDict = {}
    for rowIndex in range (1, len(rows)):
        for columnIndex in range (1, len(rows)):
            costDict[(rows[rowIndex][0], rows[0][columnIndex])] = rows[rowIndex][columnIndex]
    return costDict


def datetimeReader(date):

    searchObject = re.search("(\d{1,2})\/(\d{1,2})\/(\d{1,2}) (\d{1,2}):(\d{2})", date)
    (month, day, year, hour, minute) = searchObject.groups()
    date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
    return date

def constructor(echelonDict, eventRoomList, itemList, costDict):
    storageRoomList = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]
    allRoomList = eventRoomList + storageRoomList
    roomDict = {}
    for i in range (len(allRoomList)):
        roomDict[i + 1] = allRoomList[i]
    arcDict = {}
    for item in itemList:
        for echelon in echelonDict:
            for roomI in roomDict:
                for roomJ in roomDict:
                    for ab in ["a", "b"]:
                        if ab == "a":
                            if roomI == roomJ:
                                arcDict[((roomI, echelon, "a"),(roomJ, echelon, "b"), item)] = (0, 0, 0)
                        if ab == "b":
                            arcDict[((roomI, echelon, "b"),(roomJ, echelon+ 1, "a"), item)] = (0, 0, costDict[(roomDict[roomI], roomDict[roomJ])])

    return arcDict, roomDict

def labeler(arcDict):
    return None

def main(args):
    (echelonDict, eventRoomList, itemList) = setupDataReader("SetupData.csv")
    costDict = costDataReader("CostData.csv")

    print("\n\n")

    #for room in eventRoomList:
    #    print(room)
    #print(echelonDict)
    arcDict, roomDict = constructor(echelonDict, eventRoomList, itemList, costDict)
    #print(eventRoomList)
    #print(itemList)
    print(arcDict)

if __name__ == '__main__':
    import sys
    main(sys.argv)

