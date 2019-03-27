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

def csvReader(filename):
    dictionary = {}
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dictionary[row[0]] = row[1]
    return dictionary

def greedy_swap(statics, movement_arcs_dict):
    cost_dict = statics.cost_dict
    priority_list = statics.priority_list
    over_cap = {} # key = string name of room node | value = current deviation from capacity
    under_cap = {} # key = string name of room node | value = current deviation from capacity
    for node in mcnf.lagrange_mults:
        axb = mcnf.cap_constrs[node].getValue()
        if axb < 0:
            under_cap[node] = axb
        elif axb > 0:
            over_cap[node] = axb

    sorted_over_node_list = sorted(over_cap, key=lambda k: k[1])
    print(sorted_over_node_list)
    for over_node in sorted_over_node_list:
        print("Now working on node " + str(over_node))
        incoming_dict = {}
        for incoming_arc in movement_arcs_dict.keys():
            if incoming_arc[1] == (over_node[0], over_node[1], 'a'):
                if movement_arcs_dict[incoming_arc] > 0:
                    if incoming_arc[2] in incoming_dict.keys():
                         incoming_dict[incoming_arc[2]].append(incoming_arc)
                    else:
                         incoming_dict[incoming_arc[2]] = [incoming_arc]
        for commodity in priority_list:
            print("Now moving " + commodity)
            insertion_cost_dict = {}
            if commodity in incoming_dict.keys():
                for incoming_arc in commodity:
                    for under_node in under_cap.keys():
                        cost = cost_dict[(incoming_arc[0], under_node)] - cost_dict[(incoming_arc[0], over_node)]
                        insertion_cost_dict[(incoming_arc[0], under_node, commodity)] = cost
            #below func gives [(key_with_lowest_value), (key_with_second_lowest_value), ...]
            sorted_insertion_list = sorted(insertion_cost_dict, key=lambda k: insertion_cost_dict[k])
            print(sorted_insertion_list)
            print ("Amount to move: " + str(over_cap[over_node]))
            for red_arc in sorted_insertion_list:
                if over_cap[over_node] > 0:
                    print("Now trying " + str(red_arc))
                    blue_arc = (red_arc[0], (over_node[0], over_node[1], 'a'), commodity)
                    under_node = (red_arc[1][0], red_arc[1][1], 'b')
                    swap_count = min(movement_arcs_dict[blue_arc], over_cap[over_node], under_cap[under_node])
                    movement_arcs_dict[over_node] -= swap_count
                    movement_arcs_dict[under_node] += swap_count
                    if movement_arcs_dict[under_node] == 0:
                        del under_cap[under_node]
            if over_cap[over_node] == 0:
                del over_cap[over_node]

def main(args):
    statics = DataStorage()
    statics.roomKey = excelReader("EquipmentInventory.xlsx", "Room Dictionary")
    statics.room_caps = excelReader("EquipmentInventory.xlsx", "Storage Rooms")
    statics.commodity_vols = excelReader("EquipmentInventory.xlsx", "Commodities")

    movement_arcs_dict = csvReader('modelOutput.csv')
    greedy_swap(statics, movement_arcs_dict)

if __name__ == '__main__':
    import sys
    main(sys.argv)