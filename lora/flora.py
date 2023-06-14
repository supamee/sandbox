def max_wait(id):
    return int(0.5*id*(id+5))+id
    # return id**2+id
def upper_limit_map(count):
    return int((count*(count+1)*(count+8))/6)

class Lora:
    def __init__(self,name:str,id:int,connections:list,data_rate:int,SD_rate:int,internet=False,total_nodes=1):
        self.name=name
        self.id=id
        connections.sort(key = lambda connections: -1*connections[1])
        self.connections = connections
        print("connnections",self.id,self.connections)
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
        self.peers=[]
        self.upstream_info={}
        self.branch_length=0
        self.distance_from_internet=125
        self.got_times=[]
        self.t=0
        if self.internet: self.distance_from_internet = 0
        self.total_nodes=total_nodes

    def tick(self,count=1):
        self.t+=1
        out_going_ping_len=4
        responce_ping_len=4
        search_rep_len=2
        if self.outgoing:
            return
        if len(self.incomming)>0:
            
            if self.incomming[0]==128:
                if len(self.incomming)>=out_going_ping_len:
                    if self.state=="":
                        self.state="echo_ping"
                        print(self.id,"wait")
                        self.total_nodes=self.incomming[1]
                        self.distance_from_internet=self.incomming[2]+1
                        if not self.incomming[3] in self.downstream:
                            self.downstream.append(self.incomming[3])
                        self.branch_length=max(self.branch_length,self.distance_from_internet)
                        self.ping_time=self.t
                        self.outgoing=[128,self.incomming[1],self.incomming[2]+1,self.id]
                        for i in range(out_going_ping_len-len(self.outgoing)):
                            self.outgoing.append(0)

                        # delay=this_msg_size+respond_msg_size+2*self.total_nodes
                        # self.wait=self.total_nodes*delay-self.incomming[2]*delay+self.id*respond_msg_size
                        # self.wait=self.total_nodes*delay-self.incomming[2]*delay+self.id*respond_msg_size
                        # self.wait=self.incomming[2]*(respond_msg_size)+this_msg_size+1
                        # self.wait=this_msg_size+respond_msg_size*2-1
                        self.wait=(out_going_ping_len+1)*2+(self.distance_from_internet-1)*(2*responce_ping_len)-1
                        # self.wait=9
                        self.incomming=self.incomming[out_going_ping_len:]
                        return
                    elif self.state=="echo_ping" or self.state=="hub":
                        if not self.incomming[3] in self.upstream and not self.incomming[3] in self.downstream:
                            self.upstream_info[self.incomming[3]]={"length":0,"nodes":[]}
                            self.upstream.append(self.incomming[3])
                            self.incomming=self.incomming[out_going_ping_len:]
            elif self.incomming[0]==129:

                if len(self.incomming)>=responce_ping_len:
                    self.got_times.append(self.t)
                    # 129, id, branch_length
                    if self.state=="echo_ping":

                        print(self.id,",",self.distance_from_internet,":",self.incomming[1])
                        if not self.incomming[1] in self.downstream: self.downstream.append(self.incomming[1])
                        
                        # self.number_upstream+=1
                        # self.upstream_info[self.incomming[1]]={"count":self.incomming[2],"nodes":[0]*self.incomming[2],"length":0}
                        self.branch_length=max(self.branch_length,self.incomming[2])
                        self.incomming=self.incomming[responce_ping_len:]
                    elif self.state=="responded" or self.state=="hub":
                        if not self.incomming[1] in self.downstream:
                            # if self.incomming[2]>self.branch_length:
                            print("check 129",self.id," msg:",self.incomming," cur branch length:",self.branch_length)
                            if not self.incomming[1] in self.upstream_info:
                                self.upstream.append(self.incomming[1])
                                self.upstream_info[self.incomming[1]]={"length":self.incomming[2]-self.distance_from_internet,"nodes":[]}            
                            self.upstream_info[self.incomming[1]]["length"]=max(self.upstream_info[self.incomming[1]]["length"],self.incomming[2]-self.distance_from_internet)
                            if self.incomming[3] !=0:
                                if not self.incomming[3] in self.upstream_info[self.incomming[1]]["nodes"]:
                                    self.upstream_info[self.incomming[1]]["nodes"].append(self.incomming[3])
                            self.branch_length = self.incomming[2]
                            # if self.state=="responded":
                            self.outgoing=[129,self.id,self.branch_length,self.incomming[1]]
                        else:
                            if not self.incomming[1] in self.downstream: self.downstream.append(self.incomming[1])

                        self.incomming=self.incomming[responce_ping_len:]
                        if self.state=="hub":
                            self.wait=max(self.wait,(out_going_ping_len+3*responce_ping_len)-len(self.outgoing)+2)
            elif self.incomming[0]==130:
                if self.incomming[-1]==0:
                    if not( self.state=="hub_search" or self.state=="searching"):
                        if not self.id in self.incomming:
                            self.outgoing=[131,self.id]
                        else:
                            self.state="searching_wait"
                            self.peers=self.incomming[1:-1]
                            self.peers.remove(self.id)
                            print(self.id,"peers:",self.peers)
                            # self.wait=2*self.incomming.index(self.id)
                            self.wait=search_rep_len+1
                    self.incomming=[]
            elif self.incomming[0]==131:
                if len(self.incomming)>=search_rep_len:
                    if self.state=="hub_search" or self.state=="searching":
                        if not self.incomming[1] in self.upstream:
                            self.upstream.append(self.incomming[1])
                            self.branch_length=max(self.distance_from_internet+1,self.branch_length)
                            self.upstream_info[self.incomming[1]]={"lenght":self.branch_length,"nodes":[]}
                            self.state="search_again"
                    self.incomming=self.incomming[search_rep_len:]



            elif self.incomming[-1]==0:
                self.incomming.pop(-1)
            elif self.incomming[0] == 0:
                self.incomming.pop(0)
            
        if self.state=="searching_wait":
            if self.wait>1:
                self.wait-=1
            elif self.wait==1:
                self.wait=0
                self.outgoing=[130]
                self.outgoing.extend(self.upstream)
                self.state="searching"

        elif self.state == "echo_ping":
            if self.wait >1:
                self.wait-=1   
            elif self.wait==1:
                self.outgoing=[129,self.id,self.branch_length,self.upstream[0] if len(self.upstream)>0 else 0]
                for i in range(responce_ping_len-len(self.outgoing)):
                    self.outgoing.append(0)
                self.state="responded"
                self.wait=0
        
        elif self.state=="listen_ping":
            
            if self.wait >1:
                self.wait-=1
            elif self.wait==1:
                self.upstream=self.incomming
                self.outgoing=[129]
                for i in range(len(self.outgoing)):
                    self.outgoing.append(self.upstream[i])
                self.outgoing.append(0)
                self.wait=0
        
        elif self.state=="wait_ping":
            if self.wait >1:
                self.wait-=1
            elif self.wait==1:
                self.outgoing=[self.id]
                self.state="wait_set_id"
                self.wait=0

        elif self.state=="hub":
            if self.wait>1:
                self.wait-=1
            elif self.wait==1:
                self.wait=0
                self.state="hub_search"
                self.outgoing=[130]
                self.outgoing.extend(self.upstream)

        elif self.state == "":
            if self.internet:
                self.state = "hub"
                self.wait=out_going_ping_len*4+responce_ping_len+1
                self.ping_time=self.t
                self.outgoing=[128,self.total_nodes,0,self.id]
                for i in range(out_going_ping_len-len(self.outgoing)):
                    self.outgoing.append(0)
                

    def show_view(self):
        print(self.name," ",self.id," upstream",self.upstream," downstream",self.downstream, "dist",self.distance_from_internet," up_stream_info", self.upstream_info)
                


