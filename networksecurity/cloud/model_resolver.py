# networksecurity/cloud/model_resolver.py

import boto3
import pickle
from networksecurity.exception.exception import NetworkSecurityException
import sys

class S3ModelResolver:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3")

    def get_latest_timestamp(self) -> str:
        try:
            obj = self.s3.get_object(
                Bucket=self.bucket_name,
                Key="final_model/latest.txt"
            )
            return obj["Body"].read().decode("utf-8").strip()
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def load_model(self, timestamp: str):
        try:
            preprocessor = self._load_pickle(
                f"final_model/{timestamp}/preprocessor.pkl"
            )
            model = self._load_pickle(
                f"final_model/{timestamp}/model.pkl"
            )
            return preprocessor, model
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def _load_pickle(self, key: str):
        obj = self.s3.get_object(
            Bucket=self.bucket_name,
            Key=key
        )
        return pickle.loads(obj["Body"].read())
