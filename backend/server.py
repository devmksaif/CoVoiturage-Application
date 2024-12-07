from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
app = Flask(__name__)
import os
# Enable CORS for all routes and all origins
CORS(app)


# Replace 'mongodb://localhost:27017/' with your MongoDB connection string
client = MongoClient("mongodb://localhost:27017/")

# Specify the database you want to use (it will be created if it doesn't exist)
db = client["covoiturage"]

# Specify the collection you want to work with (it will be created if it doesn't exist)
users_collection = db["users"]
drivers_collection = db["drivers"]
vehicules_verification = db["vehicules"]
ride_collection = db["ride"]

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/post-verify-driver', methods=['POST'])
def verify_driver():
    data = request.json
    vehicule = data.get("vehicule")
    status = data.get("status")
    try:
        vehicules_verification.insert_one(vehicule )
        return jsonify({"msg" : "success"}), 200
    except Exception as e:
        print(e)
        return jsonify({"msg" : "error_server"})
        
@app.route('/verify_docs_state', methods=["POST"])
def verify_user_state():
    data = request.json
    phone = data.get("phone_number")
    role = data.get("role")
    result = None
    try:
        if role == "driver":
     
            result = drivers_collection.update_one(
                {"numerotel": phone}, 
                {"$set": {"verified_documents": "review"}}
            )
            if result is not None:
                if result.matched_count == 0:
                    return jsonify({"message": "not_found"}), 404                                                  
                else:
                    return jsonify({"message": "user_updated"}), 200
            else:
                     return jsonify({"error": "Missing fields"}), 500 
    except Exception as e:
        # Log the exception (optional)
        print(f"Error: {e}")
        return jsonify({"message": "Server error"}), 500      
        
@app.route('/upload-documents', methods=['POST'])
def upload_documents():
    try:
        phone = request.form.get("phone")
        if not phone:
            return jsonify({"message": "Phone number is required"}), 400

        files = request.files
        # Path to the user's upload directory
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], phone)

        # Create the directory for the user if it doesn't exist
        os.makedirs(user_folder, exist_ok=True)

        # Save each file
        for file_key in files:
            file = files[file_key]
            save_path = os.path.join(user_folder, file.filename)
            file.save(save_path)

        return jsonify({"message": "Files uploaded successfully"}), 200
    except Exception as e:
        print("Upload error:", e)
        return jsonify({"message": f"Error uploading files: {str(e)}"}), 500
    
    
    
# Assume users_collection and drivers_collection are already defined MongoDB collections
@app.route('/get_user', methods=["POST"])
def get_user():
    data = request.json
    phone = data.get("phone_number")
    role = data.get("role")
   
    
    if role == "passenger":
        user = users_collection.find_one({"numerotel" : phone})
        user["_id"] = str(user["_id"])
        try:
            if user:
                return jsonify(user) , 200
            else:
                return jsonify("user_not_found") , 404
        except Exception as e:
            print(e)
            return jsonify("server_error") , 500
    else:
        driver = drivers_collection.find_one({"numerotel" : phone})         
        driver["_id"] = str(driver["_id"])     
        try:
            if driver:
                return jsonify(driver) , 200
            else:
                return jsonify("user_not_found") , 404
        except Exception as e:
            print(e)
            return jsonify("server_error") , 500
    
    
@app.route('/verify_user', methods=["POST"])
def verify_user():
    data = request.json
    phone = data.get("phone_number")
    role = data.get("role")

    try:
        result = None
        if role == "passenger":
             
            result = users_collection.update_one(
                {"numerotel": phone}, 
                {"$set": {"verified_number": "true"}}
            )
        else:
     
            result = drivers_collection.update_one(
                {"numerotel": phone}, 
                {"$set": {"verified_number": "true"}}
            )

        # Check if a document was updated
        if result.matched_count == 0:
            return jsonify({"message": "not_found"}), 404

        return jsonify({"message": "user_verified"}), 200

    except Exception as e:
        # Log the exception (optional)
        print(f"Error: {e}")
        return jsonify({"message": "Server error"}), 500


@app.route('/register',methods=["POST"])
def home():
    data = request.json
    name_lastname = data.get("fullname")
  
    numero_tel = data.get("numerotel")
    mdp = data.get("mdp")
    conf_mdp = data.get("conf_mdp")
    role = data.get("role")
    first_time = data.get("first_time")
    dob = data.get("dob")
    verified_number = data.get("verified_number")
    if name_lastname is None  or numero_tel is None or mdp is None or conf_mdp is None or role is None or first_time is None or dob is None:
        return jsonify("Missing fields"),405 
    try:
        if role == "passenger":
            if users_collection.find_one({"numerotel" : numero_tel}) is None and role=="passanger":
                users_collection.insert_one({
                    "fullname" : name_lastname,
                    "numerotel" : numero_tel,
                    "mdp" : mdp,
                    "conf_mdp" : conf_mdp,
                    "role" : role,
                    "first_time" : first_time,
                    "dob" : dob,
                    "verified_number" : verified_number
                })
                return jsonify("u_registered") , 200
            else:
                return jsonify("u_exists") , 200
        elif role =="driver":
            if drivers_collection.find_one({"numerotel" : numero_tel}) is None and role=="driver":
                drivers_collection.insert_one({
                    "fullname" : name_lastname,
                    "numerotel" : numero_tel,
                    "mdp" : mdp,
                    "conf_mdp" : conf_mdp,
                    "role" : role,
                    "first_time" : first_time,
                    "dob" : dob,
                    "verified_number" : verified_number,
                    "verified_documents" : "ongoing"
                })
                return jsonify("u_registered") , 200
            else:
                return jsonify("u_exists") , 200
    except Exception as e:
        return jsonify("u_error") , 500
@app.route('/find_user/',methods=["POST"])
def find():
    data = request.json
    phone = data.get("phone_number")
     
    user = users_collection.find_one({"numerotel" : f"{str(phone)}"})
    user["_id"] = str(user["_id"])
    try:
        if user is None:
            return jsonify("not_found") , 400
        else:
            return jsonify(user) ,200
    except Exception as e:
        print(e)
        return jsonify("u_error") , 500   

@app.route('/data')
def data():
    return jsonify(data="Here's some data with CORS enabled!")

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0")