class Network:
    def __init__(self,nodes):
        self.map={}
        self.tick_count=0
        for node in nodes:
            self.map[node.name]=node
    
    def resolve(self):
        for node in self.map:
            got_something=False
            if not self.map[node].outgoing:
                for target, db in self.map[node].connections:
                    if len(self.map[target].outgoing)>0:
                        # print("adding",target,"to",node)
                        self.map[node].incomming.append(self.map[target].outgoing[0])
                        got_something=True
                        break
                if not got_something:
                    self.map[node].incomming.append(0)
        for node in self.map:
            if len(self.map[node].outgoing)>0:
                self.map[node].outgoing.pop(0)
    def tick(self,count=1):
        for i in range(count):
            self.tick_count+=1
            for node in self.map:
                self.map[node].tick()
            print(mesh)
            self.resolve()
        
    def __repr__(self):
        temp=str(self.tick_count)+"\n"
        for node in self.map:
            temp+= str(node)+" "+str(self.map[node].id)+" ^"+str(self.map[node].outgoing)+" v"+str(self.map[node].incomming)+" w"+str(self.map[node].wait)+" s "+str(self.map[node].state)+"\n"

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
nodec=Lora("3",3,[["4",-30],["5",-30]],0,0,False)
noded=Lora("4",4,[["6",-20],["3",-30],["2",-40],["1",-40]],0,0,False)
nodee=Lora("5",5,[["2",-40],["3",-30]],0,0,False)
nodef=Lora("6",6,[["4",-20]],0,0,False)

