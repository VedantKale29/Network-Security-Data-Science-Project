from networksecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.constant.training_pipeline import SCHEMA_FILE_PATH
from scipy.stats import ks_2samp
import pandas as pd
import os, sys
from networksecurity.utils.main_utils.utils import read_yaml_file, write_yaml_file

class DataValidation:
    def __init__(self,data_validation_config:DataValidationConfig,
                 data_ingestion_artifact:DataIngestionArtifact):
        try:
            self.data_validation_config=data_validation_config
            self.data_ingestion_artifact=data_ingestion_artifact
            self._schema_config=read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise NetworkSecurityException(e,sys)
    
    @staticmethod
    def read_data(file_path:str)->pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e,sys)
    
    def validate_number_of_columns(self,dataframe:pd.DataFrame)->bool:
        try:
            number_of_columns=len(self._schema_config)
            logging.info(f"Required number of columns:{number_of_columns}")
            logging.info(f"Data frame has columns:{len(dataframe.columns)}")
            if len(dataframe.columns)==number_of_columns:
                return True
            return False
        except Exception as e:
            raise NetworkSecurityException(e,sys)
    
    def is_numeriacal_column_exist(self, dataframe: pd.DataFrame) -> bool:
        try:
            numerical_columns = self._schema_config.get("numerical_columns", [])

            # Strip spaces from schema column names
            numerical_columns = [col.strip() for col in numerical_columns]

            dataframe_columns = dataframe.columns
            missing_columns = []

            for column in numerical_columns:
                if column not in dataframe_columns:
                    missing_columns.append(column)

            if len(missing_columns) > 0:
                logging.error(
                    f"Missing numerical columns in dataframe: {missing_columns}"
                )
                return False

            logging.info("All numerical columns are present in the dataframe")
            return True

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def detect_data_drift(self,base_dataframe:pd.DataFrame,current_dataframe:pd.DataFrame, threshold=0.05)->dict:
        try:
            status=True
            report={}
            for column in base_dataframe.columns:
                d1=base_dataframe[column]
                d2=current_dataframe[column]
                is_same_dist=ks_2samp(d1,d2)
                if threshold<=is_same_dist.pvalue:
                    is_found=False
                else:
                    is_found=True
                    status=False
                report.update({column:{
                    "p_value":float(is_same_dist.pvalue),
                    "drift_status":is_found
                    
                    }})
            drift_report_file_path = self.data_validation_config.drift_report_file_path

            #Create directory
            dir_path = os.path.dirname(drift_report_file_path)
            os.makedirs(dir_path,exist_ok=True)
            write_yaml_file(file_path=drift_report_file_path,content=report)

        except Exception as e:
            raise NetworkSecurityException(e,sys)
        
    def initiate_data_validation(self)->DataValidationArtifact:
        try:
            train_file_path=self.data_ingestion_artifact.train_file_path
            test_file_path=self.data_ingestion_artifact.test_file_path

            ## Read the data from train and test file location
            train_dataframe=DataValidation.read_data(train_file_path)
            test_dataframe=DataValidation.read_data(test_file_path)

            ## Validate number of column
            status=self.validate_number_of_columns(train_dataframe)
            if not status:
                error_msg="Train data does not contain all columns. \n"
            status=self.validate_number_of_columns(test_dataframe)
            if not status:
                error_msg="Test data does not contain all columns."

            ## Validate numerical columns
            status=self.is_numeriacal_column_exist(train_dataframe)
            if not status:
                error_msg="Train data does not contain all numerical columns. \n"
            status=self.is_numeriacal_column_exist(test_dataframe)
            if not status:
                error_msg="Test data does not contain all numerical columns."
            
            ## Let's check data drift
            status=self.detect_data_drift(base_dataframe=train_dataframe,
                                           current_dataframe=test_dataframe)
            dir_path=os.path.dirname(self.data_validation_config.valid_train_file_path)
            os.makedirs(dir_path,exist_ok=True)


            train_dataframe.to_csv(
                self.data_validation_config.valid_train_file_path,index=False,header=True
            )

            data_validation_artifact = DataValidationArtifact(
                validation_status=status,
                valid_train_file_path=self.data_ingestion_artifact.train_file_path,
                valid_test_file_path=self.data_ingestion_artifact.test_file_path,
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path,
            )
            return data_validation_artifact
            

        except Exception as e:
            raise NetworkSecurityException(e,sys)
