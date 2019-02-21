# SDTeam21

MCNF.py

This file houses the optimization model. It runs in Gurobi using the data in MCNFdata.csv.


MCNFData.csv

This file holds the data for the optimization model.


MCNFDataTest.csv

This file is the current home of the output of Transform.py


Transform.py

This file manipulates the data in SetupData.csv and outputs a file in the same format as MCNFData.csv.


SetupData.csv

This holds a sample of the manually input setup data for testing pruposes.

In the case where multiple rooms are combined into one space for an event setting , we will record the equipmet requirements as requirements for the loswest numbered room.
Ex:
The following requirement:
 - 20 Meeting Room Chairs to B 212/213
will be recorded as:
 - 20 Meeting Room Chairs to B 212


CostData.csv:

A cost matrix giving the cost of moving from each room to every other room.


RoomDictionary.csv:

Because rooms are stored as numbers and not names, this file is output from Transform.py for record-keeping.


TO DO:

Implement sub-gradient ascent algorithm;
Implement greedy capacity algorithm;
Get real cost matrix;
Limit number of echelons considered;
Calculate real avereage item volumes;
Get real storage room capacities;
Convert from Gurobi to open-sourced platform?;

