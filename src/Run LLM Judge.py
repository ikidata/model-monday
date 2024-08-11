# Databricks notebook source
# MAGIC %md
# MAGIC ### Remember to add ENV variables for OpenAI GPT4o endpoint
# MAGIC * OPENAI_API_KEY (dbutils.secrets.get(scope="kv", key="key"))
# MAGIC * OPENAI_API_TYPE (azure)
# MAGIC * OPENAI_API_VERSION ("2024-05-01-preview")
# MAGIC * OPENAI_API_BASE ("https://xxx.openai.azure.com/")
# MAGIC * OPENAI_DEPLOYMENT_NAME (gpt4o)"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Questions are evaluated on a scale from 1 to 5 based on the following criteria: accuracy on the topic, funniness, relevance, completeness, and uniqueness of the answer. 

# COMMAND ----------

# Setting up enviroment variables
os.environ.update(dict(
                    OPENAI_API_KEY = dbutils.secrets.get(scope="YOUR_SCOPE", key="YOUR_KEY"),
                    OPENAI_API_TYPE = "azure",
                    OPENAI_API_VERSION= "2024-05-01-preview", 
                    OPENAI_API_BASE = "https://YOUR.ENDPOINT.openai.azure.com/",
                    OPENAI_DEPLOYMENT_NAME ="YOUR_DEPLOYMENT",
                    ))

# COMMAND ----------

