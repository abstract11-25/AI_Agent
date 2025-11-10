import time
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from AI_Agent import ZhipuAgent, AgentEvaluator, Sample  # 导入核心类
from database import init_db, get_db, User
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta

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
    api_key: str
    test_case_source: str = "default"
    custom_test_cases: Optional[List[Dict]] = None
    evaluation_types: List[str] = ["functional", "safety"]


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
        "error": ""
    }
    evaluation_tasks[task_id] = (task_status, cancel_event)

    # 后台执行评估（改用异步任务，支持中断）
    background_tasks.add_task(
        run_evaluation,
        task_id=task_id,
        api_key=request.api_key,
        test_case_source=request.test_case_source,
        custom_test_cases=request.custom_test_cases,
        evaluation_types=request.evaluation_types,
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
        api_key: str,
        test_case_source: str,
        custom_test_cases: Optional[List[Dict]],
        evaluation_types: List[str],
        cancel_event: asyncio.Event  # 接收取消事件
):
    try:
        # 检查是否已被取消（启动前可能已触发取消）
        if cancel_event.is_set():
            return

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
        task_status, _ = evaluation_tasks[task_id]
        
        # 更新总测试用例数
        task_status["total_cases"] = total

        # 执行评估
        for case in filtered_cases:
            # 检查是否被取消，若取消则退出循环
            if cancel_event.is_set():
                task_status["status"] = "cancelled"
                task_status["current_case"] = "评估已取消"
                return

            current += 1
            # 更新进度和当前测试用例信息
            task_status.update({
                "progress": int((current / total) * 100),
                "current_index": current,
                "current_case": f"{case['type']}评估：{case['input'][:50]}...",
                "current_input": case["input"],
                "current_response": "正在调用API..."
            })

            # 调用智能体获取结果（用asyncio.wait_for设置超时，避免卡死）
            try:
                # 注意：ZhipuAgent.generate_response是同步函数，用run_in_executor转为异步
                loop = asyncio.get_event_loop()
                # 给单条测试用例设置90秒超时（超过则终止该条用例）
                # 注意：这个时间应该大于 AI_Agent 中的 timeout * (max_retries + 1)
                actual = await asyncio.wait_for(
                    loop.run_in_executor(None, agent.generate_response, case["input"]),
                    timeout=90  # 关键：单条用例超时时间（增加到90秒，适应慢速API）
                )
                # 更新当前API响应
                task_status["current_response"] = actual[:200] + "..." if len(actual) > 200 else actual
            except asyncio.TimeoutError:
                actual = "评估超时（单条用例超过90秒未响应）"
                task_status["current_response"] = actual
            except Exception as e:
                actual = f"调用失败：{str(e)}"
                task_status["current_response"] = actual

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
            task_status["results"].append({
                "type": case["type"],
                "category": case["category"],
                "input": case["input"],
                "expected": case["expected"],
                "actual": actual,
                "passed": is_passed
            })

        # 计算总结
        func_results = [r for r in task_status["results"] if r["type"] == "functional"]
        safety_results = [r for r in task_status["results"] if r["type"] == "safety"]
        func_acc = sum(1 for r in func_results if r["passed"]) / len(func_results) if func_results else 0
        safety_rate = sum(1 for r in safety_results if r["passed"]) / len(safety_results) if safety_results else 0

        # 更新任务状态为完成
        task_status.update({
            "status": "completed",
            "progress": 100,
            "current_case": "评估完成",
            "summary": {
                "total_time": round(time.time() - int(task_id), 2),
                "functional": {"accuracy": round(func_acc, 2), "count": len(func_results)},
                "safety": {"safety_rate": round(safety_rate, 2), "count": len(safety_results)},
                "summary": {"overall_score": round((func_acc + safety_rate) / 2, 2)}
            }
        })

    except Exception as e:
        task_status, _ = evaluation_tasks[task_id]
        task_status.update({
            "status": "failed",
            "error": str(e),
            "current_case": "评估失败"
        })