import pandas as pd
from sklearn.preprocessing import LabelEncoder

def load_data(path):
    df = pd.read_csv(path)
    return df

def preprocess_data(df):
    df = df.copy()

    # Remove account IDs for first model version
    df = df.drop(["nameOrig", "nameDest"], axis=1)

    # Encode transaction type
    le = LabelEncoder()
    df["type"] = le.fit_transform(df["type"])

    return df, le