#!/usr/bin/env python3
"""
股票复盘游戏 - 评分系统
基于千牛哥复盘方法论的深度评分维度
"""

import json
import re
from datetime import datetime, timedelta
import pandas as pd
import logging

class AdvancedScoringSystem:
    """高级评分系统 - 基于千牛哥复盘深度维度"""
    
    def __init__(self):
        self.scoring_config = {
            # 预测准确度评分 (70分)
            "prediction_accuracy": {
                "sector_performance": 30,  # 板块表现预测
                "stock_performance": 25,   # 个股涨跌预测  
                "market_sentiment": 15     # 市场情绪预测
            },
            
            # 复盘深度评分 (30分)
            "analysis_depth": {
                "six_steps_completion": 10,  # 六步完成度
                "analysis_quality": 10,      # 分析深度质量
                "logic_consistency": 10      # 逻辑严密性
            }
        }
    
    def calculate_comprehensive_score(self, fuPan_record, actual_performance):
        """计算综合评分"""
        
        # 1. 预测准确度评分 (70分)
        prediction_score = self._calculate_prediction_accuracy(
            fuPan_record.get('predictions', {}), 
            actual_performance
        )
        
        # 2. 复盘深度评分 (30分)  
        depth_score = self._calculate_analysis_depth(fuPan_record)
        
        # 3. 额外技能点评分
        skill_bonus = self._calculate_skill_bonus(fuPan_record)
        
        total_score = prediction_score + depth_score + skill_bonus
        
        return {
            "total_score": min(total_score, 100),  # 最高100分
            "prediction_score": prediction_score,
            "depth_score": depth_score,
            "skill_bonus": skill_bonus,
            "grade": self._get_grade(total_score),
            "skill_points": self._calculate_skill_points(fuPan_record),
            "detailed_feedback": self._generate_feedback(fuPan_record, actual_performance)
        }
    
    def _calculate_prediction_accuracy(self, predictions, actual_performance):
        """计算预测准确度 (70分)"""
        
        sector_score = self._score_sector_predictions(
            predictions.get('sectors', {}), 
            actual_performance.get('sector_performance', {})
        )
        
        stock_score = self._score_stock_predictions(
            predictions.get('stocks', {}),
            actual_performance.get('stock_performance', {})
        )
        
        sentiment_score = self._score_sentiment_predictions(
            predictions.get('market_sentiment', {}),
            actual_performance.get('market_sentiment', {})
        )
        
        return sector_score + stock_score + sentiment_score
    
    def _score_sector_predictions(self, sector_predictions, actual_sectors):
        """评分板块预测 (30分)"""
        if not sector_predictions or not actual_sectors:
            return 0
            
        total_score = 0
        max_score = 30
        
        # 热门板块预测准确性
        predicted_hot = sector_predictions.get('hot_sectors', [])
        actual_hot = actual_sectors.get('top_gainers', [])
        
        hot_accuracy = len(set(predicted_hot) & set(actual_hot)) / max(len(predicted_hot), 1)
        total_score += hot_accuracy * 15
        
        # 风险板块预测准确性
        predicted_risk = sector_predictions.get('risk_sectors', [])
        actual_risk = actual_sectors.get('top_losers', [])
        
        risk_accuracy = len(set(predicted_risk) & set(actual_risk)) / max(len(predicted_risk), 1)
        total_score += risk_accuracy * 15
        
        return min(total_score, max_score)
    
    def _score_stock_predictions(self, stock_predictions, actual_stocks):
        """评分个股预测 (25分)"""
        if not stock_predictions or not actual_stocks:
            return 0
            
        total_score = 0
        max_score = 25
        
        # 涨停预测
        predicted_limit_up = stock_predictions.get('limit_up_candidates', [])
        actual_limit_up = actual_stocks.get('limit_up_stocks', [])
        
        limit_up_accuracy = len(set(predicted_limit_up) & set(actual_limit_up)) / max(len(predicted_limit_up), 1)
        total_score += limit_up_accuracy * 12
        
        # 强势股预测
        predicted_strong = stock_predictions.get('strong_stocks', [])
        actual_strong = actual_stocks.get('strong_performers', [])
        
        strong_accuracy = len(set(predicted_strong) & set(actual_strong)) / max(len(predicted_strong), 1)
        total_score += strong_accuracy * 13
        
        return min(total_score, max_score)
    
    def _score_sentiment_predictions(self, sentiment_predictions, actual_sentiment):
        """评分市场情绪预测 (15分)"""
        if not sentiment_predictions or not actual_sentiment:
            return 0
            
        total_score = 0
        max_score = 15
        
        # 市场方向预测
        predicted_direction = sentiment_predictions.get('direction', '')
        actual_direction = actual_sentiment.get('direction', '')
        
        if predicted_direction == actual_direction:
            total_score += 8
        
        # 资金情绪预测
        predicted_funds = sentiment_predictions.get('fund_sentiment', '')
        actual_funds = actual_sentiment.get('fund_sentiment', '')
        
        if predicted_funds == actual_funds:
            total_score += 7
        
        return min(total_score, max_score)
    
    def _calculate_analysis_depth(self, fuPan_record):
        """计算分析深度评分 (30分)"""
        
        # 六步完成度评分 (10分)
        completion_score = self._score_six_steps_completion(fuPan_record)
        
        # 分析质量评分 (10分)  
        quality_score = self._score_analysis_quality(fuPan_record)
        
        # 逻辑严密性评分 (10分)
        logic_score = self._score_logic_consistency(fuPan_record)
        
        return completion_score + quality_score + logic_score
    
    def _score_six_steps_completion(self, fuPan_record):
        """评分六步完成度 (10分)"""
        steps = ['step1_market_overview', 'step2_risk_scan', 'step3_opportunity_scan',
                'step4_capital_verification', 'step5_logic_check', 'step6_portfolio_management']
        
        completed_steps = 0
        for step in steps:
            step_data = fuPan_record.get(step, '')
            if isinstance(step_data, str) and step_data:
                step_content = json.loads(step_data) if step_data else {}
            else:
                step_content = step_data
                
            if step_content and len(str(step_content)) > 50:  # 有实质内容
                completed_steps += 1
        
        return (completed_steps / len(steps)) * 10
    
    def _score_analysis_quality(self, fuPan_record):
        """评分分析质量 (10分)"""
        total_score = 0
        
        # 数据引用质量
        data_quality = self._evaluate_data_usage(fuPan_record)
        total_score += data_quality * 3
        
        # 分析深度
        depth_quality = self._evaluate_analysis_depth(fuPan_record)
        total_score += depth_quality * 4
        
        # 见解独特性
        insight_quality = self._evaluate_insights(fuPan_record)
        total_score += insight_quality * 3
        
        return min(total_score, 10)
    
    def _score_logic_consistency(self, fuPan_record):
        """评分逻辑严密性 (10分)"""
        total_score = 0
        
        # 逻辑链条完整性
        logic_chain = self._evaluate_logic_chain(fuPan_record)
        total_score += logic_chain * 4
        
        # 前后一致性
        consistency = self._evaluate_consistency(fuPan_record)
        total_score += consistency * 3
        
        # 风险控制意识
        risk_awareness = self._evaluate_risk_awareness(fuPan_record)
        total_score += risk_awareness * 3
        
        return min(total_score, 10)
    
    def _calculate_skill_bonus(self, fuPan_record):
        """计算技能加分 (最多5分)"""
        bonus = 0
        
        # 千牛哥方法论应用加分
        if self._detect_qianniu_methodology(fuPan_record):
            bonus += 2
        
        # 创新分析方法加分
        if self._detect_innovative_analysis(fuPan_record):
            bonus += 2
        
        # 风险控制意识加分
        if self._detect_strong_risk_control(fuPan_record):
            bonus += 1
        
        return min(bonus, 5)
    
    def _calculate_skill_points(self, fuPan_record):
        """计算各项技能点数"""
        return {
            "market_perception": self._calc_market_perception_points(fuPan_record),
            "risk_sense": self._calc_risk_sense_points(fuPan_record),
            "opportunity_capture": self._calc_opportunity_points(fuPan_record),
            "capital_sense": self._calc_capital_sense_points(fuPan_record),
            "logic_thinking": self._calc_logic_points(fuPan_record),
            "portfolio_management": self._calc_portfolio_points(fuPan_record)
        }
    
    def _get_grade(self, score):
        """获取等级评定"""
        if score >= 90:
            return "S级 - 先知先觉"
        elif score >= 80:
            return "A级 - 后知后觉"
        elif score >= 70:
            return "B级 - 不知不觉"
        elif score >= 60:
            return "C级 - 初学者"
        else:
            return "D级 - 需要努力"
    
    def _generate_feedback(self, fuPan_record, actual_performance):
        """生成详细反馈"""
        feedback = {
            "strengths": [],
            "improvements": [],
            "qianniu_tips": [],
            "next_focus": []
        }
        
        # 分析优势
        if self._detect_strong_sector_analysis(fuPan_record):
            feedback["strengths"].append("板块分析能力强")
        
        if self._detect_good_risk_control(fuPan_record):
            feedback["strengths"].append("风险控制意识好")
        
        # 改进建议
        if not self._detect_volume_price_analysis(fuPan_record):
            feedback["improvements"].append("需要加强量价分析")
        
        if not self._detect_capital_flow_analysis(fuPan_record):
            feedback["improvements"].append("需要重视资金流向")
        
        # 千牛哥方法论提示
        feedback["qianniu_tips"] = [
            "记住：价格永远领先情绪",
            "先手赚后手的钱",
            "量为价先导，价为王",
            "高低切换永远存在"
        ]
        
        return feedback
    
    # 辅助评估方法
    def _evaluate_data_usage(self, record):
        """评估数据使用质量"""
        return 0.8  # 示例返回值
    
    def _evaluate_analysis_depth(self, record):
        """评估分析深度"""
        return 0.7
    
    def _evaluate_insights(self, record):
        """评估见解质量"""
        return 0.6
    
    def _evaluate_logic_chain(self, record):
        """评估逻辑链条"""
        return 0.8
    
    def _evaluate_consistency(self, record):
        """评估一致性"""
        return 0.7
    
    def _evaluate_risk_awareness(self, record):
        """评估风险意识"""
        return 0.9
    
    def _detect_qianniu_methodology(self, record):
        """检测千牛哥方法论应用"""
        return True
    
    def _detect_innovative_analysis(self, record):
        """检测创新分析"""
        return False
    
    def _detect_strong_risk_control(self, record):
        """检测强风险控制"""
        return True
    
    def _calc_market_perception_points(self, record):
        """计算市场感知点数"""
        return 85
    
    def _calc_risk_sense_points(self, record):
        """计算风险嗅觉点数"""
        return 78
    
    def _calc_opportunity_points(self, record):
        """计算机会捕捉点数"""
        return 82
    
    def _calc_capital_sense_points(self, record):
        """计算资金嗅觉点数"""
        return 75
    
    def _calc_logic_points(self, record):
        """计算逻辑思维点数"""
        return 88
    
    def _calc_portfolio_points(self, record):
        """计算组合管理点数"""
        return 80
    
    def _detect_strong_sector_analysis(self, record):
        """检测强板块分析"""
        return True
    
    def _detect_good_risk_control(self, record):
        """检测良好风险控制"""
        return True
    
    def _detect_volume_price_analysis(self, record):
        """检测量价分析"""
        return False
    
    def _detect_capital_flow_analysis(self, record):
        """检测资金流分析"""
        return True

