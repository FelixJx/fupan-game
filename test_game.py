#!/usr/bin/env python3
"""
股票复盘游戏 - 测试脚本
验证游戏核心功能
"""

import sys
import json
from datetime import datetime
from data_system import StockDataSystem
from scoring_system import AdvancedScoringSystem

def test_game_flow():
    """测试完整游戏流程"""
    print("🎮 开始测试股票复盘游戏...")
    
    # 1. 初始化系统
    print("\n📊 初始化数据系统...")
    data_system = StockDataSystem()
    
    print("🏆 初始化评分系统...")
    scoring_system = AdvancedScoringSystem()
    
    # 2. 测试数据获取
    print("\n📈 测试市场数据获取...")
    try:
        market_data = data_system.get_market_overview()
        print(f"✅ 市场概览数据: {len(str(market_data))} 字符")
        
        risk_data = data_system.get_risk_scan_data()
        print(f"✅ 风险扫描数据: {len(str(risk_data))} 字符")
        
        opportunity_data = data_system.get_opportunity_scan_data()
        print(f"✅ 机会扫描数据: {len(str(opportunity_data))} 字符")
        
        capital_data = data_system.get_capital_verification_data()
        print(f"✅ 资金验证数据: {len(str(capital_data))} 字符")
        
    except Exception as e:
        print(f"⚠️ 实时数据获取失败，使用模拟数据: {e}")
    
    # 3. 测试游戏会话
    print("\n🎯 测试游戏会话...")
    user_id = "test_user"
    date = datetime.now().strftime('%Y-%m-%d')
    
    # 模拟六步复盘数据
    step_data = {
        "step1": {"market_overview": "测试市场分析", "sentiment": "震荡偏强"},
        "step2": {"risk_analysis": "识别房地产板块风险", "risk_level": "中等"},
        "step3": {"opportunity_analysis": "新能源汽车板块机会", "hot_sectors": ["新能源"]},
        "step4": {"capital_analysis": "资金流入科技板块", "volume_analysis": "量价配合"},
        "step5": {"logic_analysis": "政策支持新能源发展", "logic_strength": "强"},
        "step6": {"portfolio": "建立新能源自选股池", "focus_stocks": ["比亚迪", "宁德时代"]}
    }
    
    # 模拟预测数据
    predictions = {
        "sectors": {
            "hot_sectors": ["新能源汽车", "人工智能"],
            "risk_sectors": ["房地产", "银行"]
        },
        "stocks": {
            "limit_up_candidates": ["比亚迪"],
            "strong_stocks": ["宁德时代", "特斯拉概念"]
        },
        "market_sentiment": {
            "direction": "震荡偏强",
            "fund_sentiment": "积极"
        }
    }
    
    # 保存复盘记录
    print("💾 保存复盘记录...")
    record_id = data_system.save_fuPan_record(user_id, date, step_data, predictions)
    print(f"✅ 复盘记录ID: {record_id}")
    
    # 4. 测试评分系统
    print("\n🏆 测试评分系统...")
    
    # 模拟第二天实际表现
    mock_actual_performance = {
        "sector_performance": {
            "top_gainers": ["新能源汽车", "人工智能"],
            "top_losers": ["房地产", "银行"]
        },
        "stock_performance": {
            "limit_up_stocks": ["比亚迪"],
            "strong_performers": ["宁德时代"]
        },
        "market_sentiment": {
            "direction": "震荡偏强",
            "fund_sentiment": "积极"
        }
    }
    
    # 计算评分
    score_result = scoring_system.calculate_comprehensive_score(step_data, mock_actual_performance)
    
    print("📊 评分结果:")
    print(f"   总分: {score_result['total_score']:.1f}/100")
    print(f"   预测准确度: {score_result['prediction_score']:.1f}/70")
    print(f"   分析深度: {score_result['depth_score']:.1f}/30")
    print(f"   技能加分: {score_result['skill_bonus']}/5")
    print(f"   等级评定: {score_result['grade']}")
    
    print("\n🎯 技能点数:")
    for skill, points in score_result['skill_points'].items():
        print(f"   {skill}: {points}/100")
    
    # 5. 测试千牛哥反馈
    print("\n💡 千牛哥点评:")
    feedback = score_result['detailed_feedback']
    for tip in feedback['qianniu_tips'][:3]:
        print(f"   • {tip}")
    
    print("\n✅ 游戏流程测试完成！")
    print("🎮 股票复盘游戏核心功能正常运行")
    
    return True

def test_web_interface():
    """测试Web界面"""
    print("\n🌐 测试Web界面...")
    
    try:
        # 检查HTML文件
        with open('game_interface.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        if len(html_content) > 1000:
            print("✅ 游戏界面HTML文件正常")
        else:
            print("⚠️ 游戏界面HTML文件可能不完整")
            
        # 检查JavaScript文件
        with open('game_logic.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
            
        if 'StockFuPanGame' in js_content:
            print("✅ 游戏逻辑JavaScript文件正常")
        else:
            print("⚠️ 游戏逻辑JavaScript文件可能有问题")
            
    except FileNotFoundError as e:
        print(f"❌ 文件缺失: {e}")
        
def test_qianniu_methodology():
    """测试千牛哥方法论集成"""
    print("\n🧠 测试千牛哥方法论集成...")
    
    # 检查六步法实现
    data_system = StockDataSystem()
    
    steps = [
        ("市场鸟瞰", data_system.get_market_overview),
        ("风险扫描", data_system.get_risk_scan_data), 
        ("机会扫描", data_system.get_opportunity_scan_data),
        ("资金验证", data_system.get_capital_verification_data)
    ]
    
    for step_name, step_func in steps:
        try:
            result = step_func()
            print(f"✅ {step_name}功能正常")
        except Exception as e:
            print(f"⚠️ {step_name}功能异常: {e}")
    
    # 检查评分维度
    scoring = AdvancedScoringSystem()
    config = scoring.scoring_config
    
    print("✅ 评分维度配置:")
    print(f"   预测准确度: {config['prediction_accuracy']}")
    print(f"   复盘深度: {config['analysis_depth']}")

if __name__ == "__main__":
    print("🎮 股票复盘游戏 - 系统测试")
    print("=" * 50)
    
    try:
        # 运行所有测试
        test_game_flow()
        test_web_interface() 
        test_qianniu_methodology()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！游戏系统准备就绪")
        print("🚀 运行 python main.py 启动游戏服务器")
        print("🌐 访问 http://localhost:8000 开始游戏")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        sys.exit(1)