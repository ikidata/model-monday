# Databricks notebook source
class AIMaster():
    def __init__(self, uc_catalog: str, uc_schema: str, uc_table: str):
        self.logger = self.activate_logger() 
        self.uc_catalog = uc_catalog
        self.uc_schema = uc_schema
        self.uc_table = uc_table

        self.fetch_configs()
        self.activate_authentication()
        
        # Enable MLflow Tracing for RAG
        mlflow.langchain.autolog()                               

    def activate_authentication(self):
        '''
        Authentication fetched from Notebook
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
            self.model_name = config_data['model_name']
            self.vector_search_endpoint_name= config_data['vector_search_endpoint_name']
            self.endpoint = config_data['endpoint']
            self.embedding_endpoint = config_data['embedding_endpoint']
            self.extra_params = config_data['extra_params']
            self.system_prompt = config_data['system_prompt']
            self.rag_prompt = config_data['rag_prompt']
        self.logger.info(f"Configs have been fetched successfully")

    def activate_llm(self, extra_params: dict):
        '''
        Activating LLM model
        '''
        llm = ChatDatabricks(
                endpoint=self.endpoint,
                extra_params = extra_params
                )
        return llm

    def get_retriever(self): 
        '''
        The get_retriever function initializes a vector search client using provided credentials and configurations, retrieves a vector search index based on the specified endpoint and index name, and creates a retriever object from the vector store. This retriever can be used to perform search operations on the indexed data. The function returns the configured retriever object.
        '''

        # Get the vector search index
        vsc = VectorSearchClient(
            workspace_url = self.server_hostname, 
            personal_access_token = self.token, 
            disable_notice=True
            )
        vs_index = vsc.get_index(
            endpoint_name = self.vector_search_endpoint_name,
            index_name = f"{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_index"
            )

        # Create the retriever
        vectorstore = DatabricksVectorSearch(
            vs_index, text_column = 'text', 
            embedding = self.embedding_endpoint
            )
        return vectorstore.as_retriever()


    def with_rag(self, user_query: str, q: str):
        '''
        The with_rag function generates a response to a user query using a Retrieval-Augmented Generation (RAG) approach. It initializes a prompt template, creates a retrieval-based question-answering chain with a specified language model and retriever, and logs the generated answer along with the query and elapsed time. The function leverages an internal create_prompt method to format the input for the language model.
        '''
        TEMPLATE = self.rag_prompt

        # Create a PromptTemplate with the formatted template
        prompt = PromptTemplate(template=TEMPLATE, 
                                input_variables=["context", "question"])
        
        chain = RetrievalQA.from_chain_type(
            llm = self.activate_llm(self.extra_params),
            chain_type = "stuff",
            retriever= self.get_retriever(),
            chain_type_kwargs={"prompt": prompt}
            )
        question = {"query": user_query}
        start_time = time.time()                 
        answer = chain.invoke(question)
        elapsed_time = round(time.time() - start_time, 2)   
        self.logger.info(f"Rag AI reply has been generated succesfully for question: {q}")
        df = self.log_answers(answer['query'], answer['result'], elapsed_time, 'rag', q)
    
    def create_prompt(self, question: str):  
        '''
        Creating prompt
        '''

        # Define the prompt template  
        system_message = (  
            "system",  self.system_prompt
            )  

        fixed_prompt = {
                    "messages": [
                        {
                        "role": "system",
                        "content": system_message
                        },
                        {
                        "role": "user",
                        "content": question
                        }
                    ]
                    }

        return json.dumps(fixed_prompt)
    
    def without_rag(self, prompt: str, q: str):
        '''
        The function starts by recording the current time and formatting the prompt using an internal create_prompt method. Depending on the type of question (q), it activates a LLM model with different configurations and generates an answer. The function logs the generated answer along with the original question and elapsed time, and stores this information using the log_answers method.
        '''
        start_time = time.time()                                                # Start the timer                                                   
        prompt = self.create_prompt(prompt)
        if q == 'q6':                                                           # Adding more tokens for math problem solving question
           llm_model = self.activate_llm({"max_tokens": 2000, "temperature": 0.01})
        else:
            llm_model = self.activate_llm(self.extra_params)
        answer = llm_model.invoke(prompt).content
        elapsed_time = round(time.time() - start_time, 2)                       # Calculate the elapsed time                              
        question = ast.literal_eval(prompt)['messages'][1]['content']
        self.logger.info(f"Normal AI reply has been generated succesfully for question: {q}")
        df = self.log_answers(question, answer, elapsed_time, 'normal', q)
    
    def call_chat_model(self, prompt: str, **kwargs): 
        """Calls the chat model and returns the response text or tool calls."""
        chat_args = {
            "model": self.endpoint,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.extra_params['max_tokens'],
            "temperature": self.extra_params['temperature'],
        }
        chat_args.update(kwargs)

        chat_completion = self.openai_client.chat.completions.create(**chat_args)

        response = chat_completion.choices[0].message
        if response.tool_calls:
            call_args = [c.function.arguments for c in response.tool_calls]
            if len(call_args) == 1:
                return get_weather(json.loads(call_args[0])['city']) 
            return get_weather(json.loads(call_args)['city'])
    
    def mosaic_function(self, text: str, q: str):
        '''
        The mosaic_function defines a set of tools for the chat model, including a function to get weather information for a specific city. The function then calls the chat model with the provided prompt and tools, logs the generated response along with the original text, question type, and elapsed time, and stores this information using the log_answers method.
        '''
        base_url = f'https://{spark.conf.get("spark.databricks.workspaceUrl")}/serving-endpoints'
        self.openai_client = OpenAI(api_key=self.token, base_url=base_url)

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a chosen city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City to be used",
                            }
                        },
                        "required": ["city"],
                    },
                },
            }
        ]

        start_time = time.time()                           
        response = self.call_chat_model(prompt = text, 
                                        tools=tools)
        elapsed_time = round(time.time() - start_time, 2)   
        self.logger.info(f"Mosaic AI Function calling reply has been generated succesfully for question: {q}")
        self.log_answers(text, response, elapsed_time,'function', q)

    def log_answers(self, question: str, answer: str, time: float, answer_type: str, q: str) -> None:
        '''
        The log_answers function logs the details of a question-answering session by creating a DataFrame with the answer, question, input prompt, elapsed time, model name, and answer type. It appends this data to a specified table in a unified catalog schema and logs a success message. The function uses delta tables to manage the data operations and ensure the information is stored persistently.
        '''
        df = (spark.createDataFrame([(answer,)], ["ai_output"] ) 
                    .withColumn('question', f.lit(q))
                    .withColumn('input_prompt', f.lit(question))
                    .withColumn('time_s', f.lit(time))
                    .withColumn('model', f.lit(self.model_name))
                    .withColumn('answer_type', f.lit(answer_type))
                    .withColumn('inserted', f.current_timestamp()))
        df.write.mode('append').saveAsTable(f'{uc_catalog}.{uc_schema}.{uc_table}_inference_table')
        self.logger.info(f"Answer has been logged successfully for question {q}")

    def call_ai(self, prompt: str, q: str):
        '''
        The call_ai function dispatches the processing of a prompt based on the type of question (q). It calls the with_rag method for RAG-based questions, the mosaic_function for function-based questions, and the without_rag method for all other types of questions. This function acts as a central point for handling different AI workflows.
        '''
        if q == 'q_rag':
            self.with_rag(prompt, q)
        elif q == 'q_function':
            self.mosaic_function(prompt, q)
        else:
            self.without_rag(prompt, q)

# COMMAND ----------

# Main program
if __name__ == "__main__":
    # Activating Main Class
    main = AIMaster(uc_catalog = uc_catalog, 
                    uc_schema = uc_schema, 
                    uc_table = uc_table)

    # Fetching question data and looping all questions one by one
    with open("./configs.json", 'r') as json_file:
                questions = json.load(json_file)['questions']

    for q_number, question in questions.items():
        main.call_ai(question, q_number)
