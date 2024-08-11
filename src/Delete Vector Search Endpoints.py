# Databricks notebook source
class VectorSearchDeletionClass():
    '''
    This Class Activas both vector search endpoint and vector search index based on config file parameters.
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
    
    def delete_vector_search_endpoint(self):
        '''
        Deleting a Vector Search Endpoint Using the Databricks REST API"
        '''
        headers = {'Authorization': 'Bearer %s' % self.token}
        api_version = '/api/2.0'
        api_command = f'/vector-search/endpoints/{self.vector_search_endpoint_name}'
        url = f'{self.server_hostname}{api_version}{api_command}'

        session = requests.Session()
        
        resp = session.request('DELETE', url, verify=True, headers=headers)
        assert resp.status_code == 200, f"Deleting Vector Search Endpoint '{self.vector_search_endpoint_name}' has failed. \nError code: {resp.status_code}\nError message: {resp.json()}"
        self.logger.info(f"Vector Search Endpoint '{self.vector_search_endpoint_name}' has been deleted")


    def delete_vector_search_index(self):
        '''
        Deleting a Vector Search Index Using the Databricks REST API
        '''
        headers = {'Authorization': 'Bearer %s' % self.token}
        api_version = '/api/2.0'
        api_command = f'/vector-search/indexes/{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index'
        url = f'{self.server_hostname}{api_version}{api_command}'
        session = requests.Session()

        resp = session.request('DELETE', url, verify=True, headers=headers)
        assert resp.status_code == 200, f"Deleting Vector Search Index '{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index' has failed. \nError code: {resp.status_code}\nError message: {resp.json()}"
        self.logger.info(f"Waiting 60 to make sure vector searh index has been fully deleted - it take some time")
        time.sleep(60)
        self.logger.info(f"Vector Search Index '{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index' has been deleted successfully")
        

# COMMAND ----------

# Main program
if __name__ == "__main__":
    main = VectorSearchDeletionClass(uc_catalog = uc_catalog, uc_schema = uc_schema, uc_table = uc_table)
    main.delete_vector_search_index()
    main.delete_vector_search_endpoint()
