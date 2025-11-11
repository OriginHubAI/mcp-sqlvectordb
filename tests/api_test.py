      
import requests
import json
import os
import dotenv

dotenv.load_dotenv()

API_KEY = os.getenv("TEXT2VEC_SQL_API")
URL = os.getenv("TEXT2VEC_SQL_URL")


# 完整的提示符 (与 Gradio 示例相同)
example = """You are a senior SQL engineer. Your task is to generate a single, correct, and executable SQL query to answer the user's question based on the provided database context.
## INSTRUCTIONS
1.  **Backend Adherence**: The query MUST be written for the `myscale` database backend. This is a strict requirement.
2.  **Follow Special Notes**: You MUST strictly follow all syntax, functions, or constraints described in the [Database Backend Notes]. Pay extremely close attention to this section, as it contains critical, non-standard rules.
3.  **Schema Integrity**: The query MUST ONLY use the tables and columns provided in the [Database Schema]. Do not invent or guess table or column names.
4.  **Answer the Question**: The query must directly and accurately answer the [Natural Language Question].
5.  **Output Format**: Enclose the final SQL query in a single Markdown code block formatted for SQL (` ```sql ... ``` `).
6.  **Embedding Match**: If the [EMBEDDING_MODEL_NAME] parameter is a valid string (e.g., 'intfloat/E5-Mistral-7B-Instruct'), you MUST generate a query that includes the WHERE [EMBEDDING_COLUMN_NAME] MATCH lembed(...) clause for vector search. Otherwise, if embedding model name below the [EMBEDDING MODEL NAME] is None, , you MUST generate a standard SQL query that OMITS the entire MATCH lembed(...) clause. The query should not perform any vector search.
7.  **Embedding Name**: If a value is provided for the parameter `[EMBEDDING_MODEL_NAME]`, your generated query must contain a `lembed` function call. The first parameter to the `lembed` function MUST be the exact value of `[EMBEDDING_MODEL_NAME]`, formatted as a string literal (enclosed in single quotes). For example, if `[EMBEDDING_MODEL_NAME]` is `laion/CLIP-ViT-B-32-laion2B-s34B-b79K`, the generated SQL must include `MATCH lembed('laion/CLIP-ViT-B-32-laion2B-s34B-b79K', ...)`.
## DATABASE CONTEXT
[DATABASE BACKEND]:
myscale
[DATABASE SCHEMA]:
CREATE TABLE CAMPAIGN_RESULTS (
  `result_id` Nullable(Int64),
  `campaign_id` Nullable(Int64),
  `territory_id` Nullable(Int64),
  `menu_item_id` Nullable(Int64),
  `sales_increase_percentage` Nullable(Float64),
  `customer_engagement_score` Nullable(Float64),
  `feedback_improvement` Nullable(Float64)
);
CREATE TABLE CUSTOMERS (
  `customer_id` Nullable(Int64),
  `customer_name` Nullable(String),
  `email` Nullable(String),
  `phone_number` Nullable(String),
  `loyalty_points` Nullable(Int64)
);
CREATE TABLE CUSTOMER_FEEDBACK (
  `feedback_id` Nullable(Int64),
  `menu_item_id` Nullable(Int64),
  `customer_id` Nullable(Int64),
  `feedback_date` Nullable(String),
  `rating` Nullable(Float64),
  `comments` Nullable(String),
  `feedback_type` Nullable(String),
  `comments_embedding` Array(Float32)
);
CREATE TABLE INGREDIENTS (
  `ingredient_id` Nullable(Int64),
  `name` Nullable(String),
  `description` Nullable(String),
  `supplier_id` Nullable(Int64),
  `cost_per_unit` Nullable(Float64),
  `description_embedding` Array(Float32)
);
CREATE TABLE MARKETING_CAMPAIGNS (
  `campaign_id` Nullable(Int64),
  `campaign_name` Nullable(String),
  `start_date` Nullable(String),
  `end_date` Nullable(String),
  `budget` Nullable(Float64),
  `objective` Nullable(String),
  `territory_id` Nullable(Int64)
);
CREATE TABLE MENU_CATEGORIES (
  `category_id` Nullable(Int64),
  `category_name` Nullable(String),
  `description` Nullable(String),
  `parent_category_id` Nullable(Int64),
  `description_embedding` Array(Float32)
);
CREATE TABLE MENU_ITEMS (
  `menu_item_id` Nullable(Int64),
  `territory_id` Nullable(Int64),
  `name` Nullable(String),
  `price_inr` Nullable(Float64),
  `price_usd` Nullable(Float64),
  `price_eur` Nullable(Float64),
  `category_id` Nullable(Int64),
  `menu_type` Nullable(String),
  `calories` Nullable(Int64),
  `is_vegetarian` Nullable(Int64),
  `promotion_id` Nullable(Int64)
);
CREATE TABLE MENU_ITEM_INGREDIENTS (
  `menu_item_id` Nullable(Int64),
  `ingredient_id` Nullable(Int64),
  `quantity` Nullable(Float64),
  `unit_of_measurement` Nullable(String)
);
CREATE TABLE PRICING_STRATEGIES (
  `strategy_id` Nullable(Int64),
  `strategy_name` Nullable(String),
  `description` Nullable(String),
  `territory_id` Nullable(Int64),
  `effective_date` Nullable(String),
  `end_date` Nullable(String),
  `description_embedding` Array(Float32)
);
CREATE TABLE PROMOTIONS (
  `promotion_id` Nullable(Int64),
  `promotion_name` Nullable(String),
  `start_date` Nullable(String),
  `end_date` Nullable(String),
  `discount_percentage` Nullable(Float64),
  `category_id` Nullable(Int64),
  `territory_id` Nullable(Int64)
);
CREATE TABLE SALES_DATA (
  `sale_id` Nullable(Int64),
  `menu_item_id` Nullable(Int64),
  `territory_id` Nullable(Int64),
  `sale_date` Nullable(String),
  `quantity_sold` Nullable(Int64),
  `total_revenue` Nullable(Float64),
  `discount_applied` Nullable(Float64),
  `customer_id` Nullable(Int64)
);
CREATE TABLE SALES_FORECAST (
  `forecast_id` Nullable(Int64),
  `menu_item_id` Nullable(Int64),
  `territory_id` Nullable(Int64),
  `forecast_date` Nullable(String),
  `forecast_quantity` Nullable(Int64),
  `forecast_revenue` Nullable(Float64),
  `prediction_accuracy` Nullable(Float64)
);
CREATE TABLE SUPPLIERS (
  `supplier_id` Nullable(Int64),
  `supplier_name` Nullable(String),
  `contact_email` Nullable(String),
  `phone_number` Nullable(String),
  `address` Nullable(String)
);
CREATE TABLE TERRITORIES (
  `territory_id` Nullable(Int64),
  `territory_name` Nullable(String),
  `region` Nullable(String),
  `contact_email` Nullable(String),
  `local_tax_rate` Nullable(Float64),
  `currency_code` Nullable(String)
);
CREATE TABLE USERS (
  `user_id` Nullable(Int64),
  `user_name` Nullable(String),
  `email` Nullable(String),
  `role_id` Nullable(Int64),
  `territory_id` Nullable(Int64)
);
CREATE TABLE USER_ROLES (
  `role_id` Nullable(Int64),
  `role_name` Nullable(String),
  `description` Nullable(String),
  `permissions` Nullable(String),
  `description_embedding` Array(Float32)
);
[DATABASE BACKEND NOTES]:
There are a few requirements you should comply with in addition:
1. When generating SQL queries, you should prioritize utilizing K-Nearest Neighbor (KNN) searches whenever contextually appropriate. However, you must avoid unnecessary/forced KNN implementations for:
-- Traditional relational data queries (especially for columns like: id, age, price).
-- Cases where standard SQL operators (equality, range, or aggregation functions) are more efficient and semantically appropriate.
2. Only columns with a vector type (like: Array(Float32) or FixedString) support KNN queries. The names of these vector columns often end with "_embedding". You can perform KNN searches when the column name you need to query ends with "_embedding" or is otherwise identified as a vector column.
3. In MyScale, vector similarity search is performed using the `distance()` function. You must explicitly calculate the distance in the SELECT clause and give it an alias, typically "AS distance". This distance alias will not be implicitly generated.
4. **MyScale Specific Syntax:** When providing a query vector (the "needle") for an `Array(Float32)` column, at least one number in the array *must* contain a decimal point (e.g., `[3.0, 9, 45]`). This prevents the database from misinterpreting the vector as `Array(UInt64)`, which would cause an error.
5. The `lembed` function is used to transform a string into a semantic vector. This function should be used within a WITH clause to define the reference vector. The lembed function has two parameters: the first is the name of the embedding model used (default value: '{embedding_model}'), and the second is the string content to embed. The resulting vector should be given an alias in the WITH clause.
6. You must generate plausible and semantically relevant words or sentences for the second parameter of the `lembed` function based on the column's name, type, and comment. For example, if a column is named `product_description_embedding` and its comment is "Embedding of the product's features and marketing text", you could generate text like "durable and waterproof outdoor adventure camera".
7. Every KNN search query MUST conclude with "ORDER BY distance LIMIT N" to retrieve the top-N most similar results.  The LIMIT clause is mandatory for performing a KNN search and ensuring predictable performance.
8. When combining a vector search with JOIN operations, the standard `WHERE` clause should be used to apply filters from any of the joined tables.  The `ORDER BY distance LIMIT N` clause is applied after all filtering and joins are resolved.
9. A SELECT statement should typically be ordered by a single distance calculation to perform one primary KNN search. However, subqueries can perform their own independent KNN searches, each with its own WITH clause, distance calculation, and `ORDER BY distance LIMIT N` clause.
## Example of a MyScale KNN Query
DB Schema: Some table on `articles` with a column `abstract_embedding` `Array(Float32)`.
Query Task: Identify the article ID of the single most relevant article discussing innovative algorithms in graph theory.
Generated SQL:
```
    WITH
        lembed('all-MiniLM-L6-v2', 'innovative algorithms in graph theory.') AS ref_vec_0   
    SELECT id, distance(articles.abstract_embedding, ref_vec_0) AS distance
    FROM articles
    ORDER BY distance
    LIMIT 1;
```
[EMBEDDING MODEL NAME]:
intfloat/E5-Mistral-7B-Instruct
## NATURAL LANGUAGE QUESTION
In vector searches, the `MATCH` operator performs an approximate nearest neighbor (ANN) search, which identifies items based on their similarity to a given vector. The `lembed()` function is used to convert text phrases into vector representations using a specific model, in this case, `intfloat/E5-Mistral-7B-Instruct`. This helps in finding items that align closely with the concept of "Popular menu items based on sales." The parameter `k = 5` specifies that only the top 5 categories, which are most similar in terms of the embedding, should be considered. The similarity is determined by calculating the Euclidean distance between vectors, where a smaller distance indicates higher similarity.
Can you unveil the crown jewel of our vegetarian delights, the one that has soared to the top of the sales charts from the elite circle of our most cherished categories this year?
Let's think step by step!
"""

