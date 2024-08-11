# Databricks notebook source
# MAGIC %%capture
# MAGIC !pip install -r ../requirements.txt
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from langchain_community.chat_models import ChatDatabricks
from langchain_community.vectorstores import DatabricksVectorSearch
from databricks.vector_search.client import VectorSearchClient
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from openai import OpenAI
import openai
import mlflow
import time
import ast
import requests
import logging
import datetime
import json
import re
import os
import pandas as pd

from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, StringType
import pyspark.sql.functions as f
from src import get_weather

print("Libraries are now imported")
