#!/usr/bin/env python3
"""
股票复盘游戏 - 主程序
基于千牛哥复盘方法论的游戏化股票分析工具
"""

from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
import json
import uvicorn
from datetime import datetime, timedelta
import asyncio
import logging
from pathlib import Path
import numpy as np

from data_system import StockDataSystem
from scoring_system import AdvancedScoringSystem
from enhanced_data_manager import EnhancedDataManager
from prediction_game_engine import PredictionGameEngine
from prediction_game_engine import PredictionGameEngine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 自定义JSON编码器处理datetime和numpy类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# 创建FastAPI应用
app = FastAPI(title="股票复盘游戏", description="基于千牛哥方法论的股票复盘游戏")

# 初始化核心系统
data_system = StockDataSystem()
scoring_system = AdvancedScoringSystem()
enhanced_data_manager = EnhancedDataManager()
prediction_engine = PredictionGameEngine()

# 配置静态文件和模板 (可选)
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

# 游戏状态存储
game_sessions = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主页面 - 传统复盘游戏"""
    return HTMLResponse(open("game_interface.html", "r", encoding="utf-8").read())

@app.get("/prediction", response_class=HTMLResponse)
async def prediction_game(request: Request):
    """预测挑战游戏页面"""
    return HTMLResponse(open("prediction_game_interface.html", "r", encoding="utf-8").read())

@app.get("/api/start_game")
@app.post("/api/start_game")
async def start_game(request: Request = None):
    """开始新游戏"""
    try:
        if request and request.method == "POST":
            data = await request.json()
            user_id = data.get("user_id", "guest")
        else:
            user_id = "guest"
        
        # 创建新游戏会话
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        game_sessions[session_id] = {
            "user_id": user_id,
            "start_time": datetime.now(),
            "current_step": 1,
            "completed_steps": [],
            "step_data": {},
            "predictions": {},
            "skill_points": {
                "market_perception": 50,
                "risk_sense": 50,
                "opportunity_capture": 50,
                "capital_sense": 50,
                "logic_thinking": 50,
                "portfolio_management": 50
            },
            "total_score": 0,
            "level": 1,
            "status": "active"
        }
        
        return {"session_id": session_id, "status": "success", "message": "游戏开始！"}
        
    except Exception as e:
        logger.error(f"开始游戏失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market_data")
async def get_market_data():
    """获取实时市场数据"""
    try:
        # 获取市场概览数据
        market_overview = data_system.get_market_overview()
        
        # 获取风险扫描数据
        risk_data = data_system.get_risk_scan_data()
        
        # 获取机会扫描数据
        opportunity_data = data_system.get_opportunity_scan_data()
        
        # 获取资金验证数据
        capital_data = data_system.get_capital_verification_data()
        
        # 使用安全的JSON序列化
        response_data = {
            "market_overview": _safe_serialize(market_overview),
            "risk_data": _safe_serialize(risk_data),
            "opportunity_data": _safe_serialize(opportunity_data),
            "capital_data": _safe_serialize(capital_data),
            "timestamp": datetime.now().isoformat()
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"获取市场数据失败: {e}")
        return {
            "error": str(e),
            "mock_data": _get_mock_market_data()
        }

@app.post("/api/submit_step/{session_id}/{step_number}")
async def submit_step(session_id: str, step_number: int, request: Request):
    """提交复盘步骤分析"""
    try:
        if session_id not in game_sessions:
            raise HTTPException(status_code=404, detail="游戏会话不存在")
        
        data = await request.json()
        session = game_sessions[session_id]
        
        # 保存步骤数据
        session["step_data"][f"step{step_number}"] = data
        
        if step_number not in session["completed_steps"]:
            session["completed_steps"].append(step_number)
        
        # 更新当前步骤
        if step_number < 6:
            session["current_step"] = step_number + 1
        else:
            session["status"] = "completed"
        
        # 计算技能点奖励
        skill_reward = _calculate_step_skill_reward(step_number, data)
        for skill, points in skill_reward.items():
            session["skill_points"][skill] = min(100, session["skill_points"][skill] + points)
        
        return {
            "status": "success",
            "current_step": session["current_step"],
            "skill_points": session["skill_points"],
            "skill_reward": skill_reward,
            "message": f"第{step_number}步完成！"
        }
        
    except Exception as e:
        logger.error(f"提交步骤失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/submit_predictions/{session_id}")
async def submit_predictions(session_id: str, request: Request):
    """提交预测"""
    try:
        if session_id not in game_sessions:
            raise HTTPException(status_code=404, detail="游戏会话不存在")
        
        data = await request.json()
        session = game_sessions[session_id]
        
        # 保存预测数据
        session["predictions"] = data
        session["prediction_time"] = datetime.now()
        
        # 保存复盘记录到数据库
        record_id = data_system.save_fuPan_record(
            user_id=session["user_id"],
            date=datetime.now().strftime('%Y-%m-%d'),
            step_data=session["step_data"],
            predictions=data
        )
        
        session["record_id"] = record_id
        
        return {
            "status": "success",
            "record_id": record_id,
            "message": "预测提交成功！明日将自动验证结果"
        }
        
    except Exception as e:
        logger.error(f"提交预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calculate_score/{session_id}")
async def calculate_score(session_id: str):
    """计算复盘得分"""
    try:
        if session_id not in game_sessions:
            raise HTTPException(status_code=404, detail="游戏会话不存在")
        
        session = game_sessions[session_id]
        
        if "record_id" not in session:
            raise HTTPException(status_code=400, detail="尚未提交预测")
        
        # 计算得分 (这里使用模拟数据，实际应用中需要第二天的真实数据)
        mock_actual_performance = _get_mock_actual_performance()
        
        score_result = scoring_system.calculate_comprehensive_score(
            session["step_data"], 
            mock_actual_performance
        )
        
        # 更新会话得分
        session["final_score"] = score_result
        session["total_score"] = score_result["total_score"]
        
        return score_result
        
    except Exception as e:
        logger.error(f"计算得分失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session_status/{session_id}")
async def get_session_status(session_id: str):
    """获取游戏会话状态"""
    try:
        if session_id not in game_sessions:
            raise HTTPException(status_code=404, detail="游戏会话不存在")
        
        session = game_sessions[session_id]
        
        return {
            "session_id": session_id,
            "current_step": session["current_step"],
            "completed_steps": session["completed_steps"],
            "skill_points": session["skill_points"],
            "total_score": session["total_score"],
            "level": session["level"],
            "status": session["status"],
            "start_time": session["start_time"].isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取会话状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced_market_data")
async def get_enhanced_market_data():
    """获取增强版市场数据 - 多数据源融合"""
    try:
        # 使用增强版数据管理器
        comprehensive_data = await enhanced_data_manager.get_comprehensive_market_data()
        
        return {
            "status": "success",
            "data": _safe_serialize(comprehensive_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取增强版市场数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data_sources")
async def get_data_sources_status():
    """获取数据源状态"""
    try:
        # 获取数据源状态
        status_report = enhanced_data_manager.get_data_source_status()
        
        # 获取传统数据系统状态
        traditional_sources = data_system.data_sources if hasattr(data_system, 'data_sources') else {}
        
        return {
            "enhanced_manager": status_report,
            "traditional_sources": traditional_sources,
            "integration_status": "active",
            "total_sources": len(status_report.get('available_sources', [])) + len(traditional_sources),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取数据源状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/qianniu_analysis/{date}")
async def get_qianniu_analysis(date: str):
    """获取千牛哥专项分析"""
    try:
        # 获取指定日期的综合分析
        comprehensive_data = await enhanced_data_manager.get_comprehensive_market_data(date)
        
        # 提取千牛哥核心分析
        qianniu_analysis = {
            "date": date,
            "market_phase": comprehensive_data["step1_market_overview"].get("qianniu_market_phase"),
            "emotion_lag_signal": comprehensive_data["step1_market_overview"].get("emotion_lag_signal"),
            "first_mover_advantage": comprehensive_data["step1_market_overview"].get("first_mover_advantage"),
            "risk_level": comprehensive_data["step2_risk_scan"].get("systemic_risk_level"),
            "opportunity_strength": len(comprehensive_data["step3_opportunity_scan"].get("concept_ranking", [])),
            "capital_direction": comprehensive_data["step4_capital_verification"].get("fund_flow_direction"),
            "event_driven_ops": comprehensive_data["step5_logic_check"].get("event_driven_opportunities", []),
            "portfolio_suggestion": comprehensive_data["step6_portfolio_management"].get("strategy_suggestion"),
            "confidence_score": comprehensive_data["metadata"].get("fusion_confidence")
        }
        
        return {
            "qianniu_analysis": qianniu_analysis,
            "data_quality": comprehensive_data["metadata"].get("data_quality"),
            "sources_used": comprehensive_data["metadata"].get("data_sources_used"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取千牛哥分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 预测游戏API ====================

@app.get("/api/daily_questions/{date}")
async def get_daily_questions(date: str):
    """获取每日预测题目"""
    try:
        # 获取市场数据
        market_data = await enhanced_data_manager.get_comprehensive_market_data(date)
        
        # 生成预测题目
        questions = await prediction_engine.generate_daily_questions(date, market_data)
        
        # 格式化返回数据
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                "question_id": q.question_id,
                "step": q.step,
                "question_text": q.question_text,
                "options": q.options,
                "ai_analysis": q.ai_analysis,
                "step_name": _get_step_name(q.step)
            })
        
        return {
            "date": date,
            "questions": formatted_questions,
            "total_questions": len(questions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取每日题目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/submit_predictions")
async def submit_predictions(request: Request):
    """提交用户预测"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        date = data.get("date")
        predictions = data.get("predictions", [])
        
        if not user_id or not date or not predictions:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 提交预测
        result = prediction_engine.submit_user_predictions(user_id, date, predictions)
        
        return {
            "status": "success",
            "result": result,
            "message": f"成功提交{len(predictions)}个预测",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"提交预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user_profile/{user_id}")
