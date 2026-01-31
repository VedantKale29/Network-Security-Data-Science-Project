from dataclasses import dataclass

@dataclass
class DataIngestionArtifact:
    """
    Represents an artifact generated during the data ingestion phase
    of a network security project.
    """
    train_file_path: str
    test_file_path: str