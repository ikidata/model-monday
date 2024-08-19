# Databricks notebook source
# MAGIC %md
# MAGIC ## Meta Llama 3.1 70B Instruct
# MAGIC ### The solution is using Mosaic AI model serving endpoint

# COMMAND ----------

# MAGIC %md
# MAGIC _Llama 3.1 is a state-of-the-art 70B parameter dense language model trained and released by Meta, distributed by AzureML via the AzureML Model Catalog. The model supports a context length of 128K tokens. The model is optimized for multilingual dialogue use cases and aligned with human preferences for helpfulness and safety. It is not intended for use in languages other than English. Meta Llama 3.1 is licensed under the Meta Llama 3.1 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved. Customers are responsible for ensuring compliance with applicable model licenses._
# MAGIC
# MAGIC **Pricing model (Pay-per-token)**
# MAGIC * Input: 14.286 DBUs per 1M tokens
# MAGIC * Output: 42.857 DBUs per 1M tokens
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC # Used cluster: 15.4 LTS ML Beta (includes Apache Spark 3.5.0, Scala 2.12)

# COMMAND ----------

# DBTITLE 1,Import libraries
# MAGIC %run "../src/Import libraries"

# COMMAND ----------

# DBTITLE 1,Fetch widgets
# Create widgets 
dbutils.widgets.text("uc_catalog", "", "Unity Catalog")
dbutils.widgets.text("uc_schema", "", "Unity Catalog Schema")
dbutils.widgets.text("uc_table", "", "Unity Catalog Table")

# Retrieve the values from the widgets
uc_catalog = dbutils.widgets.get("uc_catalog")
uc_schema = dbutils.widgets.get("uc_schema")
uc_table = dbutils.widgets.get("uc_table")

# COMMAND ----------

# DBTITLE 1,Create RAG dataset
# MAGIC %run "../src/Create Rag Dataset" $file_path="../src/raw/rag_dataset.txt"

# COMMAND ----------

# DBTITLE 1,Set up vector search endpoints
# MAGIC %run "../src/Create Vector Search Endpoints"

# COMMAND ----------

# DBTITLE 1,Create AI answers
# MAGIC %run "../src/Create AI answers"

# COMMAND ----------

# DBTITLE 1,LLM judge evaluates answers
# MAGIC %run "../src/Run LLM Judge"

# COMMAND ----------

# DBTITLE 1,Summarize results
# MAGIC %run "./Summarize Results"

# COMMAND ----------

# DBTITLE 1,Delete Vector Search Endpoint and Index
# MAGIC %run "../src/Delete Vector Search Endpoints"
