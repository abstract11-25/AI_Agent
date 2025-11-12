from __future__ import annotations

import asyncio
import time
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from AI_Agent import (
    AgentFactory,
    AgentEvaluator,
    AgentSettings,
    FactualityEvaluator,
    FeatureMetricsCalculator,
    Sample,
)
from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from database import User, get_db, init_db

app = FastAPI()

# 初始化数据库
init_db()

# 跨域配置（允许前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储评估任务状态（新增取消事件，用于中断任务）
# 格式: {task_id: (status_dict, cancel_event)}
evaluation_tasks: Dict[str, Tuple[Dict, asyncio.Event]] = {}


# 前端请求数据模型
class EvaluationRequest(BaseModel):
    api_key: Optional[str] = None
    provider: str = "zhipu"
    model: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    extra_headers: Dict[str, str] = Field(default_factory=dict)
    extra_body: Dict[str, Any] = Field(default_factory=dict)
    agent: Optional[AgentSettings] = None
    feature_config: Optional["FeatureConfig"] = None
    test_case_source: str = "default"
    custom_test_cases: Optional[List[Dict[str, Any]]] = None
    evaluation_types: List[str] = Field(default_factory=lambda: ["functional", "safety"])


class FeatureConfig(BaseModel):
    enabled: bool = True
    ground_truth_total: Optional[int] = None
    total_scene_types: Optional[int] = None
    total_environment_configs: Optional[int] = None
    baseline_single_task_time: Optional[float] = None
    baseline_adaptation_cost: Optional[float] = None


# 解决前向引用
EvaluationRequest.model_rebuild(_types_namespace=globals())


# 用户注册请求模型
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


# 用户登录响应模型
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


# 用户信息响应模型
class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    created_at: str


# ==================== 认证相关接口 ====================

# 用户注册接口
@app.post("/api/auth/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "注册成功", "username": db_user.username}


# 用户登录接口
@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 查找用户（OAuth2PasswordRequestForm使用username字段，这里可以是用户名或邮箱）
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


# 获取当前用户信息接口
@app.get("/api/auth/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else ""
    }


# 启动评估任务接口（需要登录）
@app.post("/api/evaluate")
async def start_evaluation(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)  # 需要登录
):
    # 构建智能体配置（兼容旧版参数）
    if request.agent is not None:
        agent_settings = AgentSettings(**request.agent.model_dump())
    else:
        if not request.api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少api_key参数"
            )
        settings_payload = request.model_dump(
            include={
                "provider",
                "model",
                "base_url",
                "temperature",
                "max_tokens",
                "timeout",
                "max_retries",
                "extra_headers",
                "extra_body",
            },
            exclude_unset=True,
        )
        settings_payload = {k: v for k, v in settings_payload.items() if v is not None}
        settings_payload["api_key"] = request.api_key
        agent_settings = AgentSettings(**settings_payload)

    feature_config_data = request.feature_config.model_dump(exclude_unset=True) if request.feature_config else None

    task_id = str(int(time.time()))  # 用时间戳作为任务ID
    cancel_event = asyncio.Event()  # 创建取消事件
    # 初始化任务状态
    task_status = {
        "status": "running",
        "progress": 0,
        "current_case": "准备开始评估...",
        "current_input": "",  # 当前测试用例输入
        "current_response": "",  # 当前API响应
        "current_index": 0,  # 当前测试用例索引
        "total_cases": 0,  # 总测试用例数
        "results": [],
        "summary": None,
        "error": "",
        "agent": {
            "provider": agent_settings.provider,
            "model": agent_settings.model,
            "base_url": agent_settings.base_url,
        },
        "started_at": time.time(),
        "feature_config": feature_config_data,
    }
    evaluation_tasks[task_id] = (task_status, cancel_event)

    # 后台执行评估（改用异步任务，支持中断）
    background_tasks.add_task(
        run_evaluation,
        task_id=task_id,
        agent_settings=agent_settings.model_dump(),
        test_case_source=request.test_case_source,
        custom_test_cases=request.custom_test_cases,
        evaluation_types=request.evaluation_types,
        feature_config=feature_config_data,
        cancel_event=cancel_event  # 传入取消事件
    )
    return {"task_id": task_id, "status": "started"}


# 查询评估进度接口（需要登录）
@app.get("/api/evaluation/{task_id}")
async def get_evaluation_status(
    task_id: str,
    current_user: User = Depends(get_current_user)  # 需要登录
):
    if task_id not in evaluation_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_status, _ = evaluation_tasks[task_id]
    return task_status


# 新增：取消评估任务接口（需要登录）
@app.post("/api/cancel/{task_id}")
async def cancel_evaluation(
    task_id: str,
    current_user: User = Depends(get_current_user)  # 需要登录
):
    if task_id not in evaluation_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_status, cancel_event = evaluation_tasks[task_id]
    if task_status["status"] in ["completed", "failed"]:
        return {"status": "任务已结束，无需取消"}
    # 触发取消事件
    cancel_event.set()
    task_status["status"] = "cancelled"
    task_status["current_case"] = "评估已取消"
    return {"status": "已取消"}


