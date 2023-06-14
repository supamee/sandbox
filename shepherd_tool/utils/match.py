import os
import time
from uuid import uuid4
from PIL import Image
import io
import numpy as np

from detection_store import DetectionStore
from track import build_tracks_from_faces
from face import SleepyFace
import pdb
import subprocess
import shutil
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
# import img_show
# import sys
# sys.path
# sys.path.append('../viola_test')
# sys.path.append('../viola_test/viola/vinnie')
# import check_face 

def cosine_distance(e1, e2):
    return (1- np.dot(e1.flatten(), e2.flatten())/ (np.linalg.norm(e1.flatten()) * np.linalg.norm(e2.flatten()))) / 2
    
def match(root_folder_name: str, post_clustering_folder: str,):
    all_folders = os.listdir(root_folder_name)
    sfaces = []
    sframes={}
    for folder in all_folders:
        if os.path.isdir(os.path.join(root_folder_name, folder)):
            all_files = os.listdir(os.path.join(root_folder_name, folder))
            for f in all_files:
                # print(1,f)
                path = os.path.join(root_folder_name, folder, f)
                try:
                    store = DetectionStore().open(path)
                except:
                    print("failed to open detectStore")
                    continue
                    
                faces = store.read_all_faces(include_image=True)
                frames = store.read_all_frames(include_image=True)
                store.close()
                for face in faces:
                    sf = SleepyFace(
                        face_id=str(f),
                        sentry="sentry",
                        timestamp=time.time(),
                        embedding=face.embedding,
                        known_identity=None,
                    )
                    sf.crop = face.image
                    sfaces.append(sf)
                for frame in frames:
                    sframes[f]=frame
    matches = build_tracks_from_faces(
        faces=sfaces,
        minimum_cluster_size=1,
        append_face_object=True,
        return_intermediate=True,
    )
    i=0
    if not os.path.exists(f"{post_clustering_folder}/img"):
            os.makedirs(f"{post_clustering_folder}/img")
    for k, v in matches.items():
        i+=1
    # for i in range(len(matches.items)):
        # k,v = matches.items[i]
        # print("here:",i,k)
        cf = os.path.join(post_clustering_folder, f"person:{str(k)}")
        if not os.path.exists(cf):
            os.makedirs(cf)
        # os.mkdir(cf)
        for f in v:
            img = Image.open(io.BytesIO(f.crop))
            # print("hgere",f.face_id)
            
            tempname=f.face_id.split(":")[-1]
            f.face_id=f.face_id.split(":")[-1]
            if tempname in sframes:
                # with open(f"{post_clustering_folder}/img/-frame{f.face_id}.jpg", "wb") as f:
                #     f.write(sframes[tempname].image)
                # print("test")
            #     # frame=Image.open(io.BytesIO(sframes[f.face_id].image))
                cfi = os.path.join(cf, f"{tempname}:frame.jpg")
            #     # frame.save(cfi)
            #     print(cfi)
                with open(cfi, "wb") as f:
                    f.write(sframes[tempname].image)
            #     if not os.path.exists(f"{post_clustering_folder}/img"):
            #         os.makedirs(f"{post_clustering_folder}/img")
            #     with open(f"{post_clustering_folder}/img/-frame{f.face_id}.jpg", "wb") as f:
            cfi = os.path.join(cf, f"{tempname}:crop.jpg")
            img.save(cfi)
    
    # n = 0
    # if not os.path.exists(f"{post_clustering_folder}/img"):
    #         os.makedirs(f"{post_clustering_folder}/img")
    # for name in sframes:
    #     n += 1
    #     with open(f"{post_clustering_folder}/img/-frame{name}.jpg", "wb") as f:
    #         f.write(sframes[name].image)
