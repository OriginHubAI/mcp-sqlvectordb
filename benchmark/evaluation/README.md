# VectorSQL Evaluation Framework

## Overview

The VectorSQL Evaluation Framework is a comprehensive toolset for evaluating the performance of VectorSQL queries generated from natural language questions. It provides a wide range of metrics to assess the accuracy, recall, and overall quality of SQL generation, particularly for vector databases.

## Features

### 1. Multi-metric Evaluation
- **Exact Match**: Checks if predicted SQL exactly matches any ground truth SQL
- **Set Metrics**: Calculates precision, recall, and F1 score based on result sets
- **Ranking Metrics**: Evaluates ranking quality with MAP, MRR, and NDCG
- **LLM-based Evaluation**: Uses large language models to assess SQL semantic correctness

### 2. Flexible Configuration
- Supports custom SQL execution functions
- Configurable LLM evaluation parameters
- Supports multiple database schemas
- Easy to integrate with existing systems

### 3. Robust Error Handling
- Handles empty result sets gracefully
- Provides detailed error messages
- Supports various edge cases

## Evaluation Process

The evaluation framework follows a structured process to assess VectorSQL queries:

1. **SQL Execution**: Executes both standard (ground truth) SQL and predicted SQL
2. **Result Collection**: Collects results from both executions
3. **Metric Calculation**: Computes various evaluation metrics
4. **LLM Evaluation**: (Optional) Performs semantic evaluation using LLM
5. **Result Compilation**: Returns comprehensive evaluation results

## Key Functions

### `evaluate_with_metrics`
Main evaluation function that orchestrates the entire evaluation process.

```python
def evaluate_with_metrics(
    run_sql_func,  # Function to execute SQL
    nl_question: str,  # Natural language question
    standard_sql: str,  # Standard SQL
    predicted_sql: str,  # Predicted SQL
    db_schema: str = '',  # Database schema
    enable_llm: bool = False  # Whether to enable LLM evaluation
) -> Dict[str, Any]:
    # Evaluation logic
```

### Metric Calculation Functions

#### Exact Match Metrics
- `calculate_exact_match_any_gt_with_columns`: Checks exact match against any ground truth

#### Set Metrics
- `calculate_set_metrics_with_columns`: Calculates precision, recall, and F1 score

#### Ranking Metrics
- `calculate_ranking_metrics_with_columns`: Computes MAP, MRR, and NDCG

### LLM-based Evaluation

- `evaluate_vectorsql_with_llm`: Evaluates VectorSQL queries using LLM
- `calculate_llm_based_scores`: Extracts scores from LLM evaluation results

## API Configuration for LLM Evaluation

To enable LLM evaluation, configure the following environment variables in the `.env` file:

```
# LLM API Configuration
LLM_API_URL=your-llm-api-url
LLM_API_KEY=your-llm-api-key
LLM_MODEL=your-llm-model
LLM_EVALUATION_ENABLED=True
```

## Usage Example

```python
from evaluation.metrics import evaluate_with_metrics

# Define SQL execution function
def run_sql(sql):
    # Implementation to execute SQL and return results
    pass

# Evaluation parameters
nl_question = "Find the most similar products to 'smartphone'"
standard_sql = "SELECT * FROM products ORDER BY distance(description_embedding, lembed('model', 'smartphone')) LIMIT 5"
predicted_sql = "SELECT * FROM products WHERE description LIKE '%smartphone%' LIMIT 5"
db_schema = "products (id INT, name VARCHAR, description VARCHAR, description_embedding Array(Float32))"

# Run evaluation
results = evaluate_with_metrics(
    run_sql,
    nl_question,
    standard_sql,
    predicted_sql,
    db_schema,
    enable_llm=True
)

# Print results
print(results)
```

## Evaluation Results Format

The evaluation function returns a comprehensive dictionary with the following structure:

```json
{
    "golden_data": [/* Standard SQL results */],
    "golden_columns": [/* Standard SQL columns */],
    "exact_match": 0.0,
    "precision": 0.8,
    "recall": 0.6,
    "f1": 0.6857,
    "map": 0.7,
    "mrr": 1.0,
    "ndcg": 0.8,
    "llm_sql_skeleton_score": 1.0,
    "llm_vector_component_score": 0.0,
    "llm_overall_score": 0.5
}
```

## Error Handling

The framework handles various error cases:

- **EMPTY_GOLDEN_DATA**: Standard SQL returned no results
- **EMPTY_TEST_DATA**: Predicted SQL execution failed or returned no results
- **Invalid SQL syntax**: Handled by the SQL execution function

## Requirements

- Python 3.8+
- NumPy
- Requests
- PyParsing
- Dotenv

## License

Please refer to the project's main [LICENSE](../../LICENSE) file for license information.