class JudgeMaster():
    def __init__(self, uc_catalog: str, uc_schema: str, uc_table: str):
        self.logger = self.activate_logger() 
        self.uc_catalog = uc_catalog
        self.uc_schema = uc_schema
        self.uc_table = uc_table

        self.fetch_configs()

        # Activate LLM model
        self.activate_openai()
                                    
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
            config_data = json.load(json_file)

            self.databricks_endpoint = config_data['judge_configs']['databricks_endpoint']
            self.extra_params = config_data['judge_configs']['extra_params']
            self.openai_endpoint = config_data['judge_configs']['openai_endpoint']
            self.rag_prompt = config_data['judge_prompts']['rag_prompt']
            self.rag_ground_truth = config_data['judge_prompts']['rag_ground_truth']
            self.function_prompt = config_data['judge_prompts']['function_prompt']
            self.normal_system_prompt = config_data['judge_prompts']['normal_system_prompt']
        self.logger.info(f"Configs have been fetched successfully")

    def activate_openai(self):
        '''
        Activating LLM model
        '''
        self.llm = ChatDatabricks(
                endpoint= self.databricks_endpoint,
                extra_params = self.extra_params
                )
        self.logger.info(f"GPT4o has been activated successfully")

    def extract_score_explanation(self, text: str):  
        '''
        Function to extract score and explanation  
        '''
        score_match = re.search(r'\*\*Score:\*\*\s*(\d+)', text)  
        explanation_match = re.search(r'\*\*Explanation:\*\*\s*(.*)', text)  
    
        score = score_match.group(1) if score_match else None  
        explanation = explanation_match.group(1) if explanation_match else None  
    
        return pd.Series([score, explanation])  
    
    def evaluate_similarity(self, ai_output: str, llm_type: str):
        '''
        Similarity evaluation function
        '''
        if llm_type == 'rag':
            config_data =  {
                "inputs": [
                    self.rag_prompt,
                ],
                "ground_truth": [
                    self.rag_ground_truth
                ],
                "predictions": [
                    ai_output
                ],
            }
        elif llm_type == 'function':
            config_data =  {
                "inputs": [
                    self.function_prompt,
                ],
                "ground_truth": [
                    get_weather('Helsinki') 
                ],
                "predictions": [
                    ai_output
                ],
            }
        
        else:
            raise ValueError(f"llm_type can be rag or function only but used value was: {llm_type}")  

        config_data['predictions'] = ai_output
        eval_data = pd.DataFrame(config_data)
        with mlflow.start_run() as run:
            results = mlflow.evaluate(
                data=eval_data,
                targets="ground_truth",
                predictions="predictions",
                extra_metrics=[mlflow.metrics.genai.answer_similarity()],
                evaluators="default",
            )
        
        score = results.tables['eval_results_table']['answer_similarity/v1/score'][0]
        justification = results.tables['eval_results_table']['answer_similarity/v1/justification'][0]
        return score, justification

    def create_judge_evaluations(self):
        '''
        Judge evaluation function
        '''
        df = spark.read.table(f'{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_inference_table')
        df_pandas = df.toPandas()
        df_pandas = df_pandas[df_pandas['question'] != 'q0']                     #Excluding introduction message
        self.logger.info(f"Introduction question has been dropped")
        for idx, row in df_pandas.iterrows():
                if row['answer_type'] == 'normal':
                    judge_answer = self.llm.invoke(self.prompt_generator(row['input_prompt'], row['ai_output'], row['question'])).content
                    score, explanation = self.extract_score_explanation(judge_answer) 
                    df_pandas.at[idx, 'score'] = score  
                    df_pandas.at[idx, 'explanation'] = explanation  

                else:
                    score, explanation = self.evaluate_similarity(row['ai_output'], row['answer_type'])
                    df_pandas.at[idx, 'score'] = score  
                    df_pandas.at[idx, 'explanation'] = explanation  
                self.logger.info(f"Question {row['question']} has been processed successfully")
                # Adding sleeper to avoid spamming API endpoint too much
                time.sleep(10)

        df_pandas['score'] = df_pandas['score'].astype('str')
        df_pandas['explanation'] = df_pandas['explanation'].astype('str')
        spark_df = spark.createDataFrame(df_pandas)
        spark_df.write.mode('append').saveAsTable(f'{self.uc_catalog}.{self.uc_schema}.{self.uc_table}_results')
        self.logger.info(f"Data has been saved successfully to {self.uc_catalog}.{self.uc_schema}.{self.uc_table}_results table")
    
     
    def prompt_generator(self, question: str, answer: str, q: str) -> list:  
        '''
        Prompt generation function
        '''

        # System Prompt
        system_prompt = {"master": self.normal_system_prompt}
        # Master Prompt
        master_prompt = {"q1": f"""  
        You are a Karaoke judge Expert.  Use a scale from 1 to 5 based on the following criteria: accuracy on the topic, funniness, relevance, completeness, and uniqueness of the answer.  
        
        ### Evaluation Criteria:  
        
        **Answer Correctness:**  
        
        - **Score 1:** The choice is completely off the mark, entirely different from or contradicts the provided favorite karaoke songs. It shows no similarity, relevance, or connection to popular or enjoyable karaoke tracks. There is no fun or unique appeal.
        - **Score 2:** The choice shows some similarity to popular karaoke songs and includes partially correct elements, but has significant discrepancies or inaccuracies compared to the provided favorites. While it may have elements of relevance, it lacks completeness and may be missing the fun and unique appeal that makes a karaoke song special.
        - **Score 3:** The choice accurately reflects many aspects of popular or favorite karaoke songs, aligning with the provided preferences. However, it is missing significant elements such as a strong fun factor or uniqueness. It is relevant and suitable in many ways but lacks the depth of creativity or entertainment value that makes a karaoke song stand out.
        - **Score 4:** The choice is predominantly correct, providing a popular and enjoyable karaoke song with one or more minor missteps or inaccuracies. The choice is relevant, mostly complete, and shows good levels of fun and uniqueness, adding value to the overall karaoke experience.
        - **Score 5:** The choice is spot on, demonstrating a high degree of accuracy and similarity to favorite karaoke songs. It is highly relevant, complete, and excels in fun and uniqueness, offering a novel and entertaining experience that stands out in a karaoke setting.
        
        **Original Question:** '{question}'  
        **Given Answer to be Evaluated:** '{answer}'  
        
        ### OUTPUT FORMAT:  
        
        **Score:** _  
        **Explanation:** _  
        """,

    "q2": f"""  
        You are a Finnish history Expert.  Use a scale from 1 to 5 based on the following criteria: accuracy on the topic, funniness, relevance, completeness, and uniqueness of the answer.  
        
        ### Evaluation Criteria:  
        
        **Answer Correctness:**  
        
        - **Score 1:** The choice of Finnish historical figure is completely off the mark, entirely irrelevant, or contradicts known historical facts. The discussion topic is unrelated or nonsensical, showing no similarity, relevance, or connection to Finnish history or culture. There is no fun or unique appeal.
        - **Score 2:** The choice shows some relevance to Finnish history but includes significant inaccuracies or irrelevant elements. The discussion topic is partially correct but lacks depth, missing the fun and unique appeal that would make the interaction interesting.
        - **Score 3:** The choice accurately reflects a notable Finnish historical figure and aligns with known historical facts. The discussion topic is relevant and suitable but may lack significant elements such as a strong fun factor or uniqueness. It is complete in many ways but lacks depth of creativity or entertainment value.
        - **Score 4:** The choice is predominantly correct, selecting a well-known and relevant Finnish historical figure with one or more minor inaccuracies. The discussion topic is mostly complete, showing good levels of fun and uniqueness, adding value to the overall scenario.
        - **Score 5:** The choice is spot on, demonstrating a high degree of accuracy and relevance to Finnish history. The discussion topic is highly relevant, complete, and excels in fun and uniqueness, offering a novel and entertaining perspective that stands out in the context.
        
        **Original Question:** '{question}'  
        **Given Answer to be Evaluated:** '{answer}'  
        
        ### OUTPUT FORMAT:  
        
        **Score:** _  
        **Explanation:** _  
        """,   

    "q3": f"""  
        You are a Finnish culture Expert.  Use a scale from 1 to 5 based on the following criteria: accuracy on the topic, funniness, relevance, completeness, and uniqueness of the answer.  
        
        ### Evaluation Criteria:  
        
        **Answer Correctness:**  
        
        - **Score 1:** The choice is completely off the mark, entirely irrelevant, or contradicts known aspects of Finnish culture. The explanation is nonsensical or unrelated, showing no similarity, relevance, or connection to Finnish uniqueness. There is no fun or unique appeal.
        - **Score 2:** The choice shows some relevance to Finnish culture but includes significant inaccuracies or irrelevant elements. The explanation is partially correct but lacks depth, missing the fun and unique appeal that would make the fact interesting.
        - **Score 3:** The choice accurately reflects a notable aspect of Finnish culture and aligns with known facts. The explanation is relevant and suitable but may lack significant elements such as a strong fun factor or uniqueness. It is complete in many ways but lacks depth of creativity or entertainment value.
        - **Score 4:** The choice is predominantly correct, selecting a well-known and relevant aspect of Finnish culture with one or more minor inaccuracies. The explanation is mostly complete, showing good levels of fun and uniqueness, adding value to the overall scenario.
        - **Score 5:** The choice is spot on, demonstrating a high degree of accuracy and relevance to Finnish culture. The explanation is highly relevant, complete, and excels in fun and uniqueness, offering a novel and entertaining perspective that stands out in the context.
        
        **Original Question:** '{question}'  
        **Given Answer to be Evaluated:** '{answer}'  
        
        ### OUTPUT FORMAT:  
        
        **Score:** _  
        **Explanation:** _  
        """,     

    "q4": f"""  
    You are a Haiku Expert.  Use a scale from 1 to 5 based on the following criteria: accuracy on the topic, funniness, relevance, completeness, and uniqueness of the answer.  
        
        ### Evaluation Criteria:  
        
        **Answer Correctness:**  
        
        - **Score 1:** The haiku is completely off the mark, entirely irrelevant, or contradicts known aspects of Finnish mythology. It does not follow the traditional haiku structure (5-7-5 syllables) and lacks any creative or unique appeal.
        - **Score 2:** The haiku shows some relevance to Finnish mythology but includes significant inaccuracies or irrelevant elements. It may partially follow the haiku structure but lacks depth and creativity, missing the unique appeal that makes a haiku stand out.
        - **Score 3:** The haiku accurately reflects elements of Finnish mythology and aligns with known facts. It follows the traditional haiku structure and is relevant and suitable but may lack significant elements such as strong creativity or uniqueness. It is complete in many ways but lacks depth of artistic expression.
        - **Score 4:** The haiku is predominantly correct, incorporating well-known and relevant aspects of Finnish mythology with one or more minor inaccuracies. It follows the traditional haiku structure and is mostly complete, showing good levels of creativity and uniqueness, adding value to the overall composition.
        - **Score 5:** The haiku is spot on, demonstrating a high degree of accuracy and relevance to Finnish mythology. It perfectly follows the traditional haiku structure and excels in creativity and uniqueness, offering a novel and artistically pleasing perspective that stands out.
        
        **Original Question:** '{question}'  
        **Given Answer to be Evaluated:** '{answer}'  
        
        ### OUTPUT FORMAT:  
        
        **Score:** _  
        **Explanation:** _  
        """,     
    "q5": f"""  
        You are a Business Expert.  Use a scale from 1 to 5 based on the following criteria: accuracy on the topic, funniness, relevance, completeness, and uniqueness of the answer.  
        
        ### Evaluation Criteria:  
        
        **Answer Correctness:**  
        
        - **Score 1:** The business idea is completely unfeasible, entirely different from, or contradicts the provided targets. It shows no similarity, relevance, or potential for implementation. There is no indication of scalability, profitability, or uniqueness.
        - **Score 2:** The business idea shows some similarity to viable business concepts and includes partially correct elements but has significant discrepancies or inaccuracies compared to the provided targets. While it may have elements of relevance, it lacks completeness and may be missing key aspects like scalability, profitability, and uniqueness.
        - **Score 3:** The business idea accurately addresses many aspects of a viable concept, aligning with the provided targets. However, it is missing significant elements such as clear scalability or unique market positioning. It is relevant and feasible in many ways but lacks depth in creative or innovative aspects that could enhance its profitability and uniqueness.
        - **Score 4:** The business idea is predominantly correct, providing a feasible and potentially profitable concept with one or more minor missteps or inaccuracies. The idea is relevant, mostly complete, and shows good levels of scalability and uniqueness, adding value to the overall business proposition.
        - **Score 5:** The business idea is entirely feasible, demonstrating a high degree of accuracy and alignment with the provided targets. It is highly relevant, complete, and excels in scalability, profitability, and uniqueness, offering a novel and insightful business proposition that stands out in the market.
        
        **Original Question:** '{question}'  
        **Given Answer to be Evaluated:** '{answer}'  
        
        ### OUTPUT FORMAT:  
        
        **Score:** _  
        **Explanation:** _  
        """,

    "q6": f"""  
        You are a Math Expert.  Use a scale from 1 to 5 based on the following criteria: accuracy on the topic, funniness, relevance, completeness, and uniqueness of the answer.  
        
        ### Evaluation Criteria:  
        
        **Answer Correctness:**  
        
        - **Score 1:** The final answer is completely off the mark, entirely irrelevant, or mathematically incorrect. It does not provide a percentage or is far from the correct value, demonstrating a lack of understanding of the problem.
        - **Score 2:** The final answer shows some understanding of the problem but includes significant mathematical inaccuracies or irrelevant elements. The percentage is partially correct but lacks precision or completeness, demonstrating a flawed approach.
        - **Score 3:** The final answer accurately reflects many aspects of the problem and aligns with known mathematical principles. The percentage is relevant and suitable but may lack significant elements such as clarity or precision. It is complete in many ways but lacks depth of mathematical rigor.
        - **Score 4:** The final answer is predominantly correct, providing a well-calculated percentage with one or more minor inaccuracies. The answer is mostly complete, showing good levels of clarity and precision, adding value to the overall problem-solving approach.
        - **Score 5:** The final answer is spot on, demonstrating a high degree of accuracy and relevance to the problem. The percentage is highly precise, complete, and excels in clarity, offering a mathematically rigorous and correct solution.
        
        **Original Question:** '{question}'  
        **Given Answer to be Evaluated:** '{answer}'  
        
        ### OUTPUT FORMAT:  
        
        **Score:** _  
        **Explanation:** _  
        """  
        }

        # Define the prompt template  
        system_message = system_prompt['master']

        # Define the template with escaped curly braces for context and question
        TEMPLATE = master_prompt[q]
    
        user_message = ("user", TEMPLATE)  
        return [system_message, user_message] 

# COMMAND ----------

# Main program
if __name__ == "__main__":
    # Activating Main Class
    main = JudgeMaster(uc_catalog = uc_catalog, 
                    uc_schema = uc_schema, 
                    uc_table = uc_table)
    main.create_judge_evaluations()
