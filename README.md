# Model Monday
Ever wondered how the latest language models stack up against each other? Welcome to Model Monday, where we dive into the world of LLMs to see who comes out on top! For this showdown, we've enlisted Azure GPT-4o as our impartial judge, supported by a robust solution architecture built entirely on Databricks. Our evaluation includes six distinct questions, a Retrieval-Augmented Generation (RAG) assessment, and a function-calling task. All evaluations are conducted by our AI Judge, showcasing how this process can be automated for AI agents as well.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Table of Contents

- [Introduction](#introduction)
- [Solution Architecture](#Solution-Architecture)
- [Installation](#installation)
- [Usage](#usage)
- [More information](#More-information)

## Introduction

This repository contains the code used in Model Monday, fully optimized for execution in the Databricks environment. Please note that this is intended for demonstration purposes and includes multiple interesting features. However, the code can be easily modified for various use cases. Current Modules:
1) E1 - Llama 3.1.

## Solution Architecture
![architecture](./pictures/Model%20Monday%20Solution%20Architecture.png)

## Installation 

To use the Model Monday code, first clone the repository to your Databricks environment. Ensure you are using the 15.4 LTS ML Beta Cluster (includes Apache Spark 3.5.0, Scala 2.12). In the 'configs.json' file, update your component names, such as model endpoint names, if necessary. In the 'Run LLM Judge' notebook, add the required OS environment settings for Azure OpenAI configurations (needed for LLM Judge). 

## Usage
After completing the instruction steps, you can run and review all the code from the 'master_notebook'. This makes it easy to evaluate the functionality of each individual notebook. Remember to specify the correct Unity Catalog catalog, schema, and table name; the code will dynamically create new delta tables based on the master table name. If you forget to populate widget values, the code will pause. Once the widget values are populated, simply click "run all" and the remaining processes, including endpoint creation and deletion, is be automated.

## More information
To stay up-to-date with the latest developments: 
1) Follow Ikidata on LinkedIn: https://www.linkedin.com/company/ikidata/ 
2) Explore the solutions available on our website: https://www.ikidata.fi/solutions
