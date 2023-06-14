from flask import Flask, render_template
from PIL import Image
import io
import base64
import os

app = Flask(__name__)

@app.route("/")
def hello_world():
    directory="images"
  

    start_doc="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Image</title>
    </head>
    <body> 
    <h2>Detections:</h2>
    """
    
    to_return=start_doc
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".jpg") or filename.endswith(".py"): 
            im = Image.open(directory+"/"+filename)
            data = io.BytesIO()
            im.save(data, "JPEG")
            encoded_img_data = base64.b64encode(data.getvalue())
            to_return+='<img id="picture" src="data:image/jpeg;base64,'+encoded_img_data.decode('utf-8')+'" width="200"><br/>'

    end_doc = """
    </body>
    </html>
    """
    to_return+=end_doc
    print(to_return)
    return to_return
 