# 实际执行评估的函数（支持中断和超时控制）
async def run_evaluation(  # 改为async函数，支持异步中断
        task_id: str,
        agent_settings: Dict[str, Any],
        test_case_source: str,
        custom_test_cases: Optional[List[Dict[str, Any]]],
        evaluation_types: List[str],
        feature_config: Optional[Dict[str, Any]],
        cancel_event: asyncio.Event  # 接收取消事件
):
    start_time = time.time()
    task_status, _ = evaluation_tasks[task_id]

    try:
        # 检查是否已被取消（启动前可能已触发取消）
        if cancel_event.is_set():
            task_status["status"] = "cancelled"
            task_status["current_case"] = "评估已取消"
            return

        settings = AgentSettings(**agent_settings)
        try:
            agent = AgentFactory.create(settings)
        except ValueError as exc:
            task_status.update({
                "status": "failed",
                "error": str(exc),
                "current_case": "初始化失败"
            })
            return

        evaluator = AgentEvaluator(agent=agent)

        # 替换为自定义测试用例
        if test_case_source == "custom" and custom_test_cases:
            evaluator.test_cases = custom_test_cases

        # 筛选需要执行的测试用例
        filtered_cases = [
            case for case in evaluator.test_cases
            if case.get("type") in evaluation_types
        ]
        total = len(filtered_cases)

        # 更新总测试用例数
        task_status["total_cases"] = total

        if total == 0:
            task_status.update({
                "status": "completed",
                "progress": 100,
                "current_case": "无匹配测试用例",
                "summary": {
                    "total_time": round(time.time() - start_time, 2),
                    "functional": {"accuracy": 0.0, "count": 0},
                    "safety": {"safety_rate": 0.0, "count": 0},
                    "summary": {"overall_score": 0.0},
                },
            })
            return

        factuality_evaluator: Optional[FactualityEvaluator] = None
        loop = asyncio.get_running_loop()
        timeout_per_try = settings.timeout if settings.timeout and settings.timeout > 0 else 60
        retries = settings.max_retries if settings.max_retries and settings.max_retries >= 0 else 0
        per_case_timeout = max(timeout_per_try * (retries + 1), 90)
        feature_enabled = True
        if feature_config is not None and feature_config.get("enabled") is False:
            feature_enabled = False
        feature_calculator = FeatureMetricsCalculator(feature_config) if feature_enabled else None

        for index, case in enumerate(filtered_cases, start=1):
            if cancel_event.is_set():
                task_status["status"] = "cancelled"
                task_status["current_case"] = "评估已取消"
                return

            case_input = case.get("input", "")
            case_type = case.get("type", "functional")
            case_metadata = case.get("metadata") or {}

            # 更新进度和当前测试用例信息
            task_status.update({
                "progress": int((index / total) * 100),
                "current_index": index,
                "current_case": f"{case_type}评估：{case_input[:50]}...",
                "current_input": case_input,
                "current_response": "正在调用API..."
            })

            # 调用智能体获取结果
            case_started_at = time.perf_counter()
            try:
                actual = await asyncio.wait_for(
                    loop.run_in_executor(None, agent.generate_response, case_input),
                    timeout=per_case_timeout
                )
                if isinstance(actual, str) and len(actual) > 200:
                    task_status["current_response"] = f"{actual[:200]}..."
                else:
                    task_status["current_response"] = actual
            except asyncio.TimeoutError:
                actual = "评估超时（单条用例超过预设超时时间未响应）"
                task_status["current_response"] = actual
            except Exception as exc:
                actual = f"调用失败：{str(exc)}"
                task_status["current_response"] = actual
            finally:
                duration = time.perf_counter() - case_started_at
                task_status["current_duration"] = round(duration, 3)

            expected_output = case.get("expected", "")
            is_passed = False

            if case_type == "functional":
                if factuality_evaluator is None:
                    factuality_evaluator = FactualityEvaluator()
                sample = [Sample("", expected_output, actual or "")]
                try:
                    is_passed = factuality_evaluator.evaluate(sample)[0]
                except Exception as eval_exc:
                    is_passed = False
                    task_status["current_response"] = f"{task_status['current_response']}（评估失败：{eval_exc}）"
            else:
                expected_lower = (expected_output or "").lower()
                actual_lower = (actual or "").lower()
                is_passed = expected_lower in actual_lower if expected_lower else False

            # 保存结果
            task_status["results"].append({
                "type": case_type,
                "category": case.get("category"),
                "input": case_input,
                "expected": expected_output,
                "actual": actual,
                "passed": is_passed,
                "duration": duration,
                "metadata": case_metadata,
            })

        # 计算总结
        func_results = [r for r in task_status["results"] if r.get("type") == "functional"]
        safety_results = [r for r in task_status["results"] if r.get("type") == "safety"]
        func_acc = sum(1 for r in func_results if r["passed"]) / len(func_results) if func_results else 0.0
        safety_rate = sum(1 for r in safety_results if r["passed"]) / len(safety_results) if safety_results else 0.0
        has_results = bool(func_results or safety_results)

        # 更新任务状态为完成
        task_status.update({
            "status": "completed",
            "progress": 100,
            "current_case": "评估完成",
            "summary": {
                "total_time": round(time.time() - start_time, 2),
                "functional": {"accuracy": round(func_acc, 2), "count": len(func_results)},
                "safety": {"safety_rate": round(safety_rate, 2), "count": len(safety_results)},
                "summary": {"overall_score": round((func_acc + safety_rate) / 2, 2) if has_results else 0.0}
            }
        })
        durations = [item.get("duration") for item in task_status["results"] if item.get("duration") is not None]
        average_case_time = sum(durations) / len(durations) if durations else None
        task_status["summary"]["average_case_time"] = round(average_case_time, 3) if average_case_time else None
        if feature_calculator is not None:
            task_status["summary"]["feature_metrics"] = feature_calculator.compute(task_status["results"])

    except Exception as exc:
        task_status.update({
            "status": "failed",
            "error": str(exc),
            "current_case": "评估失败"
        })