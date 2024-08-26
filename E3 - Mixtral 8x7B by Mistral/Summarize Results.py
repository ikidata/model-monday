# Databricks notebook source
# MAGIC %%capture
# MAGIC from IPython.display import display  
# MAGIC
# MAGIC df_raw = (spark.read.table(f'{uc_catalog}.{uc_schema}.{uc_table}_results')
# MAGIC            .withColumn('question', f.when(f.col('question') == 'qr', 'RAG')
# MAGIC                        .when(f.col('question') == 'qf', 'FUNCTION') 
# MAGIC                        .otherwise(f.col('question')))
# MAGIC                        .orderBy('question'))
# MAGIC df = df_raw.toPandas()
# MAGIC
# MAGIC df['Questions'] = df['question'].str.upper() + " - " + df['input_prompt']
# MAGIC df['Mixtral 8x7b'] = df['score']
# MAGIC df['Model 2'] = ''
# MAGIC df['Model 3'] = ''
# MAGIC df['Model 4'] = ''
# MAGIC df['Model 5'] = ''
# MAGIC
# MAGIC # Excluding function calling scoring
# MAGIC df_cleaned = df[df['question'] != 'q_function']
# MAGIC
# MAGIC # Adding Overall situation row  
# MAGIC df = df.sort_values(by=['Questions'])
# MAGIC df['Mixtral 8x7b speed'] = df['time_s'].astype(str) + "s" 
# MAGIC
# MAGIC situation_df = pd.DataFrame([{'Questions': 'Overall situation:', 'Mixtral 8x7b': str(round(df_cleaned['Mixtral 8x7b'].astype(float).mean(), 2)), 'time_s': ""}])
# MAGIC speed_df = pd.DataFrame([{'Questions': ' Avg Speed:', 'Mixtral 8x7b': str(round(df_cleaned['time_s'].astype(float).mean(), 2)) + "s", 'time_s': ""}])
# MAGIC df = pd.concat([df, situation_df, speed_df], ignore_index=True)
# MAGIC
# MAGIC df.fillna('', inplace=True)
# MAGIC df = df[['Questions', 'Mixtral 8x7b', 'Mixtral 8x7b speed', 'Model 2', 'Model 3', 'Model 4', 'Model 5']]
# MAGIC
# MAGIC # Replacing function calling value
# MAGIC df.loc[df['Questions'] == "Q_FUNCTION - What's the current weather in Helsinki?", 'Mixtral 8x7b'] = '❌'  
# MAGIC
# MAGIC styled_df = df.style.set_properties(  
# MAGIC     **{'text-align': 'center', 'padding': '10px'}  
# MAGIC ).set_properties(  
# MAGIC     subset=['Questions'], **{'text-align': 'left'}  
# MAGIC ).set_table_styles(  
# MAGIC     [{'selector': 'th', 'props': [('padding', '10px')]},  
# MAGIC      {'selector': 'td', 'props': [('padding', '10px')]}]  
# MAGIC ).hide(axis='index') 
# MAGIC
# MAGIC # Function to apply bold styling
# MAGIC def bold_first_row(val):  
# MAGIC     # Check if the cell is in the first row  
# MAGIC     if val.name == 8:  
# MAGIC         return ['font-weight: bold' for _ in val]  
# MAGIC     return ['' for _ in val]  
# MAGIC   
# MAGIC # Apply CSS styling to Overall situation row    
# MAGIC styled_df = styled_df.apply(bold_first_row, axis=1)  

# COMMAND ----------

display(styled_df)  

# COMMAND ----------

df_raw.display()
