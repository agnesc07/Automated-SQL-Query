# Automated-SQL-Query
AI-powered SQL Agent using LangChain and OpenAI for database querying.

An AI-powered SQL Agent that enables users to interact with relational databases through natural language queries. Built with Python, LangChain, and OpenAI, this project translates user questions into SQL queries and retrieves relevant information from a MySQL database.

Project Overview

This project explores the implementation of a Large Language Model (LLM)-powered SQL Agent to simplify database interaction.

Instead of manually writing SQL queries, users can ask questions in natural language. The AI Agent interprets the request, generates SQL queries, executes them against the connected database, and returns results in a human-readable format.

The system was developed as part of a Data Analyst internship project, focusing on improving database accessibility and reducing manual SQL query development and debugging efforts.

Key Features

Natural Language to SQL: Converts natural language questions into SQL queries.

Database Integration: Connects to MySQL databases for structured data retrieval.

LLM-Powered Query Generation: Uses OpenAI language models to interpret user requests and generate SQL statements.

Multi-Table Query Handling: Supports queries involving multiple tables and SQL joins.

Context-Aware Interaction: Maintains conversational context to support follow-up questions.

Date Normalization: Handles different date expressions and formats in user queries.

Multilingual Query Understanding: Supports natural language questions with varying language patterns.

Read-Only Database Access: Designed for data retrieval without modifying database records.

Technology Stack

Technology

Purpose

Python

Core programming language

LangChain

AI Agent orchestration

OpenAI API

Natural language understanding and SQL generation

MySQL

Relational database

SQLAlchemy

Database connectivity

SQLDatabase

Database schema inspection and integration

System Architecture

The system follows this workflow:

User Input: User submits a question in natural language.

LLM Processing: The language model interprets the question and identifies the required data.

SQL Generation: The SQL Agent generates an appropriate SQL query.

Query Execution: The generated query is executed against the connected MySQL database.

Result Processing: Retrieved data is processed and interpreted.

Natural Language Response: The system returns an understandable response to the user.

Project Implementation

The main implementation involves:

Configuring the OpenAI language model.

Establishing database connections using SQLAlchemy.

Integrating database schema information with LangChain.

Creating an SQL Agent for natural language-based database querying.

Handling SQL query generation, execution, and response interpretation.

Supporting multi-table queries and contextual follow-up interactions.

Results & Impact

The implementation demonstrated the potential of LLM-powered SQL Agents to improve database querying workflows.

Reduced SQL query execution and debugging time by approximately 60%.

Simplified access to structured database information through natural language interaction.

Improved handling of complex queries involving multiple tables and contextual requirements.

Reduced dependency on manually writing SQL queries for routine data retrieval.
