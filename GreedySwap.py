import csv
import pandas as pd
from openpyxl import load_workbook

class DataStorage:
    '''Class to store network data.'''
    pass

def excelReader(filename, sheet_name):
    '''Reads supporting data from master excel file into a dictionary'''

    excel_data = {}
    xl = pd.ExcelFile(filename)
    inventory_df = xl.parse(sheet_name)
    inventory_rows = inventory_df.values.tolist()
    if sheet_name == 'Commodities':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[row[0]] = row[1]
    if sheet_name == 'Storage Rooms':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[row[0]] = row[3]
    if sheet_name == 'Room Dictionary':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[str(row[0])] = row[1]
    return excel_data

def costDataReader(filename):
    xl = pd.ExcelFile(filename)
    df = xl.parse("Cost Data", header=None)
    rows = df.values.tolist()
    cost_dict = {}
    for rowIndex in range (1, len(rows)):
        for columnIndex in range (1, len(rows)):
            cost_dict[(rows[rowIndex][0], rows[0][columnIndex])] = rows[rowIndex][columnIndex]
    return cost_dict

def csvReader(filename):
    dictionary = {}
    with open(filename) as f:
        reader = csv.reader(f, delimiter='|')
        if filename == "ModelOutput.csv":
            for row in reader:
                if any(row):
                    dictionary[((row[0], row[1], row[2]), (row[3], row[4], row[5]), row[6])] = float(row[7])
        if filename == "UnderCap.csv":
            for row in reader:
                if any(row):
                    dictionary[(row[0], row[1], "a")] = float(row[3])
        if filename == "OverCap.csv":
            for row in reader:
                if any(row):
                    dictionary[(row[0], row[1], "a")] = float(row[3])
    return dictionary

def greedy_swap(statics, movement_arcs_dict, under_cap, over_cap):
    print("greedy_swap")
    with open("log_file.txt","w") as f:
        cost_dict = statics.cost_dict
        # print(cost_dict)
        # print()
        priority_list = statics.priority_list
        sorted_over_node_list = sorted(over_cap, key=lambda k: k[1])
        for over_node in sorted_over_node_list:
            print("Now working on node " + str(over_node))
            incoming_dict = {}
            for incoming_arc in movement_arcs_dict.keys():
                if incoming_arc[1] == over_node:
                    if float(movement_arcs_dict[incoming_arc]) > 0:
                        if incoming_arc[2] in incoming_dict.keys():
                             incoming_dict[incoming_arc[2]].append(incoming_arc)
                        else:
                             incoming_dict[incoming_arc[2]] = [incoming_arc]
            for commodity in priority_list:
                print("Now moving " + commodity)
                insertion_cost_dict = {}
                if commodity in incoming_dict:
                    for incoming_arc in incoming_dict[commodity]:
                        for under_node in under_cap:
                            # cost to add red_arc to current under_node and remove blue arc to over_node
                            origin_node = incoming_arc[0]
                            cost = cost_dict[(origin_node[0], under_node[0])] - cost_dict[(origin_node[0], over_node[0])]
                            insertion_cost_dict[(origin_node, under_node, commodity)] = cost

                #below func gives [(key_with_lowest_value), (key_with_second_lowest_value), ...]
                sorted_insertion_list = sorted(insertion_cost_dict, key=lambda k: insertion_cost_dict[k])
                #if len(sorted_insertion_list) > 0:
                #    print(sorted_insertion_list)

                for red_arc in sorted_insertion_list:
                    origin_node = red_arc[0]
                    blue_arc = (origin_node, over_node, commodity)
                    if float(over_cap[over_node]) > 0 and float(movement_arcs_dict[blue_arc]) > 0:
                        print ("Amount to move: " + str(over_cap[over_node]))
                        print("Now trying " + str(red_arc))
                        under_node = red_arc[1]
                        #print(under_cap)
                        if under_node in under_cap:
                            a = abs(float(over_cap[over_node])) # Volume over capacity still to move from over_node
                            b = abs(float(under_cap[under_node])) # Spare capacity in under_node
                            c = abs(float(movement_arcs_dict[blue_arc])) # Volume available to move from origin_node
                            swap_count = min(a, b, c)
                            if swap_count > 0:
                                movement_arcs_dict[(origin_node, over_node, commodity)] -= swap_count
                                over_cap[over_node] -= swap_count
                                movement_arcs_dict[(origin_node, under_node, commodity)] += swap_count
                                under_cap[under_node] += swap_count
                                if under_cap[under_node] == 0:
                                    del under_cap[under_node]
                                # if movement_arcs_dict[(origin_node, (under_node[0], under_node[1], 'a'), commodity)] == 0:
                                #     del under_cap[under_node]
                if over_cap[over_node] == 0:
                    del over_cap[over_node]

        f.write("\nOUTPUT:\n")
        f.write("Remaining over nodes:\n")
        for over_node in  over_cap:
            f.write(": ".join([str(over_node), str(over_cap[over_node])])+ "\n")
        f.write("Remaining under nodes:\n")
        for under_node in  under_cap:
            f.write(": ".join([str(under_node), str(under_cap[under_node])])+ "\n")

def main(args):
    statics = DataStorage()
    statics.room_caps = excelReader("EquipmentInventory.xlsx", "Storage Rooms")
    statics.commodity_vols = excelReader("EquipmentInventory.xlsx", "Commodities")
    statics.cost_dict = costDataReader("EquipmentInventory.xlsx")
    statics.priority_list = ["8 X 30 TABLES", "6 X 30 TABLES", "8 X 18 TABLES", "6 X 18 TABLES", "66 RROUND TABLES", "HIGH BOYS", "30 COCKTAIL ROUNDS",
        "MEETING ROOM CHAIRS", "PODIUMS", "STAGE SKIRT DOLLIES", "TABLE SKIRT DOLLIES", "MEETING ROOM CHAIR DOLLIES",
        "66 ROUND TABLE DOLLIES", "FOLDING CHAIR DOLLIES (V STACK)", "FOLDING CHAIR DOLLIES (SQUARE STACK)", "HIGH BOY DOLLIES",
        "LONG TABLE DOLLIES", "SHORT TABLE DOLLIES", "STAND UP TABLE DOLLIES", "16RISERS 6 X 8", "24RISERS 6 X 8", "32RISERS 6 X 8", "(3) STEP UNIT WITH RAIL",
        "(3) STEP UNIT WITHOUT RAIL", "(2) STEP UNIT WITH RAIL", "(2) STEP UNIT WITHOUT RAIL","SETS OF STAGE STEPS", "16RISERS 6 X 8", "24RISERS 6 X 8", "30 STAND-UP ROUNDS"]

    movement_arcs_dict = csvReader('ModelOutput.csv')
    under_cap = csvReader('UnderCap.csv')
    over_cap = csvReader('OverCap.csv')
    greedy_swap(statics, movement_arcs_dict, under_cap, over_cap)
    print("\a")

if __name__ == '__main__':
    import sys
    main(sys.argv)