if __name__ == "__main__":
    # example = "Hi"

    response = requests.post(
        URL,
        json={"text_input": example}, headers={"Authorization": f"Bearer {API_KEY}"}
    )

    if response.status_code == 200:
        print("Get Response Successfully")
        print(response.json()["result"])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Response:
# Get Response Successfully
# To address the question, we need to identify the top vegetarian menu item that has performed the best in terms of sales from the most popular categories. Here's a step-by-step breakdown of how to construct the SQL query:

# 1. **Identify the Most Popular Categories**: 
#    - We need to find the top 5 categories based on their similarity to the concept "Popular menu items based on sales."
#    - This involves using the `lembed` function to generate a reference vector for the concept and then calculating the distance between this vector and the `description_embedding` of each category.
#    - We will use a `WITH` clause to define the reference vector and then select the top 5 categories based on the smallest distance.

# 2. **Filter Vegetarian Menu Items**:
#    - We need to filter the menu items to only include those that are vegetarian (`is_vegetarian = 1`).

# 3. **Join with Sales Data**:
#    - We need to join the filtered vegetarian menu items with the `SALES_DATA` table to get the sales information for these items.

# 4. **Aggregate Sales Data**:
#    - We will aggregate the sales data to calculate the total quantity sold and total revenue for each vegetarian menu item.

