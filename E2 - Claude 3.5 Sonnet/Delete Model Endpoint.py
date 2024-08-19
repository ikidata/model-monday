# Databricks notebook source
class ModelEndpointClass():
    '''
    This Class creates external model endpoint for Anthropic.
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
            self.endpoint_name = config_data['endpoint']
            self.kv_scope = config_data['kv_scope']
            self.kv_secret = config_data['kv_secret']
        self.logger.info(f"Configs has been fetched successfully")  

    def delete_model_endpoint(self):
        '''
        Deleting a Vector Search Endpoint Using the Databricks REST API
        '''
        headers = {'Authorization': 'Bearer %s' % self.token}
        api_version = '/api/2.0'
        api_command = f'/serving-endpoints/{self.endpoint_name}'
        url = f'{self.server_hostname}{api_version}{api_command}'

        session = requests.Session()
        resp = session.request('DELETE', url, verify=True, headers=headers)
        assert resp.status_code == 200, f"Deleting External model serving endpoint for Anthropic has failed. \nError code: {resp.status_code}\nError message: {resp.json()}"
        self.logger.info(f"Deleting External model serving endpoint for Anthropic has been created successfully\n\n{resp.json()}")

# COMMAND ----------

# Main program
if __name__ == "__main__":
    main = ModelEndpointClass(uc_catalog = uc_catalog, uc_schema = uc_schema, uc_table = uc_table)
    main.delete_model_endpoint()