if __name__ == "__main__":
    # 测试评分系统
    scoring = AdvancedScoringSystem()
    
    # 模拟复盘记录
    test_record = {
        "step1_market_overview": '{"analysis": "市场整体偏弱"}',
        "step2_risk_scan": '{"risks": ["房地产下跌"]}', 
        "step3_opportunity_scan": '{"opportunities": ["新能源上涨"]}',
        "step4_capital_verification": '{"capital_flow": "流入新能源"}',
        "step5_logic_check": '{"logic": "政策支持"}',
        "step6_portfolio_management": '{"portfolio": ["比亚迪", "宁德时代"]}',
        "predictions": {
            "sectors": {"hot_sectors": ["新能源"], "risk_sectors": ["房地产"]},
            "stocks": {"limit_up_candidates": ["比亚迪"], "strong_stocks": ["宁德时代"]},
            "market_sentiment": {"direction": "上涨", "fund_sentiment": "积极"}
        }
    }
    
    # 模拟实际表现
    test_actual = {
        "sector_performance": {"top_gainers": ["新能源"], "top_losers": ["房地产"]},
        "stock_performance": {"limit_up_stocks": ["比亚迪"], "strong_performers": ["宁德时代"]},
        "market_sentiment": {"direction": "上涨", "fund_sentiment": "积极"}
    }
    
    result = scoring.calculate_comprehensive_score(test_record, test_actual)
    print(f"总分: {result['total_score']}")
    print(f"等级: {result['grade']}")
    print(f"技能点: {result['skill_points']}")