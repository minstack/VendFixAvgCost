from GitHubApi import *
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
import tkinter.ttk as ttk
import getpass
import json

def submitIssue(inputs, root):
    label = inputs['label'].get()
    user = inputs['user'].get()
    email = inputs['email'].get()
    feedback = inputs['feedback'].get(1.0, END)

    creds = getData()

    issue = gitApi.createIssue(title=f"[{label}]{user}", body=f"{feedback}\n{email}", assignees=["minstack"], labels=[f"{label.lower()}"]).json()
    print(issue)
    if issue is not None:
        displayMessage(f"Thank you for your submission!\nThe {label} was submitted at\n{issue['html_url']}", root)

def getData():
    with open('data.json') as f:
        data = json.load(f)

    global gitApi

    print(f"{data['owner']}: {data['repo']} : {data['ghtoken']}")

    gitApi = GitHubApi(owner=data['owner'], repo=data['repo'], token=data['ghtoken'])

def displayMessage(message, root):
    messagebox.showinfo("Submitted!", message)

    root.destroy()

def setGitApi(api):
    global gitApi
    gitApi = api

def main():
    root = Tk()
    root.geometry("350x500")
    root.call('tk','scaling', 2.0)
    root.title("Submit Feedback")

    lbluser = Label(root, text="User")
    lblemail = Label(root, text="Email")
    lblfeedback = Label(root, text="Feedback")
    lbllabel = Label(root, text="Type")

    frame = Frame(root, height=100)

    txtuser = Entry(root, width=100)
    txtuser.insert(0, getpass.getuser())
    txtemail = Entry(root, width=100)
    txtfeedback = ScrolledText(root, width=100, height=10)
    #txtfeedback = ScrolledText(root, width=100, bd=1)
    strLabel = StringVar()
    cboLabel = ttk.Combobox(root, values=("Feedback", "Enhancement", "Question", "Bug"), textvariable=strLabel, state='readonly')
    cboLabel.current(0)

    lbluser.pack(fill=X)
    txtuser.pack(padx=5)
    lblemail.pack(fill=X)
    txtemail.pack(padx=5)
    lbllabel.pack(fill=X)
    cboLabel.pack(padx=5, fill=X)
    lblfeedback.pack(fill=X)
    txtfeedback.pack(padx=5)

    inputs = {
        'user' : txtuser,
        'email' : txtemail,
        'label' : cboLabel,
        'feedback' : txtfeedback
    }

    btnSubmit = Button(root, text="Submit", command=lambda : submitIssue(inputs, root))
    btnSubmit.pack(side=BOTTOM, pady=10)

    root.mainloop()