def match_multi(root_folder_name: str,sub_path:str, post_clustering_folder: str,user_help=False):
    all_folders = os.listdir(root_folder_name)
    sfaces = []
    sframes={}
    i=0
    for each_device in all_folders:
        print("working on device:",each_device)
        # os.path.join(root_folder_name, each_device, sub_path)
        if each_device == '.DS_Store':
            continue
        outer_folders = os.listdir(os.path.join(root_folder_name, each_device, sub_path))
        # print("outer_folders",outer_folders)
        
        for f in outer_folders:
            i+=1
            # print(1,f)
            path = os.path.join(root_folder_name,each_device,sub_path, f)
            try:
                store = DetectionStore().open(path)
            except:
                print("failed to open detectStore",path)

                continue
                
            faces = store.read_all_faces(include_image=True)
            frames = store.read_all_frames(include_image=True)
            store.close()
            for face in faces:
                
                image = Image.open(io.BytesIO(face.image))
                x,y = image.size
                if (x>=50 and y>=70):

                # if check_face.check(image):
                    # print("\n\nGOOD",len(face.image),i,len(all_files),"\n\n")
                # if len(face.image)>1500:
                    # print(f,x,y,x*y)
                    temp_name=str(f)+"@"+str(each_device)
                    sf = SleepyFace(
                        face_id=temp_name,
                        sentry="sentry",
                        timestamp=time.time(),
                        embedding=face.embedding,
                        known_identity=None,
                    )
                    sf.crop = face.image
                    sfaces.append(sf)
                # else:
                #     print("bad face",f,i,len(all_files))
            for frame in frames:
                sframes[f]=frame
    matches = build_tracks_from_faces(
        faces=sfaces,
        minimum_cluster_size=1,
        append_face_object=True,
        return_intermediate=True,
    )
    i=0
    # if not os.path.exists(f"{post_clustering_folder}/img"):
    #         os.makedirs(f"{post_clustering_folder}/img")
    if not os.path.exists(os.path.join(root_folder_name,each_device, post_clustering_folder)):
                os.makedirs(os.path.join(root_folder_name,each_device, post_clustering_folder))
    known_faces={}
    for each_device in all_folders:
        if each_device == '.DS_Store':
            continue
        persons = os.listdir(os.path.join(root_folder_name,each_device, post_clustering_folder))
        for person in persons:
            faces=os.listdir(os.path.join(root_folder_name,each_device, post_clustering_folder,person))
            for face in faces:
                if "crop" in face:
                    known_faces[face.replace(":crop.jpg",'')]=person
    #cos(dist) # 0 -> identical
    emb_avg={}

    for k, v in matches.items():
        i+=1
        prev_match=False
        local_avg=np.zeros((1,512))
        
        # cf = os.path.join(post_clustering_folder, f"person:{str(k)}")
        # if not os.path.exists(cf):
        #     os.makedirs(cf)
        for f in v:
            
            tempname, device=f.face_id.split("@")
            tempname=tempname.split(":")[-1]
            if prev_match or tempname in known_faces:
                if tempname in known_faces:
                    k=known_faces[tempname]
                    prev_match=True
                # print("match")
                # k=known_faces[tempname]
                cf = os.path.join(root_folder_name,device, post_clustering_folder, k)
                
            else:
                # print(tempname)
                cf = os.path.join(root_folder_name,device, post_clustering_folder, str(k))
            if k in emb_avg:
                emb_avg[k].append(f.embedding)
            else:
                emb_avg[k]=[f.embedding,]
            local_avg+=f.embedding
            if not os.path.exists(cf):
                os.makedirs(cf)
            img = Image.open(io.BytesIO(f.crop))            
            if tempname in sframes:
                cfi = os.path.join(cf, f"{tempname}:frame.jpg")
                with open(cfi, "wb") as f:
                    f.write(sframes[tempname].image)
            cfi = os.path.join(cf, f"{tempname}:crop.jpg")
            img.save(cfi)
    if user_help:
        new_emb=[]
        for emb in emb_avg:
            print("?",len(emb_avg[emb]))
            new_emb.append([emb,sum(emb_avg[emb])/len(emb_avg[emb])])
        emb_avg=new_emb
        
        for emb in emb_avg:
            print(emb[0])

        to_check=[]
        for i in range(len(emb_avg)):
            for j in range(i+1,len(emb_avg)):
                print("dif of ",emb_avg[i][0], "and", emb_avg[j][0],"is ",cosine_distance(emb_avg[i][1],emb_avg[j][1]))
                to_check.append([cosine_distance(emb_avg[i][1],emb_avg[j][1]),[emb_avg[i][0], emb_avg[j][0]]])
        to_check.sort(key = lambda to_check: to_check[0])
        for temp in to_check:
            print(temp)
        for x,ab in to_check:
            a,b=ab
            a=str(a)
            b=str(b)
            print("score of ",x, "with",str(a),b)
            if x < .3:
                check_pair_folder(root_folder_name,all_folders,post_clustering_folder,a,b)








def check_pair_folder(root:str,devices:list,sub_path:str,identA:str,identB:str):
    for each_device in devices:
        if each_device == '.DS_Store':
            continue
        if identA == identB:
            continue
        fig, axs = plt.subplots(2)
        plt.ion()
        print(root, each_device, sub_path)
        temp_path=os.path.join(root, each_device, sub_path)
        print("temp path",temp_path,identA,identB)
        if os.path.isdir(os.path.join(temp_path, identA)) and os.path.isdir(os.path.join(temp_path, identB)):
            facesA = os.listdir(os.path.join(temp_path,identA))
            for exampleA in facesA:
                if "crop" in exampleA:
                    exampleA=os.path.join(temp_path,identA,exampleA)
                    axs[0].imshow(mpimg.imread(exampleA))
                    break
            facesB = os.listdir(os.path.join(temp_path,identB))
            for exampleB in facesB:
                if "crop" in exampleB:
                    exampleB=os.path.join(temp_path,identB,exampleB)
                    axs[1].imshow(mpimg.imread(exampleB))
                    break
            plt.show()
            same = input("are they the same? y/n ")
            if "y" in same:
                for each_device in devices:
                    if each_device == '.DS_Store':
                        continue
                    temp_path=os.path.join(root, each_device, sub_path)
                    if not os.path.isdir(os.path.join(temp_path, identA)):
                        print("src not real",os.path.join(temp_path, identA))
                        break
                    # else:print("real",os.path.join(temp_path, identA))
                    if not os.path.isdir(os.path.join(temp_path, identB)):
                        os.rename(os.path.join(temp_path, identA),os.path.join(temp_path,identB))
                        print("dst not real",os.path.join(temp_path, identB))
                        break
                    # else:print("real",os.path.join(temp_path, identB))
                    facesA = os.listdir(os.path.join(temp_path,identA))
                    for exampleA in facesA:
                        
                        src = os.path.join(temp_path,identA,exampleA)
                        dst=os.path.join(temp_path,identB,exampleA)
                        
                        # dst='/'.join(exampleB.split("/")[:-1])+'/'+exampleA
                        print("was",src)
                        print( "to ",dst)
                        shutil.move(src,dst)
                        
                        done=False
                    os.rmdir('/'.join(src.split("/")[:-1]))
                # last_img='/'.join(last_img.split("/")[:-1])+'/'+file
                # print("last img",last_img)
                break
            try:
                plt.close()
            except:
                pass
            break
        plt.close()



if __name__ == "__main__":
    match(
        root_folder_name="../folder",
        post_clustering_folder="test",
    )

