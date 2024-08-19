# Databricks notebook source
# MAGIC %md
# MAGIC Blog texts: 
# MAGIC * https://www.databricks.com/blog/data-ai-summit-2024-executive-summary-data-leaders
# MAGIC * https://www.databricks.com/blog/supernovas-black-holes-and-streaming-data

# COMMAND ----------

def check_catalog_and_schema_exists(catalog_name: str, schema_name: str, table_name: str) -> None:  
    '''
    This function checks if a specified catalog and schema exist in Databricks Unity Catalog and ensures that a specified table does not exist within that schema. It raises an AssertionError if any of the conditions are not met.
    '''
    # Assert that all three lists are not empty
    assert uc_catalog and uc_schema and uc_table, "One or more lists (catalog, schema, table) are empty."

    # List all catalogs  
    catalogs = spark.sql("SHOW CATALOGS").collect()  
      
    # Check if the desired catalog is in the list  
    catalog_exists = any(row.catalog == catalog_name for row in catalogs)  
      
    # Assert and print appropriate message for catalog  
    assert catalog_exists, f"Catalog '{catalog_name}' does not exist. Please check you Catalog value."  
      
    # List all schemas in the specific catalog  
    schemas = spark.sql(f"SHOW SCHEMAS IN {catalog_name}").collect()  
        
    # Check if the desired schema is in the list  
    schema_exists = any(row.databaseName == schema_name for row in schemas)  
        
    # Assert and print appropriate message for schema  
    assert schema_exists, f"Schema '{schema_name}' in catalog '{catalog_name}' does not exist. Please check you Schema value."  

    # List all tables in the specific schema  
    tables = spark.sql(f"SHOW TABLES IN {catalog_name}.{schema_name}").collect()  
              
    # Check if the desired table is in the list  
    table_exists = any(row.tableName == table_name for row in tables)  
        
    # Assert that the table should not exist and print appropriate message  
    assert not table_exists, f"Table '{table_name}' in schema '{schema_name}' in catalog '{catalog_name}' should not exist."  



def load_raw_text(file_path):  
    '''
    This function loads raw text from a specified file path, reading the file with UTF-8 encoding and returning its content.
    ''' 
    with open(file_path, 'r', encoding='utf-8') as file:  
        return file.read()  
  
def split_text_into_documents(text, max_words_per_doc=200, overlap=50):  
    '''
    This function splits text into documents of up to max_words_per_doc words, with an overlap of overlap words between consecutive documents. 
    '''  
    words = text.split()  
    documents = []  
    start = 0  
      
    while start < len(words):  
        end = start + max_words_per_doc  
        document = words[start:end]  
        documents.append(' '.join(document))  
        start += max_words_per_doc - overlap  
      
    return documents  
  
def create_dataset(documents):  
    '''
    This function creates a dataset where each document is assigned a unique identifier.
    '''
    dataset = []  
    for i, doc in enumerate(documents):  
        dataset.append({  
            'id': f'doc_{i+1}',  
            'text': doc  
        })  
    return dataset  

def read_document(dataset, index):
    '''
    Read one document from the dataset at the given index.
    '''
    if index < len(dataset):
        return dataset[index]
    else:
        return None
    
def create_dataframe(uc_catalog: str, uc_schema: str, uc_table: str, dataset: list):
    '''
    This function creates a DataFrame with a specified schema, reads and appends each document from a dataset, and saves the DataFrame as a table in the specified catalog and schema.
    '''
    
    schema = StructType([
        StructField('id', StringType(), nullable=True),
        StructField('text', StringType(), nullable=True)
    ])
    df = spark.createDataFrame([], schema=schema)

    # Read and append each document to the DataFrame
    index = 0
    while True:
        document = read_document(dataset, index)
        if document is None:
            break
        row = Row(id=document['id'], text=document['text'])
        df = df.union(spark.createDataFrame([row], schema=schema))
        index += 1
    df.write.mode('overwrite').option("overwriteSchema", "true").saveAsTable(f"{uc_catalog}.{uc_schema}.{uc_table}_rag_data")
    print(f"Dataset saved to delta table '{uc_catalog}.{uc_schema}.{uc_table}_rag_data' successfully. Number of documents: {len(dataset)}")  
    spark.sql(f"ALTER TABLE {uc_catalog}.{uc_schema}.{uc_table}_rag_data SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    print(f"Enabled Change Data Feed to delta table '{uc_catalog}.{uc_schema}.{uc_table}_rag_data' successfully.")  

# COMMAND ----------

file_path = dbutils.widgets.get("file_path")

# Main program
if __name__ == "__main__":
    check_catalog_and_schema_exists(uc_catalog, 
                                    uc_schema, 
                                    uc_table) 
    raw_text = load_raw_text(file_path) 
    split_text = split_text_into_documents(raw_text)
    dataset = create_dataset(split_text)
    create_dataframe(uc_catalog, 
                     uc_schema, 
                     uc_table, 
                     dataset)

