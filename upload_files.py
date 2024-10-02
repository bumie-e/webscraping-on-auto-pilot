import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from datetime import datetime
from dotenv import load_dotenv

_ = load_dotenv()

class AzureBlob:

    def __init__(self, filename, container_name, connection_string):

        self.today = datetime.today().strftime('%Y-%m-%d')
        self.filename = filename #os.environ.get('FILEPATH')
        self.file_path = f"data/{self.today}/{self.filename}.csv"
        self.container_name = container_name #os.environ.get('CONTAINER')
        self.connection_string = connection_string# os.environ.get("AZURE_STORAGE_CONNECTION_STRING")


    def upload_to_blob(self, blob_name):
        try:
            # Create a BlobServiceClient to interact with the Blob service
            blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

            # Create a container client (it will reference your specific container)
            container_client = blob_service_client.get_container_client(self.container_name)

            # Check if the container exists, if not, create it
            if not container_client.exists():
                container_client.create_container()

            # Create a BlobClient for the file
            blob_client = blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)

            # Open the file in binary read mode and upload its content
            with open(self.file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)

            print(f"{self.file_path} successfully uploaded to {blob_name} in Azure Blob Storage.")

        except Exception as ex:
            print(f"Error uploading file to Azure Blob: {str(ex)}")

    # Call this function after generating the CSV file
    def generate_and_upload_csv(self):
        # Blob name will include the date as part of the "folder" structure
        blob_name = f"{self.today}/{self.filename}.csv"

        # Upload the generated file to Azure Blob Storage
        self.upload_to_blob(blob_name)

if __name__ == '__main__':
    # Generate the CSV file and upload to Azure
    filename = os.environ.get('FILEPATH')
    container_name = os.environ.get('CONTAINER')
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")

    blob = AzureBlob(filename, container_name, connection_string)
    blob.generate_and_upload_csv()
