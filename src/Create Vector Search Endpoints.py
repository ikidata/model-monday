# Databricks notebook source
class VectorSearchClass():
    '''
    This Class Activates both vector search endpoint and vector search index based on config file parameters.
    '''
    def __init__(self, uc_catalog: str, uc_schema: str, uc_table: str):
        # Activating logger
        self.logger = self.activate_logger() 

        # Activating authentication
        self.activate_authentication()

        # Fetching configs
        self.fetch_configs()

        # Setting up self parameters
        self.uc_catalog = uc_catalog
        self.uc_schema = uc_schema
        self.uc_table = uc_table


    def activate_authentication(self):
        '''
        Fetching Authentication Details from the Notebook.
        '''
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        self.server_hostname = context.apiUrl().get()
        self.token = context.apiToken().get()  
    
    def activate_logger(self):
        '''
        Activating Logger for Monitoring.
        '''
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%d.%m.%Y %H:%M:%S")

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        #Only add handler the first time
        if len(logger.handlers) == 0:
            logger.addHandler(handler)
        
        return logger

    def fetch_configs(self):
        '''
        Fetching necessary configs.
        '''
        with open("./configs.json", 'r') as json_file:
            config_data = json.load(json_file)['configs']
            self.vector_search_endpoint_name= config_data['vector_search_endpoint_name']
            self.embedding_endpoint = config_data['embedding_endpoint']
        self.logger.info(f"Configs has been fetched successfully")

    def create_vector_search_endpoint(self):
        '''
        "Creating a Vector Search Endpoint Using the Databricks REST API"
        '''
        headers = {'Authorization': 'Bearer %s' % self.token}
        api_version = '/api/2.0'
        api_command = '/vector-search/endpoints'
        url = f'{self.server_hostname}{api_version}{api_command}'

        payload = {  
                "name": self.vector_search_endpoint_name,
                "endpoint_type": "STANDARD"
                }   

        session = requests.Session()

        resp = session.request('POST', url, data = json.dumps(payload), verify=True, headers=headers)
        assert resp.status_code == 200, f"Creating Vector Search Endpoint '{self.vector_search_endpoint_name}' has failed. \nError code: {resp.status_code}\nError message: {resp.json()}"
        self.logger.info(f"Vector Search Endpoint '{self.vector_search_endpoint_name}' has been created successfully\n\n{resp.json()}")

    def create_vector_search_index(self):
        '''
        Creating a Vector Search Index Using the Databricks REST API
        '''
        headers = {'Authorization': 'Bearer %s' % self.token}
        api_version = '/api/2.0'
        api_command = '/vector-search/indexes'
        url = f'{self.server_hostname}{api_version}{api_command}'

        payload = {
                "name": f"{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index",
                "endpoint_name": self.vector_search_endpoint_name, 
                "primary_key": "id",
                "index_type": "DELTA_SYNC",
                "delta_sync_index_spec": {
                    "source_table":  f"{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_rag_data",
                    "pipeline_type": "TRIGGERED",
                    "embedding_source_columns": [
                    {
                        "name": "text",
                        "embedding_model_endpoint_name": self.embedding_endpoint
                    }
                    ]
                }
                } 
    

        session = requests.Session()

        resp = session.request('POST', url, data = json.dumps(payload), verify=True, headers=headers)
        assert resp.status_code == 200, f"Creating Vector Search Index '{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index' has failed. \nError code: {resp.status_code}\nError message: {resp.json()}"
        self.logger.info(f"Vector Search Index '{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index' has been created successfully\n\n{resp.json()}")

    def validate_successful_endpoint_provision(self):

        headers = {'Authorization': 'Bearer %s' % self.token}
        api_version = '/api/2.0'
        api_command = f'/vector-search/endpoints/{self.vector_search_endpoint_name}'
        url = f'{self.server_hostname}{api_version}{api_command}'

        session = requests.Session()

        ready = False
        while ready != True:
            resp = session.request('GET', url, verify=True, headers=headers)
            assert resp.status_code == 200, f"Fetching Vector Search Endpoint '{self.vector_search_endpoint_name}' has failed. \nError code: {resp.status_code}\nError message: {resp.json()}"
            if resp.json()['endpoint_status']['state'] == 'PROVISIONING':
                ready = False
                self.logger.info(f"Vector Search Endpoint '{self.vector_search_endpoint_name}' is still provisioning. Wait 30sec before the next try.")
                time.sleep(30)
            elif resp.json()['endpoint_status']['state'] == 'ONLINE':
                ready = True
                self.logger.info(f"Vector Search Endpoint '{self.vector_search_endpoint_name}' is online.")
            else:
                self.logger.info(f"Something went wrong with '{self.vector_search_endpoint_name}' provisioning. State is {resp.json()['endpoint_status']['state']} - please check it manually")
                ready = True

    def validate_successful_index_provision(self):

        headers = {'Authorization': 'Bearer %s' % self.token}
        api_version = '/api/2.0'
        api_command = f'/vector-search/indexes/{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index'
        url = f'{self.server_hostname}{api_version}{api_command}'

        session = requests.Session()

        ready = False
        while ready != True:
            resp = session.request('GET', url, verify=True, headers=headers)
            assert resp.status_code == 200, f"Fetching Vector Search Index '{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index' has failed. \nError code: {resp.status_code}\nError message: {resp.json()}"
            if resp.json()['status']['ready'] == False:
                ready = False
                self.logger.info(f"Vector Search Index '{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index' is still provisioning. Wait 30sec before the next try.")
                time.sleep(30)
            else:
                ready = True
                self.logger.info(f"Vector Search Endpoint '{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index' is online.")
                time.sleep(30)

# COMMAND ----------

# Main program
if __name__ == "__main__":
    main = VectorSearchClass(uc_catalog = uc_catalog, uc_schema = uc_schema, uc_table = uc_table)
    main.create_vector_search_endpoint()
    main.create_vector_search_index()
    main.validate_successful_endpoint_provision()
    main.validate_successful_index_provision()