# nodea=Lora("1",1,[["4",-20],],0,0,True,6)
# nodeb=Lora("2",2,[["4",-20],["5",-40]],0,0,False)
# nodec=Lora("3",3,[["4",-40]],0,0,False)
# noded=Lora("4",4,[["6",-40],["3",-40],["2",-40],["1",-40]],0,0,False)
# nodee=Lora("5",5,[["2",-40]],0,0,False)
# nodef=Lora("6",6,[["4",-40]],0,0,False)

# nodea=Lora("1",1,[["2",-20],],0,0,True,6)
# nodeb=Lora("2",2,[["3",-20],["1",-40]],0,0,False)
# nodec=Lora("3",3,[["4",-40],["2",-30]],0,0,False)
# noded=Lora("4",4,[["5",-40],["3",-40]],0,0,False)
# nodee=Lora("5",5,[["6",-40],["4",-30]],0,0,False)
# nodef=Lora("6",6,[["5",-40]],0,0,False)

# nodea=Lora("1",1,[["2",-20],],0,0,False,6)
# nodeb=Lora("2",2,[["3",-20],["1",-40]],0,0,False)
# nodec=Lora("3",3,[["4",-40],["2",-30]],0,0,False)
# noded=Lora("4",4,[["5",-40],["3",-40]],0,0,False)
# nodee=Lora("5",5,[["6",-40],["4",-30]],0,0,False)
# nodef=Lora("6",6,[["5",-40]],0,0,True,6)

# nodea=Lora("6",6,[["5",-20],],0,0,True,6)
# nodeb=Lora("5",5,[["4",-20],["6",-40]],0,0,False)
# nodec=Lora("4",4,[["3",-40],["5",-30]],0,0,False)
# noded=Lora("3",3,[["2",-40],["4",-40]],0,0,False)
# nodee=Lora("2",2,[["1",-40],["3",-30]],0,0,False)
# nodef=Lora("1",1,[["2",-40]],0,0,False)





mesh=Network([nodea,nodeb,nodec,noded,nodee,nodef])

# print(mesh)
mesh.tick(70)
mesh.show_view()
mesh.tick(7)
mesh.show_view()
mesh.tick(3)
mesh.show_view()
# mesh.tick(12)
# mesh.show_view()

# mesh.tick(12)
# mesh.show_view()
# mesh.tick(4)
# mesh.tick(4)
# mesh.show_view()
# mesh.tick(4)
# mesh.show_view()
# mesh.tick(55)
# mesh.show_view()
# mesh.tick(33)
# mesh.show_view()
# # mesh.tick(8)
# mesh.show_view()
# mesh.tick(5)
# mesh.show_view()

# mesh.tick(17)
# mesh.show_view()
# mesh.tick(20)
# mesh.show_view()
# mesh.tick(upper_limit_map(6))
# mesh.show_view()