async def get_user_profile(user_id: str):
    """获取用户档案"""
    try:
        profile = prediction_engine.get_user_profile(user_id)
        
        if "error" in profile:
            raise HTTPException(status_code=404, detail=profile["error"])
        
        return {
            "profile": profile,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户档案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leaderboard")
async def get_leaderboard(date: str = None, top_n: int = 20):
    """获取排行榜"""
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        leaderboard = prediction_engine.get_leaderboard(date, top_n)
        
        return {
            "leaderboard": leaderboard,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify_predictions/{date}")
async def verify_predictions(date: str):
    """验证预测结果（管理员接口）"""
    try:
        # 获取实际市场数据
        actual_data = await enhanced_data_manager.get_comprehensive_market_data(date)
        
        # 验证预测
        result = await prediction_engine.verify_predictions(date, actual_data)
        
        return {
            "verification_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"验证预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket连接用于实时更新"""
    await websocket.accept()
    
    try:
        while True:
            # 发送实时市场数据更新
            market_data = await get_market_data()
            await websocket.send_json({
                "type": "market_update",
                "data": market_data
            })
            
            # 每30秒更新一次
            await asyncio.sleep(30)
            
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
        await websocket.close()

def _safe_serialize(data):
    """安全的JSON序列化，处理datetime和numpy类型"""
    try:
        return json.loads(json.dumps(data, cls=CustomJSONEncoder))
    except Exception as e:
        logger.warning(f"序列化失败，使用字符串格式: {e}")
        return str(data)

def _get_step_name(step: int) -> str:
    """获取步骤名称"""
    step_names = {
        1: "市场鸟瞰",
        2: "风险扫描", 
        3: "机会扫描",
        4: "资金验证",
        5: "逻辑核对",
        6: "标记分组"
    }
    return step_names.get(step, f"第{step}步")

def _calculate_step_skill_reward(step_number: int, step_data: dict) -> dict:
    """计算步骤技能奖励"""
    rewards = {}
    
    if step_number == 1:  # 市场鸟瞰
        rewards["market_perception"] = 5
    elif step_number == 2:  # 风险扫描
        rewards["risk_sense"] = 5
    elif step_number == 3:  # 机会扫描
        rewards["opportunity_capture"] = 5
    elif step_number == 4:  # 资金验证
        rewards["capital_sense"] = 5
    elif step_number == 5:  # 逻辑核对
        rewards["logic_thinking"] = 5
    elif step_number == 6:  # 标记分组
        rewards["portfolio_management"] = 5
    
    # 根据分析质量给予额外奖励
    if len(str(step_data)) > 200:  # 分析内容丰富
        for skill in rewards:
            rewards[skill] += 2
    
    return rewards

def _get_mock_market_data():
    """获取模拟市场数据"""
    return {
        "indices": {
            "上证指数": {"value": 3245.67, "change": -1.2},
            "深证成指": {"value": 12456.32, "change": 0.8},
            "创业板指": {"value": 2876.45, "change": 1.5}
        },
        "volume": {"total": "1.15万亿", "change": 15},
        "hot_sectors": [
            {"name": "新能源汽车", "change": 3.2},
            {"name": "人工智能", "change": 2.8},
            {"name": "医疗器械", "change": 2.1}
        ],
        "risk_sectors": [
            {"name": "房地产", "change": -2.8},
            {"name": "银行", "change": -1.5}
        ],
        "limit_up": ["比亚迪", "宁德时代", "特斯拉概念"],
        "limit_down": 12
    }

def _get_mock_actual_performance():
    """获取模拟实际表现数据"""
    return {
        "sector_performance": {
            "top_gainers": ["新能源汽车", "人工智能"],
            "top_losers": ["房地产", "银行"]
        },
        "stock_performance": {
            "limit_up_stocks": ["比亚迪", "宁德时代"],
            "strong_performers": ["特斯拉概念"]
        },
        "market_sentiment": {
            "direction": "震荡偏强",
            "fund_sentiment": "积极"
        }
    }

if __name__ == "__main__":
    print("🎮 启动股票复盘游戏服务器...")
    print("🔗 游戏地址: http://localhost:8000")
    print("📊 基于千牛哥复盘方法论")
    print("🎯 让复盘变成游戏，提升先知先觉能力！")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )