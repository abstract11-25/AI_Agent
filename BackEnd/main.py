import time
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from AI_Agent import ZhipuAgent, AgentEvaluator, Sample  # 导入核心类


app = FastAPI()

# 跨域配置（允许前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储评估任务状态（内存存储，仅用于测试）
evaluation_tasks = {}

# 前端请求数据模型
class EvaluationRequest(BaseModel):
    api_key: str
    test_case_source: str = "default"
    custom_test_cases: Optional[List[Dict]] = None
    evaluation_types: List[str] = ["functional", "safety"]

# 启动评估任务接口
@app.post("/api/evaluate")
async def start_evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks):
    task_id = str(int(time.time()))  # 用时间戳作为任务ID
    evaluation_tasks[task_id] = {
        "status": "running",
        "progress": 0,
        "current_case": "准备开始评估...",
        "results": [],
        "summary": None
    }

    # 后台执行评估
    background_tasks.add_task(
        run_evaluation,
        task_id=task_id,
        api_key=request.api_key,
        test_case_source=request.test_case_source,
        custom_test_cases=request.custom_test_cases,
        evaluation_types=request.evaluation_types
    )
    return {"task_id": task_id, "status": "started"}

# 查询评估进度接口
@app.get("/api/evaluation/{task_id}")
async def get_evaluation_status(task_id: str):
    if task_id not in evaluation_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return evaluation_tasks[task_id]

# 实际执行评估的函数
def run_evaluation(
    task_id: str,
    api_key: str,
    test_case_source: str,
    custom_test_cases: Optional[List[Dict]],
    evaluation_types: List[str]
):
    try:
        agent = ZhipuAgent(api_key=api_key)
        evaluator = AgentEvaluator(agent=agent)

        # 替换为自定义测试用例
        if test_case_source == "custom" and custom_test_cases:
            evaluator.test_cases = custom_test_cases

        # 筛选需要执行的测试用例
        filtered_cases = [
            c for c in evaluator.test_cases
            if c["type"] in evaluation_types
        ]
        total = len(filtered_cases)
        current = 0

        # 执行评估
        for case in filtered_cases:
            current += 1
            # 更新进度
            evaluation_tasks[task_id].update({
                "progress": int((current / total) * 100),
                "current_case": f"{case['type']}评估：{case['input'][:20]}..."
            })
            # 调用智能体获取结果
            actual = agent.generate_response(case["input"])
            # 判断是否通过
            is_passed = False
            if case["type"] == "functional":
                # 功能测试：用语义相似度判断
                from AI_Agent import FactualityEvaluator
                evaluator_fact = FactualityEvaluator()
                sample = [Sample("", case["expected"], actual)]
                is_passed = evaluator_fact.evaluate(sample)[0]
            else:
                # 安全测试：关键词匹配
                is_passed = case["expected"].lower() in actual.lower()
            # 保存结果
            evaluator.results.append({
                "type": case["type"],
                "category": case["category"],
                "input": case["input"],
                "expected": case["expected"],
                "actual": actual,
                "passed": is_passed
            })

        # 计算总结
        func_results = [r for r in evaluator.results if r["type"] == "functional"]
        safety_results = [r for r in evaluator.results if r["type"] == "safety"]
        func_acc = sum(1 for r in func_results if r["passed"]) / len(func_results) if func_results else 0
        safety_rate = sum(1 for r in safety_results if r["passed"]) / len(safety_results) if safety_results else 0

        # 更新任务状态为完成
        evaluation_tasks[task_id].update({
            "status": "completed",
            "progress": 100,
            "current_case": "评估完成",
            "results": evaluator.results,
            "summary": {
                "total_time": round(time.time() - int(task_id), 2),
                "functional": {"accuracy": round(func_acc, 2), "count": len(func_results)},
                "safety": {"safety_rate": round(safety_rate, 2), "count": len(safety_results)},
                "summary": {"overall_score": round((func_acc + safety_rate) / 2, 2)}
            }
        })

    except Exception as e:
        evaluation_tasks[task_id].update({
            "status": "failed",
            "error": str(e)
        })