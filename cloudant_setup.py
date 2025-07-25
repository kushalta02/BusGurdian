from cloudant import Cloudant

USERNAME = 'c98bb419-564a-4e42-a872-458562350fc5-bluemix'
API_KEY = 'a7t0e8e2iQ_nYgJYJvtRejxgBdt7ii-fw8klSvpTHfqa'
URL = 'https://c98bb419-564a-4e42-a872-458562350fc5-bluemix.cloudantnosqldb.appdomain.cloud'

client = Cloudant.iam(USERNAME, API_KEY, connect=True, url=URL)

# Connect to all databases
users_db = client['users']
buses_db = client['buses']
complaints_db = client['complaints']
attendance_db = client['attendance']
alerts_db = client['alerts']
students_db = client['students']
