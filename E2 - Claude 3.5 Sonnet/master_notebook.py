# Databricks notebook source
# MAGIC %md
# MAGIC ## Anthropic Claude 3.5 Sonnet
# MAGIC ### The solution is using Mosaic AI external model serving endpoint

# COMMAND ----------

# MAGIC %md
# MAGIC _Claude 3.5 Sonnet, the latest addition to the Claude model family, sets new industry standards in intelligence and performance with 200k context window. It outperforms its predecessor, Claude 3 Opus, in evaluations of reasoning, knowledge, and coding proficiency, while maintaining cost-effective pricing. Available on Claude.ai, the Claude iOS app, and via major cloud platforms, it offers significant improvements in speed and understanding of complex instructions. Ideal for tasks like customer support and workflow orchestration, Claude 3.5 Sonnet demonstrates advanced capabilities in writing, editing, and executing code. This model is poised to redefine industry benchmarks with its exceptional performance and versatility._
# MAGIC
# MAGIC **API Pricing model (Pay-per-token)**
# MAGIC * Input: $3 per 1M tokens
# MAGIC * Output: $15 per 1M tokens
# MAGIC
# MAGIC https://console.anthropic.com/  Free 5$ credit for the new users.

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
# MAGIC %run "../src/Create Rag Dataset" $file_path="../src/raw/rag_dataset2.txt"

# COMMAND ----------

# DBTITLE 1,Create Model Endpoint for Anthropic
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

# DBTITLE 1,Delete Model Endpoint for Anthropic
# MAGIC %run "./Delete Model Endpoint"
