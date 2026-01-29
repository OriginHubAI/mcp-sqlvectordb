# MCP SQLVectorDB Benchmark

This benchmark is designed to evaluate the performance of MCP SQLVectorDB models on Text2VectorSQL tasks. It provides comprehensive metrics to assess the accuracy, recall, and overall quality of SQL generation from natural language questions.

## How to Run this Benchmark

### Prerequisites

Before running the benchmark, ensure you have:
- Python 3.8+
- Dify API access with a valid API key
- LLM API access with a valid API key
- MyScale database access
- Required Python packages (install via `pip install -r requirements.txt`)

### Configuration

The benchmark requires the following configuration, which can be modified in `.env` file:

```
# Dify API配置
API_KEY=your-api-key-here
DIFY_URL=https://api.dify.ai/v1/chat-messages

# MyScale数据库配置
MYSCALE_HOST=your-myscale-host
MYSCALE_PORT=8123
MYSCALE_USER=your-myscale-username
MYSCALE_PASSWORD=your-myscale-password
MYSCALE_DATABASE=your-database-name

# LLM API配置
LLM_API_URL=your-llm-api-url
LLM_API_KEY=your-llm-api-key
LLM_MODEL=your-llm-model
LLM_EVALUATION_ENABLED=True
```

### Running the Benchmark

You can run the benchmark using the following command:

```bash
cd benchmark
python benchmark.py [options]
```

#### Command Line Options

- `--dataset`: Path to the dataset file (default: `./data/results/test/olympics/olympics_qs.json`)
- `--output`: Path to save the results (default: `./results`)
- `--text-num`: Number of samples to test (default: all)
- `--no-llm`: Disable LLM evaluation (default: enabled)

#### Examples

1. Run with default settings:
   ```bash
   python benchmark.py
   ```

2. Run with custom dataset and output path:
   ```bash
   python benchmark.py --dataset ./custom_dataset.json --output ./custom_results
   ```

3. Run with only 50 samples and without LLM evaluation:
   ```bash
   python benchmark.py --text-num 50 --no-llm
   ```

### Output

The benchmark generates a JSON file with timestamp in the output directory (e.g., `benchmark_results-20260114-182456.json`). The output includes:

- Summary statistics (total samples, success rate, average metrics)
- Detailed results for each sample (question, standard SQL, predicted SQL, evaluation metrics)

## Evaluation

The benchmark uses a comprehensive set of metrics to evaluate Text2SQL performance:

### 1. Exact Match Metrics

- **Exact Match**: Whether the predicted SQL exactly matches any of the ground truth SQL statements

### 2. Set Metrics

- **Precision**: The proportion of correctly predicted results among all predicted results
- **Recall**: The proportion of correctly predicted results among all ground truth results
- **F1 Score**: The harmonic mean of precision and recall

### 3. Ranking Metrics

- **MAP (Mean Average Precision)**: Average precision across all queries, considering the order of results
- **MRR (Mean Reciprocal Rank)**: Average of the reciprocals of the ranks of the first relevant result
- **NDCG (Normalized Discounted Cumulative Gain)**: Measures the ranking quality by discounting results further down the list

### 4. LLM-Based Evaluation

- **ACC_SQL**: Binary score (0/1) for SQL skeleton correctness evaluated by LLM
- **ACC_Vec**: Binary score (0/1) for vector component correctness evaluated by LLM
- **LLM Overall**: Average of ACC_SQL and ACC_Vec scores

### Evaluation Process

1. **SQL Extraction**: Extract SQL statements from MCP SQLVectorDB's natural language responses
2. **SQL Execution**: Execute both standard and predicted SQL on the MyScale database
3. **Result Comparison**: Compare execution results using set and ranking metrics
4. **LLM Evaluation**: (Optional) Use GPT-4o to evaluate SQL semantic correctness

## Environment

### System Requirements

- **Operating System**: Linux/macOS/Windows
- **Architecture**: x86-64 (recommended)
- **Memory**: 8GB+ RAM
- **Storage**: 1GB+ free disk space

### Python Dependencies

- `requests`: For API calls
- `clickhouse_connect`: For connecting to MyScale database
- `argparse`: For command-line argument parsing
- `json`: For data handling
- `os`: For file system operations
- `datetime`: For timestamp generation

### Database Requirements

- **Database**: MyScale
- **Vector Index**: Pre-built vector indexes for efficient similarity search
- **Tables**: Database schema should match the test dataset requirements

### API Requirements

- **API**: Access to MCP SQLVectorDB's API with Text2SQL capabilities
- **LLM API**: Access to LLM model API with a valid API key
- **OpenAI API**: (Optional) For LLM-based evaluation using GPT-4o

## Troubleshooting

### Common Issues

1. **API Connection Errors**: Verify your API key and network connectivity
2. **LLM API Errors**: Verify your LLM API key and network connectivity
3. **Database Errors**: Check MyScale connection parameters and database permissions
4. **SQL Execution Failures**: Ensure the database schema matches the expected structure
5. **LLM Evaluation Failures**: Verify OpenAI API access if using LLM evaluation

### Logging

Detailed logs are generated during benchmark execution, including:
- SQL execution results
- Evaluation metrics
- Error messages

Logs can be found in the `log/` directory for debugging purposes.

## License

This benchmark is provided for evaluation purposes only. Please contact the maintainers for licensing information.

## Contact

For questions or issues, please contact the development team.