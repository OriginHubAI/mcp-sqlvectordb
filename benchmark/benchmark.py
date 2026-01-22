import json
import os
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from clickhouse_connect import get_client
from dotenv import load_dotenv

from evaluation.metrics import (
    extract_sql_from_dify_answer,
    evaluate_with_metrics
)
from tools.common import unify_lembed_clauses, get_dify_answer

# 加载环境变量
load_dotenv()


class Text2SQLBenchmark:
    """
    Text2SQL Benchmark 类，用于评估 Dify Text2SQL 模型的性能
    """
    
    def __init__(
        self,
        api_key: str,
        dify_url: str,
        myscale_host: str,
        myscale_port: int,
        myscale_user: str,
        myscale_password: str,
        myscale_database: str,
        output_path: str = "./results",
        llm_evaluation_enabled: bool = True,
        llm_model: str = "gpt-4o"
    ):
        """
        初始化 Text2SQLBenchmark 实例
        
        Args:
            api_key: Dify API 密钥
            dify_url: Dify API URL
            myscale_host: MyScale 数据库主机
            myscale_port: MyScale 数据库端口
            myscale_user: MyScale 数据库用户名
            myscale_password: MyScale 数据库密码
            myscale_database: MyScale 数据库名称
            output_path: 结果输出路径
            llm_evaluation_enabled: 是否启用 LLM 评估
            llm_model: LLM 模型名称
        """
        self.api_key = api_key
        self.dify_url = dify_url
        self.myscale_host = myscale_host
        self.myscale_port = myscale_port
        self.myscale_user = myscale_user
        self.myscale_password = myscale_password
        self.myscale_database = myscale_database
        self.output_path = output_path
        self.llm_evaluation_enabled = llm_evaluation_enabled
        self.llm_model = llm_model
        
        # 确保输出目录存在
        os.makedirs(self.output_path, exist_ok=True)
    
    def get_myscale_client(self):
        """
        获取 MyScale 数据库客户端
        
        Returns:
            MyScale 数据库客户端
        """
        return get_client(
            host=self.myscale_host,
            port=self.myscale_port,
            user=self.myscale_user,
            password=self.myscale_password,
            database=self.myscale_database
        )
    
    def run_sql_with_columns(self, sql: str) -> Tuple[List[tuple], List[str]]:
        """
        执行 SQL 查询并返回结果和列名
        
        Args:
            sql: SQL 查询语句
            
        Returns:
            (查询结果数据, 查询结果列名)
        """
        client = None
        try:
            client = self.get_myscale_client()
            result = client.query(sql)

            if not result.result_set:
                return [], []

            column_names = result.column_names
            
            distance_indices = [i for i, col in enumerate(column_names) if 'distance' in col.lower()]
            embedding_indices = [i for i, col in enumerate(column_names) if 'embedding' in col.lower()]
            exclude_indices = set(distance_indices + embedding_indices)
            data = []
            for row in result.result_set:
                filtered_row = tuple(value for idx, value in enumerate(row) if idx not in exclude_indices)
                data.append(filtered_row)
            filtered_columns = [col for idx, col in enumerate(column_names) if idx not in exclude_indices]

            return data, filtered_columns

        except Exception as e:
            print(f"    ❌ SQL执行失败: {str(e)}")
            return [], []
        finally:
            if client:
                client.close()
    
    def run_benchmark(self, dataset_path: str, text_num: Optional[int] = None) -> Dict[str, Any]:
        """
        运行 Text2SQL 基准测试
        
        Args:
            dataset_path: 数据集路径
            text_num: 测试样本数量（None 表示全部样本）
            
        Returns:
            基准测试结果
        """
        print("=" * 80)
        print("🚀 开始 Dify Text2SQL Benchmark 测试")
        print("=" * 80)

        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        if text_num:
            dataset = dataset[:text_num]
        total_samples = len(dataset)
        success_count = 0
        skipped_count = 0

        db_schema = dataset[0].get('schema', '') if dataset else ''

        results = []
        all_eval_results = []

        print(f"\n📊 数据集总样本数: {total_samples}\n")

        for i, sample in enumerate(dataset, 1):
            question = sample.get('question', '')
            standard_sql = sample.get('sql', '')

            if not question or not standard_sql:
                print(f"⚠️  样本 {i}: 缺少问题或SQL，跳过")
                continue

            print(f"\n{'='*80}")
            print(f"📝 样本 {i}/{total_samples}")
            print(f"问题: {question}")

            print("\n🤖 步骤1: 调用Dify API获取回答...")
            dify_answer = get_dify_answer(question, self.api_key, self.dify_url)
            if dify_answer.startswith("ERROR:"):
                print(f"    ❌ Dify调用失败: {dify_answer}")
                continue

            print(f"    ✅ Dify回答获取成功: {dify_answer}")

            print("    步骤2: 从Dify回答中提取SQL...")
            predicted_sql = extract_sql_from_dify_answer(dify_answer)
            if not predicted_sql:
                print("    ❌ 无法从Dify回答中提取SQL")
                continue
            print("    ✅ 提取到预测SQL")
            print(f"    标准SQL: {standard_sql}")
            print(f"    预测SQL: {predicted_sql}")

            # 保存原始预测SQL用于比较
            original_predicted_sql = predicted_sql
            
            # 执行lembed子句统一处理
            predicted_sql = unify_lembed_clauses(standard_sql, predicted_sql)
            
            # 如果预测SQL发生了变化，输出信息
            if predicted_sql != original_predicted_sql:
                print("    🔄 统一了lembed子句")
                print(f"    统一后预测SQL: {predicted_sql}")

            print("    步骤3: 使用metrics.py进行评估...")
            eval_results = evaluate_with_metrics(
                run_sql_func=self.run_sql_with_columns,
                nl_question=question,
                standard_sql=standard_sql,
                predicted_sql=predicted_sql,
                db_schema=db_schema,
                enable_llm=self.llm_evaluation_enabled
            )

            if 'error' in eval_results:
                error_type = eval_results.get('error_type', '')
                if error_type == 'EMPTY_GOLDEN_DATA' or error_type == 'EMPTY_TEST_DATA':
                    if error_type == 'EMPTY_GOLDEN_DATA':
                        print("    ⏭️  标准SQL无结果，跳过此样本")
                    else:
                        print("    ⏭️  预测SQL执行失败或无结果，跳过此样本")
                    skipped_count += 1
                    continue
                print(f"    ❌ 评估失败: {eval_results['error']}")
                continue

            success_count += 1

            result_item = {
                'sample_id': i,
                'question': question,
                'standard_sql': standard_sql,
                'predicted_sql': predicted_sql,
                'dify_answer': dify_answer,
                'evaluation': eval_results
            }
            results.append(result_item)
            all_eval_results.append(eval_results)

            print("    ✅ 评估结果:")
            print("       标准SQL执行结果:")
            golden_data = eval_results.get('golden_data', [])
            golden_columns = eval_results.get('golden_columns', [])
            if golden_data:
                print(f"       列名: {golden_columns}")
                for row in golden_data[:5]:
                    print(f"       {row}")
                if len(golden_data) > 5:
                    print(f"       ... 共 {len(golden_data)} 行")
            else:
                print("       (空结果)")
            print(f"       Exact Match: {eval_results.get('exact_match', 'N/A'):.3f}")
            print(f"       Precision:   {eval_results.get('precision', 'N/A'):.3f}")
            print(f"       Recall:      {eval_results.get('recall', 'N/A'):.3f}")
            print(f"       F1:          {eval_results.get('f1', 'N/A'):.3f}")
            print(f"       MAP:         {eval_results.get('map', 'N/A'):.3f}")
            print(f"       MRR:         {eval_results.get('mrr', 'N/A'):.3f}")
            print(f"       NDCG:        {eval_results.get('ndcg', 'N/A'):.3f}")
            if 'llm_overall_score' in eval_results:
                print(f"       LLM Overall: {eval_results['llm_overall_score']:.3f}")

            if i % 2 == 0:
                print(f"len(all_eval_results): {len(all_eval_results)}")
                avg_precision = sum(r.get('precision', 0) for r in all_eval_results) / len(all_eval_results)
                print(f"\n    📊 已处理 {i}/{total_samples} 样本, 当前平均 Precision:   {avg_precision:.4f}")
                avg_recall = sum(r.get('recall', 0) for r in all_eval_results) / len(all_eval_results)
                print(f"\n    📊 已处理 {i}/{total_samples} 样本, 当前平均 Recall:      {avg_recall:.3f}")
                avg_f1 = sum(r.get('f1', 0) for r in all_eval_results) / len(all_eval_results)
                print(f"\n    📊 已处理 {i}/{total_samples} 样本, 当前平均 F1: {avg_f1:.4f}")
                avg_mrr = sum(r.get('mrr', 0) for r in all_eval_results) / len(all_eval_results)
                print(f"\n    📊 已处理 {i}/{total_samples} 样本, 当前平均 MRR:         {avg_mrr:.3f}")
                avg_llm_overall = sum(r.get('llm_overall_score', 0) for r in all_eval_results) / len(all_eval_results)
                print(f"\n    📊 已处理 {i}/{total_samples} 样本, 当前平均 LLM Overall: {avg_llm_overall:.3f}")

        print("\n" + "=" * 80)
        print("📈 Benchmark 测试完成！")
        print("=" * 80)

        if all_eval_results:
            avg_precision = sum(r.get('precision', 0) for r in all_eval_results) / len(all_eval_results)
            avg_recall = sum(r.get('recall', 0) for r in all_eval_results) / len(all_eval_results)
            avg_f1 = sum(r.get('f1', 0) for r in all_eval_results) / len(all_eval_results)
            avg_exact_match = sum(r.get('exact_match', 0) for r in all_eval_results) / len(all_eval_results)
            avg_map = sum(r.get('map', 0) for r in all_eval_results) / len(all_eval_results)
            avg_mrr = sum(r.get('mrr', 0) for r in all_eval_results) / len(all_eval_results)
            avg_ndcg = sum(r.get('ndcg', 0) for r in all_eval_results) / len(all_eval_results)
        else:
            avg_precision = avg_recall = avg_f1 = avg_exact_match = avg_map = avg_mrr = avg_ndcg = 0

        print(f"\n总样本数: {total_samples}")
        print(f"成功评估样本数: {success_count}")
        print(f"跳过样本数(标准SQL无结果): {skipped_count}")
        print("\n🎯 平均评估指标:")
        print(f"   Exact Match: {avg_exact_match:.4f} ({avg_exact_match*100:.2f}%)")
        print(f"   Precision:   {avg_precision:.4f}")
        print(f"   Recall:      {avg_recall:.4f}")
        print(f"   F1:          {avg_f1:.4f}")
        print(f"   MAP:         {avg_map:.4f}")
        print(f"   MRR:         {avg_mrr:.4f}")
        print(f"   NDCG:        {avg_ndcg:.4f}")

        time_suffix = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = os.path.join(self.output_path, f"benchmark_results-{time_suffix}.json")

        result_summary = {
            'summary': {
                'total_samples': total_samples,
                'success_samples': success_count,
                'llm_evaluation_enabled': self.llm_evaluation_enabled,
                'metrics': {
                    'exact_match': avg_exact_match,
                    'precision': avg_precision,
                    'recall': avg_recall,
                    'f1': avg_f1,
                    'map': avg_map,
                    'mrr': avg_mrr,
                    'ndcg': avg_ndcg
                }
            },
            'details': results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_summary, f, ensure_ascii=False, indent=2)

        print(f"\n💾 详细结果已保存至: {output_path}")
        print("=" * 80)
        
        return result_summary