# 5. **Order and Limit the Results**:
#    - Finally, we will order the results by total revenue in descending order and limit the output to the top item.

# Here is the SQL query that implements the above steps:

# ```sql
# WITH
#     lembed('intfloat/E5-Mistral-7B-Instruct', 'Popular menu items based on sales') AS ref_vec_0,

# PopularCategories AS (
#     SELECT category_id, distance(description_embedding, ref_vec_0) AS distance
#     FROM MENU_CATEGORIES
#     ORDER BY distance
#     LIMIT 5
# ),

# VegetarianMenuItems AS (
#     SELECT menu_item_id, name, category_id
#     FROM MENU_ITEMS
#     WHERE is_vegetarian = 1
# ),

# SalesData AS (
#     SELECT vm.menu_item_id, vm.name, SUM(sd.quantity_sold) AS total_quantity_sold, SUM(sd.total_revenue) AS total_revenue
#     FROM VegetarianMenuItems vm
#     JOIN SALES_DATA sd ON vm.menu_item_id = sd.menu_item_id
#     JOIN PopularCategories pc ON vm.category_id = pc.category_id
#     GROUP BY vm.menu_item_id, vm.name
# )

# SELECT name, total_revenue
# FROM SalesData
# ORDER BY total_revenue DESC
# LIMIT 1;
# ```