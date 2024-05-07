import boto3
from flask import Flask , render_template, request

app =  Flask(__name__)
rekognition = boto3.client("rekognition")
s3 = boto3.client("s3")
dynamodb = boto3.client("dynamodb")

#landing page route
@app.route("/")
def index():
   return render_template("index.html")


@app.route("/upload",methods=["POST"])
def upload():
   if 'file' not in request.files:
      return "file not found"
   
   file= request.files["file"]
   if file.filename == "":
      return "file not selected"
   
   #get details of uploaded file
   filename = file.filename
   file.save("visitors/"+filename)

   #match image with the images in collection
   with open("visitors/"+filename,"rb") as file:
      image_bytes = file.read()

   collection_id = "employee"   
   matched_info = match_image_with_collection(image_bytes,collection_id)
   
   #get detailes from dynamodb
   table_name = "van-employee-table"

   if matched_info:
     faceid =matched_info[0]["Face"]["FaceId"]
     first_name,last_name = get_name_from_dynamodb(table_name,faceid)

   else:
      first_name = "unknown"
      last_name = "unknown"  


   return render_template("index.html",matched_info=matched_info,first_name=first_name,last_name=last_name)

def match_image_with_collection(image_bytes,collection_id, threshold = 80):
   try:
      response = rekognition.search_faces_by_image(
         CollectionId= collection_id,
         Image = {"Bytes":image_bytes},
         FaceMatchThreshold = threshold,
         MaxFaces = 1

      )
      face_match = response["FaceMatches"]
      return face_match
   
   except Exception as e:
      return f"Error matching image with collection {e} "

def get_name_from_dynamodb(table_name, faceid): 
   try:
      #get firstname and lastname
      response = dynamodb.get_item(
         TableName =  table_name,
         Key = {"rekID":{"S":faceid}}
      )

      if 'Item' in response:
         item = response["Item"]
         first_name = item.get("firstname",{}).get("S","unknown")
         last_name = item.get("lastname",{}).get("S","unknown")
         return first_name, last_name

      else: 
         return None, None   #first_name = none, last_name = none  

   except Exception as e:
       print(f"Error in retrieving name from dynamodb {e}")
       return None, None # assuming the item does not exist, in case of error

   
if __name__ == "__main__":
   app.run(debug = True)   