from typing import Union

import requests

from src.logger_config import get_logger

logger = get_logger(__name__)


class Roche_RAG_SAAS_client:
    def __init__(self,google_share_drive,embedding_model,base_url,rass_api_key,api_id,portkey_api_key):
        self.create_collection_payload = {
            'dataSource': {
                "sourceFolderUrl": google_share_drive
            },
            'model': {
                'modelId': embedding_model
            },
            'chunkingConfiguration': [
                {
                    'pattern': "*.*",
                    'splitter': {
                        "SentenceSplitter": {
                            # https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/sentence_splitter/
                            "chunk_overlap": 100,
                            "chunk_size": 1000
                        }
                    }
                }
            ]
        }
        self.base_url = base_url
        self.raas_api_key = rass_api_key
        self.api_id = api_id
        self.portkey_api_key = portkey_api_key
        self.headers = {
            'x-api-key': self.raas_api_key,
            'x-apigw-api-id': self.api_id,
            'x-portkey-api-key': self.portkey_api_key
        }
    """
    return {'message': 'Collection creation started successfully', 'collectionId': '3b33a23e-dd51-4988-afe9-9a9a11e2b4c5'}
    """
    def create_collection(self) -> Union[str, None]:
        create_collection_response = requests.post(
            url=f"{self.base_url}/collections",
            json=self.create_collection_payload,
            headers=self.headers)
        logger.debug(f"get the creation collections response code : {create_collection_response.status_code}, get the creation collections reason: {create_collection_response.reason}")
        if create_collection_response.status_code == 200 or create_collection_response.status_code == 202 or create_collection_response.status_code ==201:
            logger.info("RAG SAAS collection created successfully.")
            collection_id = create_collection_response.json()['collectionId']
            return collection_id
        else:
            logger.error(f"Failed to create RAG SAAS collection: {create_collection_response.text}")
            return None
    """
    {'collection': {'collectionId': '3b33a23e-dd51-4988-afe9-9a9a11e2b4c5',
                'debug': {'currentState': 'SetCollectionStatusActive',
                          'stepFunctionCause': None,
                          'stepFunctionError': None,
                          'stepFunctionStartDate': '2025-08-19T09:50:44.588000+00:00',
                          'stepFunctionStatus': 'SUCCEEDED',
                          'stepFunctionStopDate': '2025-08-19T09:51:14.321000+00:00'},
                'embeddingSize': 768,
                'endTimestamp': '2025-08-19T09:51:14.122Z',
                'expiresAfter': '9999-12-31T23:59:59Z',
                'modelId': 'text-embedding-004',
                'owner': '7048a166418c648cf6312646262fcc81a6b844c97707f7f40a52be2a0ec621ac',
                'startTimestamp': '2025-08-19T09:50:44.626Z',
                'status': 'ACTIVE',
                'ttlHours': -1}}
    
    """
    def retrieve_collection_status(self, collection_id) -> bool:
        logger.info(f"Retrieving RAG SAAS collection status: {collection_id}")
        retrieve_collection_status_url = f"{self.base_url}/collections/{collection_id}"
        retrieve_collection_status_response = requests.get(
            url=retrieve_collection_status_url,
            headers=self.headers)
        logger.debug(f"get the retrieve_collection_status_response code : {retrieve_collection_status_response.status_code}, get the retrieve_collection_status_response reason: {retrieve_collection_status_response.reason}, get the retrieve_collection_status_response body is : {retrieve_collection_status_response.text}")
        if retrieve_collection_status_response.status_code == 200 or retrieve_collection_status_response.status_code == 201 or retrieve_collection_status_response.status_code ==202:
            status = retrieve_collection_status_response.json()['collection']['status']
            if status == 'ACTIVE':
                logger.info(f"RAG SAAS collection status: {status}")
                return True
            else:
                logger.warning(f"RAG SAAS collection status: {status}")
                return False
        else:
            logger.error(f"Failed to retrieve RAG SAAS collection status: {retrieve_collection_status_response.text}")
            return False

    """
    
    {'embedding_model': 'text-embedding-004',
     'limit': 7,
     'message': 'Successfully searched table: 3b33a23e-dd51-4988-afe9-9a9a11e2b4c5',
     'query_text': 'What is the population of Portugal?',
     'result_count': 7,
     'results': [{'_distance': 0.40382224321365356,
                  'expiresAfter': '9999-12-31T23:59:59Z',
                  'fileType': 'txt',
                  'page': None,
                  'sourceFile': 'file_1.txt',
                  'text': 'Portugal, long a country of emigration (the vast '
                          'majority of Brazilians have Portuguese ancestry), has '
                          'now become a country of net immigration, and not just '
                          'from the last Indian (Portuguese until 1961), African '
                          '(Portuguese until 1975), and Far East Asian (Portuguese '
                          'until 1999) overseas territories. An estimated 800,000 '
                          "Portuguese returned to Portugal as the country's "
                          'African possessions gained independence in 1975. By '
                          '2007, Portugal had 10,617,575 inhabitants of whom about '
                          '332,137 were legal immigrants.\n'
                          'According to the 2011 Census, 81.0% of the Portuguese '
                          'population are Roman Catholic. The country has small '
                          'Protestant, Latter-day Saint, Muslim, Hindu, Sikh, '
                          "Eastern Orthodox Church, Jehovah's Witnesses, Baha'i, "
                        ...
                        'results_processing_time': 0,
                        'search_execution_time': 0.1607,
                        'table_opening_time': 0.0727,
                        'total_execution_time': 0.7888}}
                        """
    def search(self,collection_id,query:str):
        search_url = f"{self.base_url}/collections/{collection_id}/search"
        search_payload = {
            "queryText": query,
            "limit": 7
        }
        search_response = requests.post(
            url=search_url,
            json=search_payload,
            headers=self.headers)
        logger.debug(f"get the search_response code : {search_response.status_code}, get the search_response reason: {search_response.reason}")
        if search_response.status_code == 200 or search_response.status_code == 201 or search_response.status_code ==202:
            results =  [result['text'] for result in search_response.json()['results']]
            logger.info(f"RAG SAAS search results retrieved successfully.")
            return results
        else:
            logger.error(f"Failed to perform RAG SAAS search: {search_response.text}")
            return None
    """
    {'collections': [{'modelId': 'text-embedding-004',
   'startTimestamp': '2025-08-11T14:32:04.058Z',
   'ttlHours': -1,
   'expiresAfter': '9999-12-31T23:59:59Z',
   'endTimestamp': '2025-08-11T14:32:31.837Z',
   'status': 'ACTIVE',
   'embeddingSize': 768,
   'owner': '30ed2a4341ed4623433866598923e3d0b2470c9a4a35c462799d3803bc1d6e71',
   'collectionId': '7613468c-d083-48b5-8e79-a3fce9a1f2e1'},
  {'modelId': 'text-embedding-004',
   'startTimestamp': '2025-08-12T05:14:32.975Z',
   'ttlHours': -1,
   'expiresAfter': '9999-12-31T23:59:59Z',
   'endTimestamp': '2025-08-12T05:14:48.630Z',
   'status': 'ACTIVE',
   'embeddingSize': 768,
   'owner': '30ed2a4341ed4623433866598923e3d0b2470c9a4a35c462799d3803bc1d6e71',
   'collectionId': '0a77f270-ea72-4f8c-812e-0ec3e60ceefd'},
  {'modelId': 'text-embedding-004',
   'startTimestamp': '2025-08-12T05:18:46.492Z',
   'ttlHours': -1,
   'expiresAfter': '9999-12-31T23:59:59Z',
   'endTimestamp': '2025-08-12T05:18:54.658Z',
   'status': 'ACTIVE',
   'embeddingSize': 768,
...
   'expiresAfter': '9999-12-31T23:59:59Z',
   'status': 'IN_PROGRESS',
   'embeddingSize': 768,
   'owner': '30ed2a4341ed4623433866598923e3d0b2470c9a4a35c462799d3803bc1d6e71',
   'collectionId': '6da0ce38-1094-461b-88a4-830d00ad5499'}]}
    
    """
    def list_collections(self) -> Union[list, None]:
        list_collections_url = f"{self.base_url}/develop/collections"
        headers = self.headers | {'Content-Type': 'application/json'}
        headers.pop("x-portkey-api-key", None)
        list_collections_response = requests.get(
            url=list_collections_url,
            headers=headers)
        logger.debug(
            f"get the list_collections_response code : {list_collections_response.status_code}, get the list_collections_response reason: {list_collections_response.reason}")

        if list_collections_response.status_code == 200 or list_collections_response.status_code == 202 or list_collections_response.status_code == 202:
            collections = list_collections_response.json().get('collections', [])
            logger.info(f"RAG SAAS collections listed successfully.")
            return collections
        else:
            logger.error(f"Failed to list RAG SAAS collections: {list_collections_response.text}")
            return None

    def remove_a_file_from_collection(self,collection_id,file_name) -> bool:
        remove_file_url = f"{self.base_url}/collections/{collection_id}/documents/{file_name}"
        remove_file_response = requests.delete(
            url=remove_file_url,
            headers=self.headers)
        logger.debug(remove_file_response.status_code, remove_file_response.reason)
        if remove_file_response.status_code == 200:
            logger.info(f"File {file_name} removed from RAG SAAS collection {collection_id} successfully.")
            return True
        else:
            logger.error(f"Failed to remove file {file_name} from RAG SAAS collection {collection_id}: {remove_file_response.text}")
            return False

    def remove_collection(self,collection_id) -> bool:
        remove_collection_url = f"{self.base_url}/collections/{collection_id}"
        remove_collection_response = requests.delete(
            url=remove_collection_url,
            headers=self.headers)
        logger.debug(
            f"get the remove_collection_response code : {remove_collection_response.status_code}, get the remove_collection_response reason: {remove_collection_response.reason}")
        if remove_collection_response.status_code == 200 or remove_collection_response.status_code == 202 or remove_collection_response.status_code == 202:
            logger.info(f"RAG SAAS collection {collection_id} removed successfully.")
            return True
        else:
            logger.error(f"Failed to remove RAG SAAS collection {collection_id}: {remove_collection_response.text}")
            return False

    """
    得到各个collections里面已经indexed的文件列表
    
    {
      'dataSources': [
        {
              'dataSourceName': 'collection_1',
              's3Uri': 's3://mb-ragasaservicestack-mbgalileoragsharedresourcesm-urnkbqjcwp1j/30ed2a4341ed4623433866598923e3d0b2470c9a4a35c462799d3803bc1d6e71/upload/dataSource-1afa8c6f',
              'files': [
                'Wprowadzenie do uczenia g\u0142\u0119bokiego (1) (1).pdf'
              ]
            },
            {
              'dataSourceName': 'collection_1',
              's3Uri': 's3://mb-ragasaservicestack-mbgalileoragsharedresourcesm-urnkbqjcwp1j/30ed2a4341ed4623433866598923e3d0b2470c9a4a35c462799d3803bc1d6e71/upload/dataSource-25171d78',
              'files': [
                'file_1.txt',
                'file_2.txt'
              ]
            }
          ]
        }
    """
    def list_indexed_files_in_collections(self):
        files_url = f"{self.base_url}/files"
        files_response = requests.get(
            url=files_url,
            headers=self.headers)
        logger.debug(
            f"get the files_response code : {files_response.status_code}, get the files_response reason: {files_response.reason}")
        if files_response.status_code == 200 or files_response.status_code == 202 or files_response.status_code == 202:
            files = files_response.json().get('dataSources', [])
            logger.info(f"RAG SAAS indexed files listed successfully.")
            return files
        else:
            logger.error(f"Failed to list RAG SAAS indexed files: {files_response.text}")
            return None