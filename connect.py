import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account.

cred = credentials.Certificate('./key.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client(app=app)

# ref = db.collection("patients")
# docs = ref.stream()

# for doc in docs:
#     print(f"{doc.id} => {doc.to_dict()}")
