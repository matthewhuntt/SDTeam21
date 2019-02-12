# SDTeam21

MCNF.py

This file houses the optimization model. It runs in Gurobi using the data in MCNFdata.csv.

MCNFdata.csv

This file holds the data for the optimization model.


In the case where multiple rooms are combined into one space for an event setting , we will record the equipmet requirements as requirements for the loswest numbered room.
Ex:
The following requirement:
 - 20 Meeting Room Chairs to B 212/213
will be recorded as:
 - 20 Meeting Room Chairs to B 212