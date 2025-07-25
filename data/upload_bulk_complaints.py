import json
import requests
import base64

# ===========================================
# IBM Cloudant Configuration
# ===========================================

# Your Cloudant service credentials (from IBM Cloud)
CLOUDANT_USERNAME = 'c98bb419-564a-4e42-a872-458562350fc5-bluemix.cloudantnosqldb.appdomain.cloud'
CLOUDANT_APIKEY = 'JRJFIsvp5HoCPHQ-SyZgnHS3YwrMPULaYpMrsJExq5N-'

# The name of your Cloudant database
DB_NAME = 'users'

# Construct the Cloudant base URL using your username
CLOUDANT_URL = f'https://c98bb419-564a-4e42-a872-458562350fc5-bluemix.cloudantnosqldb.appdomain.cloud'

# ===========================================
# Create Basic Auth Header
# ===========================================

# Combine username and apikey into auth string and encode to base64
auth_string = f"c98bb419-564a-4e42-a872-458562350fc5-bluemix.cloudantnosqldb.appdomain.cloud:JRJFIsvp5HoCPHQ-SyZgnHS3YwrMPULaYpMrsJExq5N-"
auth_token = base64.b64encode(auth_string.encode()).decode()

# Prepare the HTTP headers for Cloudant API
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Basic {auth_token}'
}

# ===========================================
# Bulk Users Document
# ===========================================

data = {
    "docs": [
        {
            "_id": "PrincipalA",
            "email": "shikhwatprincipal@alphaschool.edu",
            "password": "P1_alpha",
            "role": "admin"
        },
        {
            "_id": "TransportH",
            "email": "shekar@alphaschool.edu",
            "password": "T1_head",
            "role": "admin"
        },
        {
            "_id": "TransportH2",
            "email": "gernal@alphaschool.edu",
            "password": "T2_head",
            "role": "admin"
        },
        {
            "_id": "TeacherH1",
            "email": "sharma@alphaschool.edu",
            "password": "Teach_head1",
            "role": "admin"
        },
        {
            "_id": "TeacherH2",
            "email": "sinha@alphaschool.edu",
            "password": "Teach_head2",
            "role": "admin"
        },
        {
            "_id": "TeacherH3",
            "email": "thakur@alphaschool.edu",
            "password": "Teach_head3",
            "role": "admin"
        },
        {
            "_id": "MeenaVibes",
            "email": "meenakshi.verma@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Meenakshi Verma",
            "student_id": "Alpha01"
        },
        {
            "_id": "RajeshPro",
            "email": "rajesh.pandey@yahoo.com",
            "password": "parent123",
            "role": "parent",
            "name": "Rajesh Pandey",
            "student_id": "Bravo02"
        },
        {
            "_id": "FatimaStar",
            "email": "fatima.shaikh@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Fatima Shaikh",
            "student_id": "Charlie03"
        },
        {
            "_id": "AnilAce",
            "email": "anil.mehta@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Anil Mehta",
            "student_id": "Delta04"
        },
        {
            "_id": "GeetaGlow",
            "email": "geeta.singh@outlook.com",
            "password": "parent123",
            "role": "parent",
            "name": "Geeta Singh",
            "student_id": "Echo05"
        },
        {
            "_id": "VijayVibes",
            "email": "vijay.rana@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Vijay Rana",
            "student_id": "Foxtrot06"
        },
        {
            "_id": "AshaAngel",
            "email": "asha.das@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Asha Das",
            "student_id": "Golf07"
        },
        {
            "_id": "DeepakDynamo",
            "email": "deepak.mittal@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Deepak Mittal",
            "student_id": "Hotel08"
        },
        {
            "_id": "RahulRocks",
            "email": "rahul.sharma@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Rahul Sharma",
            "student_id": "India09"
        },
        {
            "_id": "PriyaPro",
            "email": "priya.patel@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Priya Patel",
            "student_id": "Juliet10"
        },
        {
            "_id": "SureshSavvy",
            "email": "suresh.kumar@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Suresh Kumar",
            "student_id": "Kilo11"
        },
        {
            "_id": "NishaNice",
            "email": "nisha.singh@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Nisha Singh",
            "student_id": "Lima12"
        },
        {
            "_id": "Ankushpro",
            "email": "ankush.thakur@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Ankush Thakur",
            "student_id": "Ænkey15"
        },
        {
            "_id": "apurvastar",
            "email": "apurva.sharma@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Apurva Sharma",
            "student_id": "apu27"
        },
        {
            "_id": "rahuldynamo",
            "email": "rahul.rana@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Rahul Rana",
            "student_id": "rahulreigns"
        },
        {
            "_id": "johandude",
            "email": "johan.dhiman@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Johan Dhiman",
            "student_id": "jack90"
        },
        {
            "_id": "ashishrocks",
            "email": "ashish.sharma@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Ashish Sharma",
            "student_id": "ashi480"
        },
        {
            "_id": "ankitaangel",
            "email": "ankita.parmar@gmail.com",
            "password": "parent123",
            "role": "parent",
            "name": "Ankita Parmar",
            "student_id": "demo40"
        }
    ]
}

# ===========================================
# Upload Data to Cloudant
# ===========================================

response = requests.post(f'https://c98bb419-564a-4e42-a872-458562350fc5-bluemix.cloudantnosqldb.appdomain.cloud/users/_bulk_docs', headers=headers, data=json.dumps(data))

# Show the result
print("Status Code:", response.status_code)
print("Response:", response.json())
