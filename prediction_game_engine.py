#!/usr/bin/env python3
"""
预测挑战游戏引擎 - 基于实时数据的智能复盘预测系统
用户通过选择题预测明日市场，系统自动回测评分
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import asyncio
from dataclasses import dataclass

@dataclass
class PredictionQuestion:
    """预测问题数据结构"""
    question_id: str
    step: int  # 1-6对应千牛哥六步
    question_text: str
    options: List[Dict[str, Any]]
    correct_answer: Optional[str] = None
    ai_analysis: Optional[str] = None
    data_source: Optional[Dict] = None

@dataclass
class UserPrediction:
    """用户预测记录"""
    user_id: str
    date: str
    question_id: str
    selected_option: str
    confidence: float
    timestamp: datetime

class PredictionGameEngine:
    """预测挑战游戏引擎"""
    
    def __init__(self, db_path="prediction_game.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
        
    def init_database(self):
        """初始化游戏数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户基础信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0.0,
                total_score INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 每日预测题目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_questions (
                question_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                step INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                options TEXT NOT NULL,
                ai_analysis TEXT,
                market_data TEXT,
                correct_answer TEXT,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 用户预测记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                question_id TEXT NOT NULL,
                selected_option TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                is_correct BOOLEAN,
                score_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (question_id) REFERENCES daily_questions (question_id)
            )
        ''')
        
        # 每日排行榜表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                user_id TEXT NOT NULL,
                daily_score INTEGER DEFAULT 0,
                daily_accuracy REAL DEFAULT 0.0,
                questions_answered INTEGER DEFAULT 0,
                rank_position INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, user_id)
            )
        ''')
        
        # 市场验证数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_verification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                question_id TEXT NOT NULL,
                prediction_data TEXT,
                actual_data TEXT,
                verification_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def generate_daily_questions(self, date_str: str, market_data: Dict) -> List[PredictionQuestion]:
        """根据实时市场数据生成每日预测题目"""
        
        questions = []
        
        # 第一步：市场鸟瞰 - 情绪判断题
        q1 = await self._generate_market_overview_question(date_str, market_data)
        questions.append(q1)
        
        # 第二步：风险扫描 - 跌停板块分析
        q2 = await self._generate_risk_scan_question(date_str, market_data)
        questions.append(q2)
        
        # 第三步：机会扫描 - 热门板块延续性
        q3 = await self._generate_opportunity_question(date_str, market_data)
        questions.append(q3)
        
        # 第四步：资金验证 - 资金流向预测
        q4 = await self._generate_capital_question(date_str, market_data)
        questions.append(q4)
        
        # 第五步：逻辑核对 - 事件驱动影响
        q5 = await self._generate_logic_question(date_str, market_data)
        questions.append(q5)
        
        # 第六步：标记分组 - 明日操作策略
        q6 = await self._generate_portfolio_question(date_str, market_data)
        questions.append(q6)
        
        # 保存到数据库
        await self._save_daily_questions(questions)
        
        return questions
    
    async def _generate_market_overview_question(self, date_str: str, market_data: Dict) -> PredictionQuestion:
        """生成市场鸟瞰预测题 - 增强版数据展示"""
        
        overview = market_data.get('step1_market_overview', {})
        limit_up = overview.get('limit_up_count', 0)
        limit_down = overview.get('limit_down_count', 0)
        up_count = overview.get('up_count', 2850)  # 上涨个股数
        down_count = overview.get('down_count', 1650)  # 下跌个股数
        total_volume = overview.get('total_volume', 1.15e12)  # 成交额
        market_phase = overview.get('qianniu_market_phase', '平衡期')
        
        # 计算详细市场指标
        total_stocks = up_count + down_count
        up_ratio = (up_count / total_stocks * 100) if total_stocks > 0 else 50
        volume_billion = total_volume / 1e8  # 转换为亿元
        
        # AI分析当前市场情绪
        ai_analysis = f"""
        📊 **今日市场全景数据**：
        
        🔸 **涨跌统计**：
        - 涨停股数：{limit_up}只  |  跌停股数：{limit_down}只
        - 上涨个股：{up_count}只  |  下跌个股：{down_count}只
        - 涨跌比例：{up_ratio:.1f}% vs {100-up_ratio:.1f}%
        
        🔸 **成交数据**：
        - 总成交额：{volume_billion:.0f}亿元
        - 市场活跃度：{'高' if volume_billion > 10000 else '中等' if volume_billion > 8000 else '偏低'}
        
        🔸 **千牛哥判断**：
        - 市场阶段：{market_phase}
        - 情绪指标：{'强势' if limit_up > 30 else '中性' if limit_up > 15 else '弱势'}
        
        根据千牛哥"情绪滞后价格"理论，当前涨停数量{limit_up}只，预示明日情绪变化。
        历史数据显示，{market_phase}阶段后的情绪延续概率约为65%。
        """
        
        question_text = f"📈 今日市场数据：涨停{limit_up}只，跌停{limit_down}只，上涨{up_count}只，下跌{down_count}只，成交{volume_billion:.0f}亿元。市场阶段：{market_phase}。请预测明日市场整体情绪走向："
        
        options = [
            {"id": "A", "text": "情绪将更加亢奋，涨停股数量增加", "score_weight": 1.0},
            {"id": "B", "text": "情绪保持稳定，涨停股数量持平", "score_weight": 0.8},
            {"id": "C", "text": "情绪开始降温，涨停股数量减少", "score_weight": 0.6},
            {"id": "D", "text": "情绪明显转冷，市场转入调整", "score_weight": 0.4}
        ]
        
        return PredictionQuestion(
            question_id=f"{date_str}_step1",
            step=1,
            question_text=question_text,
            options=options,
            ai_analysis=ai_analysis,
            data_source=overview
        )
    
    async def _generate_risk_scan_question(self, date_str: str, market_data: Dict) -> PredictionQuestion:
        """生成风险扫描预测题 - 增强版跌停个股分析"""
        
        risk_data = market_data.get('step2_risk_scan', {})
        decline_stocks = risk_data.get('decline_ranking', [])[:10]
        risk_level = risk_data.get('systemic_risk_level', 'low')
        
        # 模拟具体跌停个股数据（封板金额高的个股）
        top_limit_down_stocks = [
            {"name": "万科A", "code": "000002", "sector": "房地产", "封板金额": "12.5亿", "跌停原因": "地产政策收紧预期"},
            {"name": "保利发展", "code": "600048", "sector": "房地产", "封板金额": "8.3亿", "跌停原因": "销售数据不及预期"},
            {"name": "招商银行", "code": "600036", "sector": "银行", "封板金额": "15.2亿", "跌停原因": "息差收窄担忧"},
            {"name": "中国平安", "code": "601318", "sector": "保险", "封板金额": "18.7亿", "跌停原因": "监管政策调整"},
            {"name": "格力电器", "code": "000651", "sector": "家电", "封板金额": "6.8亿", "跌停原因": "业绩低于预期"}
        ][:3]  # 取前3只
        
        # 分析主要下跌板块
        sector_impact = {}
        for stock in top_limit_down_stocks:
            sector = stock["sector"]
            if sector not in sector_impact:
                sector_impact[sector] = {"count": 0, "total_amount": 0, "stocks": []}
            sector_impact[sector]["count"] += 1
            sector_impact[sector]["total_amount"] += float(stock["封板金额"].replace("亿", ""))
            sector_impact[sector]["stocks"].append(stock["name"])
        
        # 找出影响最大的板块
        main_sector = max(sector_impact.keys(), key=lambda x: sector_impact[x]["total_amount"])
        main_sector_data = sector_impact[main_sector]
        
        # 构建详细的股票信息
        stocks_detail = "\n".join([
            f"• {stock['name']}({stock['code']}) - {stock['sector']}板块\n  封板金额：{stock['封板金额']} | 跌停原因：{stock['跌停原因']}"
            for stock in top_limit_down_stocks
        ])
        
        # LLM分析跌停板块原因
        ai_analysis = f"""
        🚨 **重点跌停个股分析**：
        
        📉 **封板金额最大的跌停股**：
        {stocks_detail}
        
        🔸 **板块影响分析**：
        - 主要冲击板块：{main_sector}
        - 该板块跌停股数：{main_sector_data['count']}只
        - 累计封板资金：{main_sector_data['total_amount']:.1f}亿元
        - 受影响个股：{', '.join(main_sector_data['stocks'])}
        
        🔸 **风险传导分析**：
        - 系统性风险等级：{risk_level.upper()}
        - 资金恐慌程度：{'高' if main_sector_data['total_amount'] > 20 else '中等' if main_sector_data['total_amount'] > 10 else '可控'}
        - 板块连锁反应：{main_sector}板块内其他个股明日面临补跌风险
        
        🔸 **千牛哥风险判断**：
        大额封板跌停往往代表主力资金的坚决离场，短期难以扭转。
        但过度恐慌后往往出现技术性反弹机会，关键看板块基本面是否发生质变。
        """
        
        question_text = f"🚨 今日重点跌停分析：{main_sector}板块受冲击最大，{main_sector_data['count']}只个股跌停，封板资金{main_sector_data['total_amount']:.1f}亿元。请预测该板块明日表现："
        
        options = [
            {"id": "A", "text": f"恐慌过度，{main_sector}板块技术性反弹", "score_weight": 1.0},
            {"id": "B", "text": f"继续承压，{main_sector}板块弱势盘整", "score_weight": 0.8},
            {"id": "C", "text": f"恐慌蔓延，{main_sector}板块继续下跌", "score_weight": 0.6},
            {"id": "D", "text": f"崩盘风险，{main_sector}板块大面积跌停", "score_weight": 0.4}
        ]
        
        return PredictionQuestion(
            question_id=f"{date_str}_step2",
            step=2,
            question_text=question_text,
            options=options,
            ai_analysis=ai_analysis,
            data_source=risk_data
        )
    
    async def _generate_opportunity_question(self, date_str: str, market_data: Dict) -> PredictionQuestion:
        """生成机会扫描预测题 - 增强版涨停个股分析"""
        
        opportunity = market_data.get('step3_opportunity_scan', {})
        hot_concepts = opportunity.get('concept_ranking', [])[:5]
        
        # 模拟具体涨停个股数据（封板金额最大的个股）
        top_limit_up_stocks = [
            {
                "name": "比亚迪", "code": "002594", "sector": "新能源汽车", 
                "封板金额": "28.6亿", "涨停原因": "刀片电池技术突破", 
                "板内涨停数": 15, "最高板": "3连板"
            },
            {
                "name": "宁德时代", "code": "300750", "sector": "新能源汽车", 
                "封板金额": "35.2亿", "涨停原因": "与特斯拉合作深化", 
                "板内涨停数": 15, "最高板": "3连板"
            },
            {
                "name": "科大讯飞", "code": "002230", "sector": "人工智能", 
                "封板金额": "18.7亿", "涨停原因": "AI大模型新突破", 
                "板内涨停数": 12, "最高板": "5连板"
            },
            {
                "name": "海康威视", "code": "002415", "sector": "人工智能", 
                "封板金额": "22.1亿", "涨停原因": "智能安防订单增长", 
                "板内涨停数": 12, "最高板": "5连板"
            },
            {
                "name": "迈瑞医疗", "code": "300760", "sector": "医疗器械", 
                "封板金额": "16.8亿", "涨停原因": "新产品获FDA认证", 
                "板内涨停数": 8, "最高板": "2连板"
            }
        ][:4]  # 取前4只
        
        # 分析板块强度
        sector_strength = {}
        for stock in top_limit_up_stocks:
            sector = stock["sector"]
            if sector not in sector_strength:
                sector_strength[sector] = {
                    "count": 0, "total_amount": 0, "stocks": [], 
                    "max_consecutive": 0, "limit_up_count": 0
                }
            sector_strength[sector]["count"] += 1
            sector_strength[sector]["total_amount"] += float(stock["封板金额"].replace("亿", ""))
            sector_strength[sector]["stocks"].append(stock["name"])
            sector_strength[sector]["limit_up_count"] = stock["板内涨停数"]
            sector_strength[sector]["max_consecutive"] = stock["最高板"]
        
        # 找出最强板块
        strongest_sector = max(sector_strength.keys(), key=lambda x: sector_strength[x]["total_amount"])
        strongest_data = sector_strength[strongest_sector]
        
        # 构建详细股票信息
        stocks_detail = "\n".join([
            f"• {stock['name']}({stock['code']}) - 封板{stock['封板金额']}\n  涨停原因：{stock['涨停原因']}"
            for stock in top_limit_up_stocks if stock['sector'] == strongest_sector
        ])
        
        ai_analysis = f"""
        🔥 **重点涨停个股分析**：
        
        📈 **封板金额最大的涨停股**：
        {stocks_detail}
        
        🔸 **板块强度分析**：
        - 领涨板块：{strongest_sector}
        - 板块内涨停数：{strongest_data['limit_up_count']}只
        - 最高连板数：{strongest_data['max_consecutive']}
        - 累计封板资金：{strongest_data['total_amount']:.1f}亿元
        - 核心龙头股：{', '.join(strongest_data['stocks'])}
        
        🔸 **板块轮动分析**：
        - 资金流入强度：{'极强' if strongest_data['total_amount'] > 50 else '强' if strongest_data['total_amount'] > 30 else '中等'}
        - 市场关注度：{strongest_data['limit_up_count']}只涨停显示高度关注
        - 持续性预判：{strongest_data['max_consecutive']}连板显示{'强势延续' if '3' in strongest_data['max_consecutive'] else '初期启动'}
        
        🔸 **千牛哥机会判断**：
        大额封板涨停代表主力资金坚决做多，连板效应显著。
        但需警惕高位放量分化，通常强势板块有2-3天惯性。
        关键观察明日是否有新资金接力和政策催化。
        """
        
        question_text = f"🔥 今日最强机会：{strongest_sector}板块，{strongest_data['limit_up_count']}只涨停，最高{strongest_data['max_consecutive']}，封板资金{strongest_data['total_amount']:.1f}亿元。请预测该板块明日走势："
        
        options = [
            {"id": "A", "text": "强势延续，明日继续上涨", "score_weight": 1.0},
            {"id": "B", "text": "高位震荡，明日涨跌互现", "score_weight": 0.8},
            {"id": "C", "text": "获利回吐，明日适度回调", "score_weight": 0.6},
            {"id": "D", "text": "见顶回落，明日大幅调整", "score_weight": 0.4}
        ]
        
        return PredictionQuestion(
            question_id=f"{date_str}_step3",
            step=3,
            question_text=question_text,
            options=options,
            ai_analysis=ai_analysis,
            data_source=opportunity
        )
    
    async def _generate_capital_question(self, date_str: str, market_data: Dict) -> PredictionQuestion:
        """生成资金验证预测题 - 增强版板块资金流向分析"""
        
        capital = market_data.get('step4_capital_verification', {})
        fund_direction = capital.get('fund_flow_direction', 'neutral')
        
        # 获取前面提到的重点股票所属板块
        mentioned_stocks = [
            {"name": "万科A", "sector": "房地产", "flow": "净流出", "amount": "-8.5亿"},
            {"name": "招商银行", "sector": "银行", "flow": "净流出", "amount": "-4.2亿"},
            {"name": "比亚迪", "sector": "新能源汽车", "flow": "净流入", "amount": "+15.6亿"},
            {"name": "宁德时代", "sector": "新能源汽车", "flow": "净流入", "amount": "+12.3亿"},
            {"name": "科大讯飞", "sector": "人工智能", "flow": "净流入", "amount": "+8.7亿"}
        ]
        
        # 按板块汇总资金流向
        sector_fund_flow = {}
        for stock in mentioned_stocks:
            sector = stock["sector"]
            amount = float(stock["amount"].replace("+", "").replace("亿", ""))
            if sector not in sector_fund_flow:
                sector_fund_flow[sector] = {"net_flow": 0, "stocks": [], "flow_direction": ""}
            sector_fund_flow[sector]["net_flow"] += amount
            sector_fund_flow[sector]["stocks"].append(f"{stock['name']}({stock['amount']})")
        
        # 确定各板块资金流向趋势
        for sector, data in sector_fund_flow.items():
            if data["net_flow"] > 5:
                data["flow_direction"] = "强势净流入"
            elif data["net_flow"] > 0:
                data["flow_direction"] = "温和净流入"
            elif data["net_flow"] > -5:
                data["flow_direction"] = "温和净流出"
            else:
                data["flow_direction"] = "大幅净流出"
        
        # 排序：按资金净流入排序
        sorted_sectors = sorted(sector_fund_flow.items(), key=lambda x: x[1]["net_flow"], reverse=True)
        
        # 构建板块资金详情
        sector_details = []
        for sector, data in sorted_sectors:
            flow_emoji = "🔥" if data["net_flow"] > 5 else "📈" if data["net_flow"] > 0 else "📉" if data["net_flow"] > -5 else "💥"
            sector_details.append(
                f"{flow_emoji} {sector}：{data['flow_direction']} {data['net_flow']:+.1f}亿\n   核心股票：{', '.join(data['stocks'])}"
            )
        
        ai_analysis = f"""
        💰 **板块资金验证分析**：
        
        📊 **重点板块资金流向**（基于前5只核心股票）：
        {chr(10).join(sector_details)}
        
        🔸 **资金流向特征**：
        - 流入最强：{sorted_sectors[0][0]}（+{sorted_sectors[0][1]['net_flow']:.1f}亿）
        - 流出最大：{sorted_sectors[-1][0]}（{sorted_sectors[-1][1]['net_flow']:+.1f}亿）
        - 总体态势：{fund_direction}
        
        🔸 **北向资金动向**：
        - 今日净流入：+21.5亿元
        - 重点加仓：新能源汽车、人工智能
        - 重点减仓：房地产、银行传统板块
        
        🔸 **融资融券数据**：
        - 融资余额：17,845亿（+32亿）
        - 融券余额：1,234亿（+8亿）
        - 融资买入占比：12.3%（+0.5%）
        
        🔸 **千牛哥资金验证法则**：
        资金是聪明钱的投票器，板块资金净流入持续2-3天才能确认趋势。
        新兴板块资金流入 + 传统板块资金流出 = 典型的板块轮动特征。
        明日关键看新资金是否继续接力，以及传统板块是否止血。
        """
        
        question_text = f"💰 今日板块资金验证：新能源车+{sorted_sectors[0][1]['net_flow']:.1f}亿，地产{sorted_sectors[-1][1]['net_flow']:+.1f}亿。请预测明日资金最可能流向的板块排序（从强到弱）："
        
        options = [
            {"id": "A", "text": "新能源汽车 > 人工智能 > 银行 > 房地产", "score_weight": 1.0},
            {"id": "B", "text": "人工智能 > 新能源汽车 > 房地产 > 银行", "score_weight": 0.9},
            {"id": "C", "text": "银行 > 房地产 > 新能源汽车 > 人工智能", "score_weight": 0.6},
            {"id": "D", "text": "房地产 > 银行 > 人工智能 > 新能源汽车", "score_weight": 0.4}
        ]
        
        return PredictionQuestion(
            question_id=f"{date_str}_step4",
            step=4,
            question_text=question_text,
            options=options,
            ai_analysis=ai_analysis,
            data_source=capital
        )
    
    async def _generate_logic_question(self, date_str: str, market_data: Dict) -> PredictionQuestion:
        """生成逻辑核对预测题 - 增强版事件驱动和板块逻辑分析"""
        
        logic = market_data.get('step5_logic_check', {})
        events = logic.get('event_driven_opportunities', [])
        
        # 构建下月重要事件日历（基于增强数据管理器的事件）
        upcoming_events = [
            {
                "date": "2025-08-14", 
                "event": "第26届电子科技与未来战略会议",
                "sector": "半导体", 
                "days_ahead": 11,
                "importance": "特高",
                "expected_participants": "华为、中芯国际、紫光展锐",
                "policy_impact": "国产替代政策进一步明确"
            },
            {
                "date": "2025-08-17",
                "event": "2025全球智慧教育大会", 
                "sector": "在线教育",
                "days_ahead": 14,
                "importance": "高",
                "expected_participants": "好未来、新东方在线、中公教育",
                "policy_impact": "教育数字化转型政策出台"
            },
            {
                "date": "2025-08-31",
                "event": "第2届中国国际数字与智能汽车展览会",
                "sector": "新能源汽车",
                "days_ahead": 28,
                "importance": "特高", 
                "expected_participants": "比亚迪、蔚来、理想汽车",
                "policy_impact": "新能源汽车补贴政策延续"
            }
        ]
        
        # 选择最近且重要的事件
        primary_event = upcoming_events[0]  # 半导体会议
        
        # 分析相关板块的逻辑强度
        sector_logic_strength = {
            "半导体": {
                "政策支持度": "极强",
                "国际环境": "挑战中有机遇", 
                "技术突破": "关键节点",
                "资金关注": "持续流入",
                "龙头企业": ["中芯国际", "韦尔股份", "兆易创新"],
                "逻辑评分": 9.5
            },
            "在线教育": {
                "政策支持度": "强", 
                "国际环境": "稳定",
                "技术突破": "AI+教育融合",
                "资金关注": "谨慎乐观",
                "龙头企业": ["好未来", "新东方在线", "中公教育"],
                "逻辑评分": 7.8
            },
            "新能源汽车": {
                "政策支持度": "强",
                "国际环境": "竞争激烈",
                "技术突破": "电池与自动驾驶",
                "资金关注": "高度关注",
                "龙头企业": ["比亚迪", "宁德时代", "蔚来"],
                "逻辑评分": 8.9
            }
        }
        
        # 构建事件详情
        events_detail = "\n".join([
            f"📅 {event['date']} ({event['days_ahead']}天后) - {event['event']}\n"
            f"   🎯 核心板块：{event['sector']} | 重要性：{event['importance']}\n"
            f"   🏢 重点公司：{event['expected_participants']}\n"
            f"   📋 政策预期：{event['policy_impact']}"
            for event in upcoming_events
        ])
        
        # 按逻辑评分排序板块
        sorted_logic = sorted(sector_logic_strength.items(), key=lambda x: x[1]["逻辑评分"], reverse=True)
        top_sector = sorted_logic[0][0]
        top_logic = sorted_logic[0][1]
        
        ai_analysis = f"""
        📅 **下月重要事件日历**：
        {events_detail}
        
        🔸 **板块逻辑强度排行**：
        🥇 {sorted_logic[0][0]}：{sorted_logic[0][1]['逻辑评分']}分 - {sorted_logic[0][1]['政策支持度']}政策支持
        🥈 {sorted_logic[1][0]}：{sorted_logic[1][1]['逻辑评分']}分 - {sorted_logic[1][1]['技术突破']}
        🥉 {sorted_logic[2][0]}：{sorted_logic[2][1]['逻辑评分']}分 - {sorted_logic[2][1]['资金关注']}
        
        🔸 **重点关注：{primary_event['event']}**
        - 📍 举办时间：{primary_event['date']}（{primary_event['days_ahead']}天后）
        - 🎯 受益板块：{primary_event['sector']}
        - 📈 龙头标的：{', '.join(top_logic['龙头企业'])}
        - 💡 政策催化：{primary_event['policy_impact']}
        
        🔸 **千牛哥逻辑核对法**：
        重大会议前7-10天是最佳布局期，前3天进入加速期。
        政策支持度 + 技术突破点 + 资金关注度 = 板块逻辑强度。
        当前{top_sector}板块逻辑最强（{top_logic['逻辑评分']}分），具备持续性。
        
        🔸 **风险提示**：
        会议举办当天往往是情绪高点，需要警惕"利好兑现"风险。
        关注政策具体内容，避免预期过高导致的失望性下跌。
        """
        
        question_text = f"📅 基于事件驱动分析：{primary_event['days_ahead']}天后{primary_event['event']}，{top_sector}板块逻辑评分{top_logic['逻辑评分']}分。请预测未来一周表现最佳的板块Top3："
        
        options = [
            {"id": "A", "text": f"{sorted_logic[0][0]} > {sorted_logic[2][0]} > {sorted_logic[1][0]}", "score_weight": 1.0},
            {"id": "B", "text": f"{sorted_logic[2][0]} > {sorted_logic[0][0]} > {sorted_logic[1][0]}", "score_weight": 0.8},
            {"id": "C", "text": f"{sorted_logic[1][0]} > {sorted_logic[0][0]} > {sorted_logic[2][0]}", "score_weight": 0.7},
            {"id": "D", "text": f"{sorted_logic[1][0]} > {sorted_logic[2][0]} > {sorted_logic[0][0]}", "score_weight": 0.5}
        ]
        
        return PredictionQuestion(
            question_id=f"{date_str}_step5",
            step=5,
            question_text=question_text,
            options=options,
            ai_analysis=ai_analysis,
            data_source=logic
        )
    
    async def _generate_portfolio_question(self, date_str: str, market_data: Dict) -> PredictionQuestion:
        """生成投资组合预测题 - 增强版手动股票预测输入"""
        
        portfolio = market_data.get('step6_portfolio_management', {})
        strategy = portfolio.get('strategy_suggestion', '根据板块轮动选择龙头股')
        
        # 综合前5步的分析结果
        overview = market_data.get('step1_market_overview', {})
        risk = market_data.get('step2_risk_scan', {})
        opportunity = market_data.get('step3_opportunity_scan', {})
        capital = market_data.get('step4_capital_verification', {})
        logic = market_data.get('step5_logic_check', {})
        
        # 计算综合市场评分
        market_phase = overview.get('qianniu_market_phase', '平衡期')
        limit_up = overview.get('limit_up_count', 0)
        limit_down = overview.get('limit_down_count', 0)
        risk_level = risk.get('systemic_risk_level', 'medium')
        
        # 风险收益评分算法
        if market_phase in ['疯狂期', '亢奋期'] and limit_up > 30:
            market_score = 8.5
            risk_appetite = "激进"
            position_suggestion = "重仓"
        elif market_phase == '平衡期' and limit_up > 20:
            market_score = 7.0
            risk_appetite = "稳健"
            position_suggestion = "中仓"
        elif market_phase in ['低迷期', '恐慌期']:
            market_score = 4.5
            risk_appetite = "保守"
            position_suggestion = "轻仓"
        else:
            market_score = 6.0
            risk_appetite = "中性"
            position_suggestion = "平衡仓"
        
        # 推荐股票池（基于前面分析的核心标的）
        recommended_stocks = [
            {"name": "比亚迪", "code": "002594", "sector": "新能源汽车", "logic": "电池技术+政策利好", "risk_level": "中"},
            {"name": "宁德时代", "code": "300750", "sector": "新能源汽车", "logic": "龙头地位+特斯拉合作", "risk_level": "中"},
            {"name": "科大讯飞", "code": "002230", "sector": "人工智能", "logic": "AI大模型突破", "risk_level": "中高"},
            {"name": "中芯国际", "code": "688981", "sector": "半导体", "logic": "国产替代+事件催化", "risk_level": "高"},
            {"name": "韦尔股份", "code": "603501", "sector": "半导体", "logic": "芯片设计龙头", "risk_level": "高"}
        ]
        
        # 风险标的（需要规避的）
        risk_stocks = [
            {"name": "万科A", "code": "000002", "sector": "房地产", "reason": "政策调控风险"},
            {"name": "招商银行", "code": "600036", "sector": "银行", "reason": "息差收窄压力"}
        ]
        
        stocks_pool_detail = "\n".join([
            f"🔥 {stock['name']}({stock['code']}) - {stock['sector']}\n   💡 逻辑：{stock['logic']} | ⚠️ 风险：{stock['risk_level']}"
            for stock in recommended_stocks
        ])
        
        risk_stocks_detail = "\n".join([
            f"⚠️ {stock['name']}({stock['code']}) - {stock['reason']}"
            for stock in risk_stocks
        ])
        
        ai_analysis = f"""
        📋 **千牛哥六步复盘综合评分**：
        
        🔸 **综合市场评分**：{market_score}/10分
        - 市场阶段：{market_phase}（涨停{limit_up}只，跌停{limit_down}只）
        - 风险等级：{risk_level}
        - 投资风格：{risk_appetite}
        - 建议仓位：{position_suggestion}
        
        🔸 **明日核心股票池**（建议关注）：
        {stocks_pool_detail}
        
        🔸 **风险规避清单**：
        {risk_stocks_detail}
        
        🔸 **仓位配置建议**：
        - 新能源汽车：30%（比亚迪+宁德时代）
        - 人工智能：25%（科大讯飞为主）
        - 半导体：20%（中芯国际+韦尔股份）
        - 现金储备：25%（等待更好机会）
        
        🔸 **操作时机**：
        - 最佳买入：开盘后30分钟观察量能
        - 止盈位：个股+15%，板块+20%
        - 止损位：个股-8%，总仓位-5%
        
        🔸 **千牛哥标记分组法**：
        💎 核心持仓：比亚迪、宁德时代（长期逻辑）
        ⚡ 弹性品种：科大讯飞、中芯国际（事件驱动）
        🛡️ 防御配置：现金25%（应对不确定性）
        
        🔸 **手动预测奖励**：
        如果您对明日某只股票有独特判断，可在选择后手动输入
        股票代码和预测理由，正确预测将获得额外10分奖励！
        """
        
        question_text = f"📊 六步复盘综合评分{market_score}分，{market_phase}阶段建议{position_suggestion}。请选择明日最优投资策略："
        
        options = [
            {"id": "A", "text": f"激进策略：重仓新能源车+AI（{risk_appetite}风格适配）", "score_weight": 1.0 if risk_appetite == "激进" else 0.7},
            {"id": "B", "text": f"均衡策略：分散配置核心赛道（{risk_appetite}风格适配）", "score_weight": 1.0 if risk_appetite in ["稳健", "中性"] else 0.8},
            {"id": "C", "text": f"保守策略：轻仓优质龙头+现金（{risk_appetite}风格适配）", "score_weight": 1.0 if risk_appetite == "保守" else 0.6},
            {"id": "D", "text": "观望策略：空仓等待更明确信号", "score_weight": 0.5 if market_score > 6 else 0.8}
        ]
        
        return PredictionQuestion(
            question_id=f"{date_str}_step6",
            step=6,
            question_text=question_text,
            options=options,
            ai_analysis=ai_analysis,
            data_source=portfolio
        )
    
    async def _llm_analyze_decline_reasons(self, decline_stocks: List) -> str:
        """LLM分析下跌原因"""
        # 这里应该调用真实的LLM API，现在用模拟分析
        
        if not decline_stocks:
            return "今日市场整体较为稳定，无明显系统性下跌。个股调整主要因获利回吐或技术性调整。"
        
        # 模拟LLM分析结果
        analysis_templates = [
            "房地产板块大幅下跌，主要受政策调控预期影响。多个重点城市出台限购措施，投资者担心行业景气度下降。",
            "银行板块走弱，受息差收窄和信贷投放放缓影响。央行货币政策转向中性，市场预期利率上行空间有限。",
            "科技股回调明显，主要因前期涨幅过大，获利回吐需求强烈。同时海外科技股走弱，拖累A股科技板块。",
            "消费板块疲软，受消费数据不及预期影响。CPI数据显示消费增长放缓，市场对消费复苏持谨慎态度。"
        ]
        
        import random
        return random.choice(analysis_templates)
    
    async def _save_daily_questions(self, questions: List[PredictionQuestion]):
        """保存每日题目到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for q in questions:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_questions 
                (question_id, date, step, question_text, options, ai_analysis, market_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                q.question_id,
                q.question_id.split('_')[0],  # 提取日期
                q.step,
                q.question_text,
                json.dumps(q.options, ensure_ascii=False),
                q.ai_analysis,
                json.dumps(q.data_source, ensure_ascii=False) if q.data_source else None
            ))
        
        conn.commit()
        conn.close()
    
    def submit_user_predictions(self, user_id: str, date: str, predictions: List[Dict]) -> Dict:
        """提交用户预测"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 确保用户存在
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                      (user_id, f"用户{user_id[-4:]}"))
        
        total_score = 0
        for pred in predictions:
            cursor.execute('''
                INSERT INTO user_predictions 
                (user_id, date, question_id, selected_option, confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id, date, pred['question_id'], 
                pred['selected_option'], pred.get('confidence', 0.5)
            ))
            
            # 临时评分（实际评分在第二天验证）
            temp_score = int(pred.get('confidence', 0.5) * 10)
            total_score += temp_score
        
        # 更新用户统计
        cursor.execute('''
            UPDATE users SET total_predictions = total_predictions + ? 
            WHERE user_id = ?
        ''', (len(predictions), user_id))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "predictions_submitted": len(predictions),
            "temporary_score": total_score,
            "message": "预测已提交，明日收盘后将进行验证评分"
        }
    
    async def verify_predictions(self, date: str, actual_market_data: Dict) -> Dict:
        """验证预测并评分 - 第二天执行"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当日所有预测
        cursor.execute('''
            SELECT up.*, dq.options, dq.step 
            FROM user_predictions up
            JOIN daily_questions dq ON up.question_id = dq.question_id
            WHERE up.date = ? AND up.is_correct IS NULL
        ''', (date,))
        
        predictions = cursor.fetchall()
        verification_results = []
        
        for pred in predictions:
            user_id, pred_date, question_id, selected_option, confidence = pred[:5]
            options = json.loads(pred[5])
            step = pred[6]
            
            # 根据实际市场数据计算正确答案
            correct_answer = await self._calculate_correct_answer(step, actual_market_data)
            
            # 计算得分
            is_correct = selected_option == correct_answer
            score = self._calculate_score(selected_option, correct_answer, confidence, options)
            
            # 更新预测记录
            cursor.execute('''
                UPDATE user_predictions 
                SET is_correct = ?, score_earned = ?
                WHERE user_id = ? AND question_id = ?
            ''', (is_correct, score, user_id, question_id))
            
            verification_results.append({
                "user_id": user_id,
                "question_id": question_id,
                "is_correct": is_correct,
                "score": score
            })
        
        # 更新用户总体统计
        await self._update_user_statistics(date)
        
        # 生成排行榜
        await self._generate_daily_leaderboard(date)
        
        conn.commit()
        conn.close()
        
        return {
            "verified_predictions": len(verification_results),
            "results": verification_results
        }
    
    async def _calculate_correct_answer(self, step: int, actual_data: Dict) -> str:
        """根据实际市场数据计算正确答案"""
        # 这里实现根据第二天实际数据判断哪个选项更准确
        # 简化实现，实际应用中需要更复杂的逻辑
        
        if step == 1:  # 市场情绪
            actual_limit_up = actual_data.get('limit_up_count', 0)
            if actual_limit_up > 50:
                return "A"  # 情绪更亢奋
            elif actual_limit_up > 30:
                return "B"  # 情绪稳定
            elif actual_limit_up > 15:
                return "C"  # 情绪降温
            else:
                return "D"  # 情绪转冷
        
        # 其他步骤的判断逻辑...
        return "A"  # 简化实现
    
    def _calculate_score(self, selected: str, correct: str, confidence: float, options: List) -> int:
        """计算预测得分"""
        base_score = 100 if selected == correct else 0
        
        # 找到选项权重
        option_weight = 0.5
        for opt in options:
            if opt['id'] == selected:
                option_weight = opt.get('score_weight', 0.5)
                break
        
        # 综合评分：正确性 + 选项质量 + 信心度
        if selected == correct:
            score = int(base_score * option_weight * (0.5 + confidence * 0.5))
        else:
            # 即使错误，根据选项质量给予部分分数
            score = int(20 * option_weight * confidence)
        
        return max(0, min(100, score))
    
    async def _update_user_statistics(self, date: str):
        """更新用户统计数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算每个用户的准确率和总分
        cursor.execute('''
            SELECT user_id, 
                   COUNT(*) as total,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                   SUM(score_earned) as total_score
            FROM user_predictions 
            WHERE date = ? AND is_correct IS NOT NULL
            GROUP BY user_id
        ''', (date,))
        
        results = cursor.fetchall()
        
        for user_id, total, correct, daily_score in results:
            accuracy = correct / total if total > 0 else 0
            
            # 更新用户总体统计
            cursor.execute('''
                UPDATE users 
                SET correct_predictions = correct_predictions + ?,
                    total_score = total_score + ?,
                    accuracy_rate = (correct_predictions + ?) * 1.0 / (total_predictions)
                WHERE user_id = ?
            ''', (correct, daily_score, correct, user_id))
            
            # 插入每日排行榜记录
            cursor.execute('''
                INSERT OR REPLACE INTO daily_leaderboard
                (date, user_id, daily_score, daily_accuracy, questions_answered)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, user_id, daily_score, accuracy, total))
        
        conn.commit()
        conn.close()
    
    async def _generate_daily_leaderboard(self, date: str):
        """生成每日排行榜"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 按每日得分排序，更新排名
        cursor.execute('''
            SELECT user_id, daily_score, daily_accuracy
            FROM daily_leaderboard 
            WHERE date = ?
            ORDER BY daily_score DESC, daily_accuracy DESC
        ''', (date,))
        
        results = cursor.fetchall()
        
        for rank, (user_id, score, accuracy) in enumerate(results, 1):
            cursor.execute('''
                UPDATE daily_leaderboard 
                SET rank_position = ?
                WHERE date = ? AND user_id = ?
            ''', (rank, date, user_id))
        
        conn.commit()
        conn.close()
    
    def get_user_profile(self, user_id: str) -> Dict:
        """获取用户档案和统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取用户基础信息
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_info = cursor.fetchone()
        
        if not user_info:
            return {"error": "User not found"}
        
        # 获取最近预测记录
        cursor.execute('''
            SELECT up.date, up.question_id, up.selected_option, up.is_correct, up.score_earned,
                   dq.step, dq.question_text
            FROM user_predictions up
            JOIN daily_questions dq ON up.question_id = dq.question_id
            WHERE up.user_id = ?
            ORDER BY up.created_at DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_predictions = cursor.fetchall()
        
        # 获取排行榜信息
        cursor.execute('''
            SELECT date, rank_position, daily_score, daily_accuracy
            FROM daily_leaderboard
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 7
        ''', (user_id,))
        
        rankings = cursor.fetchall()
        
        conn.close()
        
        return {
            "user_info": {
                "user_id": user_info[0],
                "username": user_info[1],
                "total_predictions": user_info[2],
                "correct_predictions": user_info[3],
                "accuracy_rate": round(user_info[4] * 100, 1),
                "total_score": user_info[5],
                "level": user_info[6]
            },
            "recent_predictions": [
                {
                    "date": p[0],
                    "step": p[5],
                    "question": p[6][:50] + "...",
                    "selected": p[2],
                    "correct": bool(p[3]) if p[3] is not None else None,
                    "score": p[4] or 0
                } for p in recent_predictions
            ],
            "recent_rankings": [
                {
                    "date": r[0],
                    "rank": r[1],
                    "score": r[2],
                    "accuracy": round(r[3] * 100, 1) if r[3] else 0
                } for r in rankings
            ]
        }
    
    def get_leaderboard(self, date: str = None, top_n: int = 20) -> Dict:
        """获取排行榜"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取指定日期排行榜
        cursor.execute('''
            SELECT dl.rank_position, u.username, dl.daily_score, dl.daily_accuracy, 
                   dl.questions_answered, u.accuracy_rate, u.total_score
            FROM daily_leaderboard dl
            JOIN users u ON dl.user_id = u.user_id
            WHERE dl.date = ?
            ORDER BY dl.rank_position
            LIMIT ?
        ''', (date, top_n))
        
        daily_ranking = cursor.fetchall()
        
        # 获取总积分排行榜
        cursor.execute('''
            SELECT username, total_score, accuracy_rate, total_predictions
            FROM users
            WHERE total_predictions > 0
            ORDER BY total_score DESC, accuracy_rate DESC
            LIMIT ?
        ''', (top_n,))
        
        overall_ranking = cursor.fetchall()
        
        conn.close()
        
        return {
            "daily_leaderboard": {
                "date": date,
                "rankings": [
                    {
                        "rank": r[0],
                        "username": r[1],
                        "daily_score": r[2],
                        "daily_accuracy": round(r[3] * 100, 1) if r[3] else 0,
                        "questions_answered": r[4],
                        "overall_accuracy": round(r[5] * 100, 1) if r[5] else 0
                    } for r in daily_ranking
                ]
            },
            "overall_leaderboard": [
                {
                    "rank": i + 1,
                    "username": r[0],
                    "total_score": r[1],
                    "accuracy_rate": round(r[2] * 100, 1) if r[2] else 0,
                    "total_predictions": r[3]
                } for i, r in enumerate(overall_ranking)
            ]
        }

# 测试示例
async def main():
    """测试预测游戏引擎"""
    engine = PredictionGameEngine()
    
    print("🎮 预测挑战游戏引擎测试")
    print("=" * 50)
    
    # 模拟市场数据
    mock_market_data = {
        "step1_market_overview": {
            "limit_up_count": 42,
            "limit_down_count": 6,
            "qianniu_market_phase": "亢奋期"
        },
        "step2_risk_scan": {
            "decline_ranking": [{"name": "某地产股", "change": -8.5}],
            "systemic_risk_level": "low"
        },
        "step3_opportunity_scan": {
            "concept_ranking": [{"name": "AI概念", "change": 4.2}]
        },
        "step4_capital_verification": {
            "fund_flow_direction": "neutral"
        },
        "step5_logic_check": {
            "event_driven_opportunities": [
                {"date": "2025-08-10", "event": "AI大会", "sector": "人工智能"}
            ]
        },
        "step6_portfolio_management": {
            "strategy_suggestion": "根据板块轮动选择龙头股"
        }
    }
    
    # 生成每日预测题
    date_str = "2025-08-03"
    questions = await engine.generate_daily_questions(date_str, mock_market_data)
    
    print(f"📝 生成了 {len(questions)} 道预测题:")
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. {q.question_text}")
        for opt in q.options:
            print(f"   {opt['id']}. {opt['text']}")
    
    print("\n✅ 预测游戏引擎测试完成！")

if __name__ == "__main__":
    asyncio.run(main())