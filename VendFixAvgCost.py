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

        prodstofix = getCsvProdsToFix()

        if len(prodstofix) == 0:
            gui.setStatus("Please make sure CSV has an 'id' column.")
            gui.setReadyState()
            return

        fullProdList = api.getProducts(endpointVersion='0.9')\

        prodIdtoProdObj = getProdIdtoObj(fullProdList)
        prodIdtoInventory = getProdIdToInventory(fullProdList)



    except Exception as e:
        issue = GITAPI.createIssue(title=f"[{USER}]{str(e)}", body=traceback.format_exc(), assignees=['minstack'], labels=['bug']).json()
        issue = None
        if issue is not None and issue.get('html_url', None is not None):
            gui.showError(title="Crashed!", message=f"Something went terribly wrong.\nDev notified and assigned to issue:\n{issue['html_url']}")
        else:
            gui.showError(title="Crashed!", message=f"Something went terribly wrong.\nCould not notify dev.\n{traceback.format_exc()}")

def getProdIdToInventory(fullProdList):

    prodidtoinventory = {}

    for p in fullProdList:
        prodidtoinventory[p['id']] = p['inventory']

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
