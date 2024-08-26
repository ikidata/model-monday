# Databricks notebook source
# MAGIC %md
# MAGIC ## Mistral Mixtral 8x7b Instruct
# MAGIC ### The solution is using Mosaic AI external model serving endpoint

# COMMAND ----------

# MAGIC %md
# MAGIC _Mixtral 8x7B, released on December 11, 2023, is a high-quality sparse mixture of experts model (SMoE) with open weights, licensed under Apache 2.0. It can handle a context of 32k tokens and supports English, French, Italian, German, and Spanish. The model excels in code generation and can be fine-tuned into an instruction-following model, achieving a score of 8.3 on MT-Bench._
# MAGIC
# MAGIC _Mixtral is a decoder-only network where each feedforward block selects from 8 distinct parameter groups. A router network chooses two groups (the “experts”) per token per layer, combining their output additively. This approach increases the model's parameter count to 46.7B while only using 12.9B parameters per token, maintaining the speed and cost of a 12.9B parameter model. Mixtral is pre-trained on data from the open Web, with experts and routers trained simultaneously._
# MAGIC
# MAGIC **API Pricing model (Provisioned Throughput)**
# MAGIC * Max Provisioned Throughput 1700
# MAGIC * 131.2 DBU / h

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
# MAGIC %run "../src/Create Rag Dataset" $file_path="../src/raw/rag_dataset3.txt"

# COMMAND ----------

# DBTITLE 1,Create Model Endpoint for Mixtral
# MAGIC %run "./Create Model Endpoint"

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

# COMMAND ----------

# DBTITLE 1,Delete Model Endpoint for Mixtral
# MAGIC %run "./Delete Model Endpoint"
