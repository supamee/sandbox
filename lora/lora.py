def max_wait(id):
    return int(0.5*id*(id+5))+id
    # return id**2+id
def upper_limit_map(count):
    return int((count*(count+1)*(count+8))/6)

class Lora:
    def __init__(self,name:str,id:int,connections:list,data_rate:int,SD_rate:int,internet=False,total_nodes=1):
        self.name=name
        self.id=id
        connections.sort(key = lambda connections: connections[1])
        self.connections = connections
        self.data_rate=data_rate
        self.SD_rate = SD_rate
        self.incomming=[]
        self.outgoing=[]
        self.time_count=0
        self.state=""
        self.wait=0
        self.looking_at = []
        self.turns=[]
        self.internet=internet
        self.conductor=False
        self.upstream=[]
        self.downstream=[]
        self.distance_from_internet=125
        if self.internet: self.distance_from_internet = 0
        self.total_nodes=total_nodes

    def tick(self,count=1):
        if len(self.incomming)>0:
            if 0 in self.incomming:
                index=self.incomming.index(0)
                self.looking_at=self.incomming[0:index]
                self.incomming=self.incomming[index+1:]
                if self.looking_at[0]==128:
                    if self.id in self.looking_at[2:]:
                        index=self.looking_at[2:].index(self.id)
                        if not self.looking_at[-1] in self.upstream:
                            self.upstream.append(self.looking_at[-1])
                    else:
                        if self.state=="" or self.state == "map_wait":
                            self.distance_from_internet = min(len(self.looking_at[2:]),self.distance_from_internet)
                            for node in self.looking_at[2:]:
                                if not node in self.downstream:
                                    self.downstream.append(node)
                        self.state="map_wait"
                        self.wait=max_wait(self.id)

        if self.state=="map_wait":
            if self.wait>1:
                self.wait-=1
                return
            if self.wait==1:
                self.outgoing=self.looking_at[:2]+self.downstream+[self.id]+[0]
                self.state="map_done"
                self.wait=0
            else:
                self.state=""
                self.wait=0

        if self.state == "":
            if self.internet:
                self.state = "map_done"
                self.outgoing=[128,self.total_nodes,1,0]
                self.id=1
    def show_view(self):
        print(self.name," upstream",self.upstream," downstream",self.downstream, "dist",self.distance_from_internet)
                


class Network:
    def __init__(self,nodes):
        self.map={}
        for node in nodes:
            self.map[node.name]=node
    
    def resolve(self):
        for node in self.map:
            for target, db in self.map[node].connections:
                if len(self.map[target].outgoing)>0:
                    # print("adding",target,"to",node)
                    self.map[node].incomming.append(self.map[target].outgoing[0])
                    break
        for node in self.map:
            if len(self.map[node].outgoing)>0:
                self.map[node].outgoing.pop(0)
    def tick(self,count=1):
        for i in range(count):
            for node in self.map:
                self.map[node].tick()
            print(mesh)
            self.resolve()
        
    def __repr__(self):
        temp=''
        for node in self.map:
            temp+= str(node)+" ^"+str(self.map[node].outgoing)+" v"+str(self.map[node].incomming)+" w"+str(self.map[node].wait)+" s "+str(self.map[node].state)+"\n"

        return temp
    def show_view(self):
        for node in self.map:
            self.map[node].show_view()


# TEST CASES


# nodea=Lora("1",1,[["2",-20],],0,0,True,6)
# nodeb=Lora("2",2,[["1",-20],["3",-40],["4",-40]],0,0,False)
# nodec=Lora("3",3,[["2",-40],["5",-30],["6",-40]],0,0,False)
# noded=Lora("4",4,[["2",-40],["5",-40]],0,0,False)
# nodee=Lora("5",5,[["3",-40],["4",-30]],0,0,False)
# nodef=Lora("6",6,[["3",-40]],0,0,False)

# mesh=Network([nodea,nodeb,nodec,noded,nodee,nodef])

nodea=Lora("1",1,[["4",-20],],0,0,True,6)
nodeb=Lora("2",2,[["4",-20],["5",-40]],0,0,False)
nodec=Lora("3",3,[["4",-40],["5",-30]],0,0,False)
noded=Lora("4",4,[["6",-40],["3",-40],["2",-40],["1",-40]],0,0,False)
nodee=Lora("5",5,[["2",-40],["3",-30]],0,0,False)
nodef=Lora("6",6,[["4",-40]],0,0,False)

mesh=Network([nodea,nodeb,nodec,noded,nodee,nodef])

print(mesh)
mesh.tick(10)

mesh.tick(17)
mesh.show_view()
mesh.tick(20)
mesh.show_view()
mesh.tick(upper_limit_map(6))
mesh.show_view()



