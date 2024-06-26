from tkinter import *
from tkinter.ttk import *
import socket
import _thread  # Updated to use '_thread' for threading in Python 3

class ChatClient(Frame):
  
    def __init__(self, root):
        super().__init__(root)  # Updated for Python 3
        self.root = root
        self.initUI()
        self.serverSoc = None
        self.serverStatus = 0
        self.buffsize = 1024
        self.allClients = {}
        self.counter = 0
  
    def initUI(self):
        self.root.title("Simple P2P Chat Client")
        ScreenSizeX = self.root.winfo_screenwidth()
        ScreenSizeY = self.root.winfo_screenheight()
        self.FrameSizeX  = 800
        self.FrameSizeY  = 600
        FramePosX   = (ScreenSizeX - self.FrameSizeX) // 2
        FramePosY   = (ScreenSizeY - self.FrameSizeY) // 2
        self.root.geometry("%sx%s+%s+%s" % (self.FrameSizeX, self.FrameSizeY, FramePosX, FramePosY))
        self.root.resizable(width=False, height=False)
        
        padX = 10
        padY = 10
        parentFrame = Frame(self.root)
        parentFrame.grid(padx=padX, pady=padY, stick=E+W+N+S)
        
        ipGroup = Frame(parentFrame)
        serverLabel = Label(ipGroup, text="Set: ")
        self.nameVar = StringVar()
        self.nameVar.set("SDH")
        nameField = Entry(ipGroup, width=10, textvariable=self.nameVar)
        self.serverIPVar = StringVar()
        self.serverIPVar.set("127.0.0.1")
        serverIPField = Entry(ipGroup, width=15, textvariable=self.serverIPVar)
        self.serverPortVar = StringVar()
        self.serverPortVar.set("8090")
        serverPortField = Entry(ipGroup, width=5, textvariable=self.serverPortVar)
        serverSetButton = Button(ipGroup, text="Set", width=10, command=self.handleSetServer)
        addClientLabel = Label(ipGroup, text="Add friend: ")
        self.clientIPVar = StringVar()
        self.clientIPVar.set("127.0.0.1")
        clientIPField = Entry(ipGroup, width=15, textvariable=self.clientIPVar)
        self.clientPortVar = StringVar()
        self.clientPortVar.set("8091")
        clientPortField = Entry(ipGroup, width=5, textvariable=self.clientPortVar)
        clientSetButton = Button(ipGroup, text="Add", width=10, command=self.handleAddClient)
        serverLabel.grid(row=0, column=0)
        nameField.grid(row=0, column=1)
        serverIPField.grid(row=0, column=2)
        serverPortField.grid(row=0, column=3)
        serverSetButton.grid(row=0, column=4, padx=5)
        addClientLabel.grid(row=0, column=5)
        clientIPField.grid(row=0, column=6)
        clientPortField.grid(row=0, column=7)
        clientSetButton.grid(row=0, column=8, padx=5)
        
        readChatGroup = Frame(parentFrame)
        self.receivedChats = Text(readChatGroup, bg="white", width=60, height=30, state=DISABLED)
        self.friends = Listbox(readChatGroup, bg="white", width=30, height=30)
        self.receivedChats.grid(row=0, column=0, sticky=W+N+S, padx=(0,10))
        self.friends.grid(row=0, column=1, sticky=E+N+S)

        writeChatGroup = Frame(parentFrame)
        self.chatVar = StringVar()
        self.chatField = Entry(writeChatGroup, width=80, textvariable=self.chatVar)
        sendChatButton = Button(writeChatGroup, text="Send", width=10, command=self.handleSendChat)
        self.chatField.grid(row=0, column=0, sticky=W)
        sendChatButton.grid(row=0, column=1, padx=5)

        self.statusLabel = Label(parentFrame)

        bottomLabel = Label(parentFrame, text="Created by Siddhartha under Prof. A. Prakash [Computer Networks, Dept. of CSE, BIT Mesra]")
        
        ipGroup.grid(row=0, column=0)
        readChatGroup.grid(row=1, column=0)
        writeChatGroup.grid(row=2, column=0, pady=10)
        self.statusLabel.grid(row=3, column=0)
        bottomLabel.grid(row=4, column=0, pady=10)
    
    def handleSetServer(self):
        if self.serverSoc is not None:
            self.serverSoc.close()
            self.serverSoc = None
            self.serverStatus = 0
        serveraddr = (self.serverIPVar.get().strip(), int(self.serverPortVar.get().strip()))
        try:
            self.serverSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverSoc.bind(serveraddr)
            self.serverSoc.listen(5)
            self.setStatus("Server listening on %s:%s" % serveraddr)
            _thread.start_new_thread(self.listenClients, ())
            self.serverStatus = 1
            self.name = self.nameVar.get().strip()
            if self.name == '':
                self.name = "%s:%s" % serveraddr
        except Exception as e:
            self.setStatus("Error setting up server: " + str(e))
    
    def listenClients(self):
    

        while True:
            clientsoc, clientaddr = self.serverSoc.accept()
            self.setStatus("Client connected from %s:%s" % clientaddr)
            self.addClient(clientsoc, clientaddr)
            _thread.start_new_thread(self.handleClientMessages, (clientsoc, clientaddr))
    
    def handleClientMessages(self, clientsoc, clientaddr):
        while True:
            try:
                data = clientsoc.recv(self.buffsize)
                if not data:
                    break
                self.addChat("%s:%s" % clientaddr, data.decode('utf-8'))
            except:
                break
        self.removeClient(clientsoc, clientaddr)
        clientsoc.close()
        self.setStatus("Client disconnected from %s:%s" % clientaddr)
    
    def handleAddClient(self):
        if self.serverStatus == 0:
            self.setStatus("Set server address first")
            return
        clientaddr = (self.clientIPVar.get().strip(), int(self.clientPortVar.get().strip()))
        try:
            clientsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientsoc.connect(clientaddr)
            self.setStatus("Connected to friend %s:%s" % clientaddr)
            self.addClient(clientsoc, clientaddr)
            _thread.start_new_thread(self.handleClientMessages, (clientsoc, clientaddr))
        except Exception as e:
            self.setStatus("Error connecting to friend: " + str(e))
    
    def handleSendChat(self):
        msg = self.chatVar.get().strip()
        if msg == '':
            return
        self.addChat("me", msg)
        for client in self.allClients.keys():
            self.allClients[client].send(msg.encode('utf-8'))
        self.chatVar.set('')
    
    def addChat(self, client, msg):
        self.receivedChats.config(state=NORMAL)
        self.receivedChats.insert(END, client + ": " + msg + "\n")
        self.receivedChats.config(state=DISABLED)
    
    def addClient(self, clientsoc, clientaddr):
        self.allClients[clientaddr] = clientsoc
        self.friends.insert(END, "%s:%s" % clientaddr)
        self.counter += 1
    
    def removeClient(self, clientsoc, clientaddr):
        print("Client %s disconnected" % str(clientaddr))
        del self.allClients[clientaddr]
        self.friends.delete(0, END)
        for clientaddr in self.allClients.keys():
            self.friends.insert(END, "%s:%s" % clientaddr)
    
    def setStatus(self, msg):
        self.statusLabel.config(text=msg)
        print(msg)


def handleClientMessages(self, clientsoc, clientaddr):
    while True:
        try:
            data = clientsoc.recv(self.buffsize)
            if not data:
                break
            # Display messages received from other clients
            self.addChat("%s:%s" % clientaddr, data.decode('utf-8'))
        except:
            break
    self.removeClient(clientsoc, clientaddr)
    clientsoc.close()
    self.setStatus("Client disconnected from %s:%s" % clientaddr)

def addChat(self, sender, msg):
    self.receivedChats.config(state=NORMAL)
    # Display messages received from friends
    if sender != self.name:  # Check if sender is not the local client
        self.receivedChats.insert(END, sender + ": " + msg + "\n")
    else:  # If sender is the local client, display message without sender's name
        self.receivedChats.insert(END, msg + "\n")
    self.receivedChats.config(state=DISABLED)



def main():  
    root = Tk()
    app = ChatClient(root)
    root.mainloop()

if __name__ == '__main__':
    main()