import csv
from VendApi import *
from VendFixAvgCostGUI import *
from GitHubApi import *
import re
import threading
import queue
import tkinter
import CsvUtil
import traceback
import os
import time
import getpass

gui = None
api = None
retrieveFilepath = ""
THREAD_COUNT = 1

USER = getpass.getuser()

def startProcess(bulkDelGui):
    """
        The entry point to begin retrieving customers to delete and process the
        bulk delete task. Handles all the basic error checks and feedback to the
        user through the GUI status message/bar, before creating API class.
    """
    global gui
    gui = bulkDelGui

    gui.setStatus("")
    if not gui.entriesHaveValues():
        ## error
        gui.setStatus("Please have values for prefix, token and CSV.")
        gui.setReadyState()
        return

    if not gui.isChecklistReady():
        gui.setStatus("Please make sure checklist is completed.")
        gui.setReadyState()
        return

    pattern = re.compile("^.+[.]csv$", re.IGNORECASE)

    for file in gui.csvList:
        if pattern.match(file) is None:
            gui.setStatus("Please make sure the selected files are .csv file.")
            gui.setReadyState()
            return

    global api
    try:
        api = VendApi(gui.txtPrefix.get().strip(), gui.txtToken.get().strip())

        #Retrieval
        outlets = api.getOutlets()

        if not api.connectSuccessful(outlets):
            gui.setStatus("Please make sure prefix/token are correct (expiry).")
            gui.setReadyState()
            return

        prodsIdtofix = getCsvProdsToFix()

        if len(prodsIdtofix) == 0:
            gui.setStatus("Please make sure CSV has an 'id' column.")
            gui.setReadyState()
            return


        gui.setStatus("Retrieving products...")
        fullProdList = api.getProducts(endpointVersion='0.9')\

        prodIdtoProdObj = getProdIdtoObj(fullProdList)
        prodIdtoInventory = getProdIdToInventory(prodsIdtofix, prodIdtoProdObj)

        gui.setStatus("Zeroing out inventory...")
        #Zero out inventory
        zeroOutInventory(prodIdtoInventory, api)

        #Proccess Stock stockorders
        gui.setStatus("Creating stock orders...")
        consignments = createStockOrders(api, outlets)

        gui.setStatus("Receiving consignment products...")
        negativeProds = addConsignmentProducts(api, consignments, prodIdtoInventory)

        receiveConsignments(consignments)
        #Cleanup with original inventory <=0
        gui.setStatus("Restoring originally negative/0 inventory products...")
        cleanupNegativeInventory(api, negativeProds)

        gui.setStatus("Done.")
        gui.setReadyState()

    except Exception as e:
        #issue = GITAPI.createIssue(title=f"[{USER}]{str(e)}", body=traceback.format_exc(), assignees=['minstack'], labels=['bug']).json()
        issue = None
        if issue is not None and issue.get('html_url', None is not None):
            gui.showError(title="Crashed!", message=f"Something went terribly wrong.\nDev notified and assigned to issue:\n{issue['html_url']}")
        else:
            gui.showError(title="Crashed!", message=f"Something went terribly wrong.\nCould not notify dev.\n{traceback.format_exc()}")

def receiveConsignments(consignments):

    for c in consignments:

        api.updateConsignment(c)

def cleanupNegativeInventory(api, negprodsinv):

    #print(negprodsinv)

    for p in negprodsinv:

        #print(p)

        prodid = p['product_id']
        inv = p['inventory']

        response = api.updateProductInventory(prodid, [inv])

        #print(response.json())

def addConsignmentProducts(api, consignments, prodIdToInventory):

    negativeProds = []

    outletToConsignment = getOutletIdToConsignment(consignments)
    #pidtoOutletInventory = getProdIdToOutletInventory(prodIdToInventory)

    #this is quite ridiculous o(n^3) I don't think i've ever coded
    #need to use my brain more to figure this out
    for oid in outletToConsignment:

        for pid in prodIdToInventory:
            inventories = prodIdToInventory[pid]['inventory']
            supply_price = prodIdToInventory[pid]['cost']

            for i in inventories:
                if i['outlet_id'] == oid:
                    qty = float(i['count'])

                    if qty <= 0:
                        qty = 1
                        negativeProds.append(
                            {
                                "product_id" : pid,
                                "inventory" : i
                            }
                        )

                    consignmentId = outletToConsignment[oid]['id']

                    response = api.addConsignmentProductReceived(consignmentId, pid, qty, supply_price)
    return negativeProds

    for c in consignments:
        cid = c['id']
        coutletid = c['outlet_id']

        for pid in prodIdToInventory:
            qty = prodIdToInventory[pid][coutletid]

def getProdIdToOutletInventory(prodIdToInventory):

    pidtooutletinventory = {}

    for pid in prodIdToInventory:
        oinventory = prodIdToInventory[pid]

        for oi in oinventory:
            curroutid = oi['outlet_id']

            pidtooutletinventory[pid][curroutid] = oi


def getOutletIdToConsignment(consignments):

    idtoobj = {}

    for c in consignments:
        outletid = c['outlet_id']

        idtoobj[outletid] = c

    return idtoobj


def createStockOrders(api, outlets):

    stockOrders = []

    i = 0

    while i < len(outlets):
        o = outlets[i]

        cresponse = api.createStockOrder(outletid=o['id'], name=f"Fix Avg Cost - {o['name']}")
        status_code = cresponse.status_code

        if status_code == 429:
            time.sleep(300)
            continue

        if status_code == 200:
            rjson = cresponse.json()
            stockOrders.append(rjson)

        i += 1

    return stockOrders
    '''
    for o in outlets:
        cresponse = api.createStockOrder(o['id'], f"Fix Avg Cost - {o['name']}")

        if cresponse == 200:

        elif cresponse ==- 429:
            time.sleep(300)
            api.createStockOrder(o['id'], f"Fix Avg Cost - {o['name']}")
    '''

def zeroOutInventory(idToInv, api):

    for id in idToInv:
        outletInventories = idToInv[id]['inventory']
        #print(outletInventories)
        minOutletsPayload = []
        for outletInv in outletInventories:
            #print(outletInv)
            minOutletsPayload.append(
                {
                    "outlet_id" : outletInv['outlet_id'],
                    "count" : 0
                }
            )

        response = api.updateProductInventory(id, minOutletsPayload)
        #print(response.json())

def getProdIdToInventory(ids, idToObj):

    prodidtoinventory = {}

    for id in ids:
        prodidtoinventory[id] = {
            'inventory' : idToObj[id]['inventory'],
            'cost' : idToObj[id]['supply_price']
        }
        '''
        prodidtoinventory[id]['inventory'] = idToObj[id]['inventory']
        prodidtoinventory[id]['cost'] = idToObj[id]['supply_price']'''

    return prodidtoinventory

def getProdIdtoObj(fullProdList):

    prodIdToObj = {}

    for p in fullProdList:
        prodIdToObj[p['id']] = p

    return prodIdToObj

def getCsvProdsToFix():
    filenames = gui.csvList

    prodstofix = []
    for file in filenames:
        filepath = gui.getFilePath(file)

        if (filepath):
            prodstofix.extend(CsvUtil.getColumn(filepath, "id"))

    return prodstofix

def loadData():

    with open('data.json') as f:
        data = json.load(f)

    global GITAPI

    #print(f"{data['owner']}: {data['repo']} : {data['ghtoken']}")

    GITAPI = GitHubApi(owner=data['owner'], repo=data['repo'], token=data['ghtoken'])


loadData()

if __name__ == "__main__":
    gui = VendFixAvgCostGUI(maincallback=startProcess)
    gui.main()
