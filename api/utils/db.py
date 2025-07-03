import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd


def get_finance_transactions():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    docs = db.collection("stock_analysis").get()

    transactions_df = pd.DataFrame([doc.to_dict() for doc in docs])
    return transactions_df