# ========== 配置 ==========
# 从环境变量加载配置
API_KEY = os.getenv("API_KEY")
DIFY_URL = os.getenv("DIFY_URL", "https://api.dify.ai/v1/chat-messages")
MYSCALE_HOST = os.getenv("MYSCALE_HOST")
MYSCALE_PORT = int(os.getenv("MYSCALE_PORT"))
MYSCALE_USER = os.getenv("MYSCALE_USER")
MYSCALE_PASSWORD = os.getenv("MYSCALE_PASSWORD")
MYSCALE_DATABASE = os.getenv("MYSCALE_DATABASE", "olympics")

DEFAULT_DATASET_PATH = "./data/results/test/olympics/olympics_qs.json"
DEFAULT_OUTPUT_PATH = "./result/"
LLM_EVALUATION_ENABLED = True
LLM_MODEL = "gpt-4o"


# ========== 主程序 ==========
def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Dify Text2SQL Benchmark 测试")
    parser.add_argument("--dataset", type=str, default=DEFAULT_DATASET_PATH,
                      help="数据集路径 (默认: %s)" % DEFAULT_DATASET_PATH)
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_PATH,
                      help="结果输出路径 (默认: %s)" % DEFAULT_OUTPUT_PATH)
    parser.add_argument("--text-num", type=int, default=None,
                      help="测试样本数量 (默认: 全部)")
    parser.add_argument("--no-llm", action="store_true",
                      help="禁用 LLM 评估")
    
    args = parser.parse_args()
    
    # 创建基准测试实例
    benchmark = Text2SQLBenchmark(
        api_key=API_KEY,
        dify_url=DIFY_URL,
        myscale_host=MYSCALE_HOST,
        myscale_port=MYSCALE_PORT,
        myscale_user=MYSCALE_USER,
        myscale_password=MYSCALE_PASSWORD,
        myscale_database=MYSCALE_DATABASE,
        output_path=args.output,
        llm_evaluation_enabled=not args.no_llm,
        llm_model=LLM_MODEL
    )
    
    # 运行基准测试
    benchmark.run_benchmark(args.dataset, args.text_num)


if __name__ == "__main__":
    main()