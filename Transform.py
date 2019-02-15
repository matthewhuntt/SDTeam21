
import csv
import re
import datetime

def csvReader(filename):
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

def datetimeReader(date):

    searchObject = re.search("(\d{1,2})\/(\d{1,2})\/(\d{1,2}) (\d{1,2}):(\d{2})", date)
    (month, day, year, hour, minute) = searchObject.groups()
    date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
    return date

def constructor(echelonDict, eventRoomList, itemList):
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
                            arcDict[((roomI, echelon, "b"),(roomJ, echelon+ 1, "a"), item)] = (0, 0, 0)

    return arcDict

def main(args):
    (echelonDict, eventRoomList, itemList) = csvReader("SetupData.csv")
    #print(echelonDict)
    arcDict = constructor(echelonDict, eventRoomList, itemList)
    #print(eventRoomList)
    #print(itemList)
    print(arcDict)

if __name__ == '__main__':
    import sys
    main(sys.argv)

