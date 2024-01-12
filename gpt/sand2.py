from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
class InputString(BaseModel):
    input_string: str


from openai import OpenAI
import openai 
client = OpenAI()
openai.api_key = "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"

import json


def filter_city(reviews,city="Austin", CuisineType="",Neighborhood="",PerfectFor=""):
    sub_review=[]
    for rev in reviews:
        # import pdb;pdb.set_trace()
        if not city in rev["city"]:
            continue
        if CuisineType != "" and not any(s.lower() == CuisineType.lower() for s in rev["cuisine_tags"]):
             continue
        if Neighborhood != "" and not any(Neighborhood.lower() in s.lower()  for s in rev["neighborhood_tags"]):
             continue
        if PerfectFor != "" and not any(PerfectFor.lower() in s.lower() for s in rev["perfect_for_tags"]):
             continue
        sub_review.append(rev)
    return sub_review



# app = Flask(__name__)

# @app.route('/process_string', methods=['GET', 'POST'])
# def process_string():
#     if request.method == 'POST':
#         input_string = request.json.get('input_string')
#         print("post")
#     else:
#         input_string = request.args.get('input_string')
#         print("get")
#     print("I got the prompt",input_string)
#     quit()
#     completion = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are a food critic based in Austin TX. keep you responces short, ideally just the name of the resturant"},
#             {"role": "user", "content": "{input_string}"}
#         ]
#     )
#     responce= completion.choices[0].message.content

#     # Process the string here (this is just a placeholder)
#     print(responce)    
#     return jsonify({"original": input_string, "processed": responce})

@app.post("/process_string/")
async def process_string(CuisineType: str="",Neighborhood : str="", PerfectFor:str=""):
    # try:
        # Process the string here
        lumped_input="".join([CuisineType,Neighborhood,PerfectFor])
        print("I got the prompt",CuisineType,Neighborhood,PerfectFor)
        responce="test"
        # reviews=filter_city("Austin",CuisineType,Neighborhood,PerfectFor)
        bad_parse=''
        with open("/home/sentry/sandbox/gpt/reviews.json","r") as fp:
            reviews=json.load(fp)
        reviews=filter_city(reviews,"Austin")
        if len(filter_city(reviews,CuisineType=CuisineType))>0:
            reviews = filter_city(reviews,CuisineType=CuisineType)
        else:
            bad_parse+="I am looking for "+CuisineType+". " 
        if len(filter_city(reviews,Neighborhood=Neighborhood))>0:
            reviews = filter_city(reviews,Neighborhood=Neighborhood)
        else:
            bad_parse+="I am looking for something in "+Neighborhood+". "
        if len(filter_city(reviews,PerfectFor=PerfectFor))>0:
            reviews = filter_city(reviews,PerfectFor=PerfectFor)
        else:
            bad_parse+="I am looking for something for "+PerfectFor+". "
        print(bad_parse)
        role="You are a food critic based in Austin TX. keep you responces short, ideally just the name of the resturant. which of these resteruants should I go to tonight?"
        if bad_parse:
            role+=" Also you should know "+bad_parse
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": "{reviews}"}
            ]
        )
        responce= completion.choices[0].message.content
         

        # Process the string here (this is just a placeholder)
        print(responce)    
        print({"original": lumped_input, "processed": responce})
        print(json.dumps({"original": lumped_input, "processed": responce}))
        return json.dumps({"original": lumped_input, "processed": responce})
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)