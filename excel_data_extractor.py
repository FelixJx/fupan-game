#!/usr/bin/env python3
"""
Excel数据提取器 - 基于千牛哥复盘方法论
从重启人生计划表2.xlsx提取适合复盘体系的数据
"""

import pandas as pd
import os
import json
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import sqlite3

class ExcelDataExtractor:
    """Excel数据提取器 - 专为千牛哥复盘体系设计"""
    
    def __init__(self, excel_file_path, db_path="fuPan_game.db"):
        self.excel_file_path = excel_file_path
        self.db_path = db_path
        self.extraction_config = self._load_extraction_config()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化数据库
        self._init_extraction_database()
    
    def _load_extraction_config(self):
        """配置千牛哥六步复盘法的数据提取规则"""
        return {
            # 1️⃣ 市场鸟瞰数据
            "market_overview": {
                "sheets": ["整体市场数据", "情绪周期图"],
                "key_fields": ["日期", "涨停数", "跌停数", "连板数", "高度板高度", "炸板率", 
                             "成交量", "砸盘系数", "挣钱效应", "最高个股"]
            },
            
            # 2️⃣ 风险扫描数据
            "risk_scan": {
                "sheets": ["整体市场数据", "情绪周期图"],
                "key_fields": ["跌停数", "炸板数", "炸板率", "砸盘系数"]
            },
            
            # 3️⃣ 机会扫描数据
            "opportunity_scan": {
                "sheets": ["5日连扳梯队", "题材梯队", "题材领涨股", "涨停信息"],
                "key_fields": ["连板数", "题材轮动", "涨停原因", "最高个股"]
            },
            
            # 4️⃣ 资金验证数据
            "capital_verification": {
                "sheets": ["成交额环比股", "大单净额股历史", "游资方向", "龙虎榜"],
                "key_fields": ["成交额", "大单净额", "游资方向", "龙虎榜资金"]
            },
            
            # 5️⃣ 逻辑核对数据
            "logic_check": {
                "sheets": ["每日新闻消息面", "涨停原因", "题材轮动数据集"],
                "key_fields": ["新闻", "涨停原因", "题材轮动"]
            },
            
            # 6️⃣ 标记分组数据
            "portfolio_management": {
                "sheets": ["行业龙头", "AI模型精选优质股", "游资目录"],
                "key_fields": ["行业龙头", "优质股", "游资"]
            }
        }
    
    def _init_extraction_database(self):
        """初始化数据提取数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建提取数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extracted_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                data_type TEXT NOT NULL,
                sheet_name TEXT NOT NULL,
                data_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建每日汇总表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                market_overview TEXT,
                risk_scan TEXT,
                opportunity_scan TEXT,
                capital_verification TEXT,
                logic_check TEXT,
                portfolio_management TEXT,
                extraction_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def extract_all_data(self, target_date=None):
        """提取所有适合复盘体系的数据"""
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"🎮 开始提取 {target_date} 的复盘数据...")
        
        try:
            # 读取Excel文件
            excel_data = pd.ExcelFile(self.excel_file_path)
            extraction_result = {
                "date": target_date,
                "extraction_time": datetime.now().isoformat(),
                "data": {}
            }
            
            # 按千牛哥六步法提取数据
            for step_name, config in self.extraction_config.items():
                step_data = self._extract_step_data(excel_data, step_name, config, target_date)
                extraction_result["data"][step_name] = step_data
                
                self.logger.info(f"✅ {step_name} 数据提取完成")
            
            # 保存到数据库
            self._save_extraction_result(extraction_result)
            
            self.logger.info(f"🎯 {target_date} 数据提取完成！")
            return extraction_result
            
        except Exception as e:
            self.logger.error(f"❌ 数据提取失败: {e}")
            return None
    
    def _extract_step_data(self, excel_data, step_name, config, target_date):
        """提取单个步骤的数据"""
        step_data = {}
        
        for sheet_name in config["sheets"]:
            if sheet_name in excel_data.sheet_names:
                try:
                    df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
                    
                    # 根据步骤类型提取相应数据
                    extracted = self._extract_sheet_data(df, sheet_name, step_name, target_date)
                    if extracted:
                        step_data[sheet_name] = extracted
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ 工作表 {sheet_name} 提取失败: {e}")
        
        return step_data
    
    def _extract_sheet_data(self, df, sheet_name, step_name, target_date):
        """从具体工作表提取数据"""
        
        if sheet_name == "整体市场数据":
            return self._extract_market_data(df, target_date)
        
        elif sheet_name == "情绪周期图":
            return self._extract_emotion_data(df, target_date)
        
        elif sheet_name == "5日连扳梯队":
            return self._extract_continuous_board_data(df, target_date)
        
        elif sheet_name == "题材梯队":
            return self._extract_theme_data(df, target_date)
        
        elif sheet_name == "涨停信息":
            return self._extract_limit_up_data(df, target_date)
        
        elif sheet_name == "龙虎榜":
            return self._extract_dragon_tiger_data(df, target_date)
        
        elif sheet_name == "每日新闻消息面":
            return self._extract_news_data(df, target_date)
        
        # 其他工作表的通用提取
        return self._extract_generic_data(df, sheet_name, target_date)
    
    def _extract_market_data(self, df, target_date):
        """提取整体市场数据 - 市场鸟瞰"""
        try:
            # 查找最新日期数据
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
                latest_data = df.dropna(subset=['日期']).tail(1)
                
                if not latest_data.empty:
                    # 转换numpy数据类型为Python原生类型
                    market_data = {
                        "date": latest_data['日期'].iloc[0].strftime('%Y-%m-%d'),
                        "limit_up_count": int(latest_data.get('涨停数', [0]).iloc[0]) if pd.notna(latest_data.get('涨停数', [0]).iloc[0]) else 0,
                        "limit_down_count": int(latest_data.get('跌停数', [0]).iloc[0]) if pd.notna(latest_data.get('跌停数', [0]).iloc[0]) else 0,
                        "continuous_boards": int(latest_data.get('连板数', [0]).iloc[0]) if pd.notna(latest_data.get('连板数', [0]).iloc[0]) else 0,
                        "highest_board": int(latest_data.get('高度板高度', [0]).iloc[0]) if pd.notna(latest_data.get('高度板高度', [0]).iloc[0]) else 0,
                        "blow_up_count": int(latest_data.get('炸板数', [0]).iloc[0]) if pd.notna(latest_data.get('炸板数', [0]).iloc[0]) else 0,
                        "blow_up_rate": float(latest_data.get('炸板率', [0]).iloc[0]) if pd.notna(latest_data.get('炸板率', [0]).iloc[0]) else 0.0,
                        "volume": float(latest_data.get('成交量', [0]).iloc[0]) if pd.notna(latest_data.get('成交量', [0]).iloc[0]) else 0.0,
                        "top_stock": str(latest_data.get('最高个股', ['无']).iloc[0]) if pd.notna(latest_data.get('最高个股', ['无']).iloc[0]) else "无",
                        "up_count": int(latest_data.get('上涨数', [0]).iloc[0]) if pd.notna(latest_data.get('上涨数', [0]).iloc[0]) else 0,
                        "down_count": int(latest_data.get('下跌数', [0]).iloc[0]) if pd.notna(latest_data.get('下跌数', [0]).iloc[0]) else 0
                    }
                    
                    # 千牛哥分析
                    market_data["qianniu_analysis"] = self._analyze_market_sentiment(market_data)
                    
                    return market_data
        except Exception as e:
            self.logger.error(f"整体市场数据提取失败: {e}")
        
        return None
    
    def _extract_emotion_data(self, df, target_date):
        """提取情绪周期数据 - 风险嗅觉"""
        try:
            if len(df) > 0:
                latest_data = df.tail(1)
                
                emotion_data = {
                    "blow_up_ratio": float(latest_data.get('砸盘系数1', [0]).iloc[0]) if '砸盘系数1' in df.columns and pd.notna(latest_data.get('砸盘系数1', [0]).iloc[0]) else 0.0,
                    "money_effect": int(latest_data.get('挣钱效应', [0]).iloc[0]) if '挣钱效应' in df.columns and pd.notna(latest_data.get('挣钱效应', [0]).iloc[0]) else 0,
                    "emotion_cycle": "分析中",
                    "risk_level": "中等"
                }
                
                # 千牛哥情绪分析
                emotion_data["qianniu_emotion"] = self._analyze_emotion_cycle(emotion_data)
                
                return emotion_data
        except Exception as e:
            self.logger.error(f"情绪周期数据提取失败: {e}")
        
        return None
    
    def _extract_continuous_board_data(self, df, target_date):
        """提取连板梯队数据 - 机会捕捉"""
        try:
            board_data = {
                "date": target_date,
                "boards": {},
                "themes": [],
                "leading_stocks": []
            }
            
            # 分析连板梯队结构
            for col in df.columns:
                if 'Unnamed' not in str(col) and df[col].notna().any():
                    # 提取连板信息
                    valid_data = df[col].dropna().astype(str)
                    if len(valid_data) > 0:
                        board_data["themes"].extend([x for x in valid_data.tolist()[:5] if '板' in x])
            
            # 千牛哥连板分析
            board_data["qianniu_board_analysis"] = self._analyze_board_structure(board_data)
            
            return board_data
        except Exception as e:
            self.logger.error(f"连板数据提取失败: {e}")
        
        return None
    
    def _extract_theme_data(self, df, target_date):
        """提取题材梯队数据 - 逻辑分析"""
        try:
            theme_data = {
                "date": target_date,
                "hot_themes": [],
                "theme_structure": {},
                "leading_themes": []
            }
            
            # 提取题材信息
            if len(df) > 0:
                for idx, row in df.head(5).iterrows():
                    for col in df.columns:
                        cell_value = str(row[col])
                        if pd.notna(row[col]) and len(cell_value) > 2:
                            # 识别题材关键词
                            if any(keyword in cell_value for keyword in ['医药', '新能源', '人工智能', '机器人', '光伏']):
                                if cell_value not in theme_data["hot_themes"]:
                                    theme_data["hot_themes"].append(cell_value)
            
            # 千牛哥题材分析
            theme_data["qianniu_theme_analysis"] = self._analyze_theme_rotation(theme_data)
            
            return theme_data
        except Exception as e:
            self.logger.error(f"题材数据提取失败: {e}")
        
        return None
    
    def _extract_limit_up_data(self, df, target_date):
        """提取涨停数据"""
        try:
            return {
                "date": target_date,
                "limit_up_stocks": df.head(20).to_dict('records') if len(df) > 0 else [],
                "count": len(df)
            }
        except Exception as e:
            self.logger.error(f"涨停数据提取失败: {e}")
        return None
    
    def _extract_dragon_tiger_data(self, df, target_date):
        """提取龙虎榜数据 - 资金验证"""
        try:
            return {
                "date": target_date,
                "dragon_tiger_list": df.head(10).to_dict('records') if len(df) > 0 else [],
                "hot_money_direction": "分析中"
            }
        except Exception as e:
            self.logger.error(f"龙虎榜数据提取失败: {e}")
        return None
    
    def _extract_news_data(self, df, target_date):
        """提取新闻数据 - 逻辑核对"""
        try:
            return {
                "date": target_date,
                "news_summary": df.head(10).to_dict('records') if len(df) > 0 else [],
                "hot_topics": []
            }
        except Exception as e:
            self.logger.error(f"新闻数据提取失败: {e}")
        return None
    
    def _extract_generic_data(self, df, sheet_name, target_date):
        """通用数据提取"""
        try:
            return {
                "sheet_name": sheet_name,
                "date": target_date,
                "data_summary": f"共{len(df)}行数据",
                "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
            }
        except Exception as e:
            self.logger.error(f"{sheet_name}通用数据提取失败: {e}")
        return None
    
    def _analyze_market_sentiment(self, market_data):
        """千牛哥市场情绪分析"""
        limit_up = market_data.get('limit_up_count', 0)
        limit_down = market_data.get('limit_down_count', 0)
        blow_up_rate = market_data.get('blow_up_rate', 0)
        
        if limit_up > 80 and blow_up_rate < 0.3:
            return "强势市场，情绪高涨，注意高位风险"
        elif limit_up > 50 and blow_up_rate < 0.4:
            return "偏强市场，情绪较好，可积极参与"
        elif limit_up < 30 or blow_up_rate > 0.5:
            return "弱势市场，情绪低迷，以防守为主"
        else:
            return "震荡市场，情绪中性，精选个股"
    
    def _analyze_emotion_cycle(self, emotion_data):
        """千牛哥情绪周期分析"""
        blow_up_ratio = emotion_data.get('blow_up_ratio', 0)
        money_effect = emotion_data.get('money_effect', 0)
        
        if blow_up_ratio > 2 and money_effect < 3:
            return "情绪退潮期，高标避险，等待新周期"
        elif blow_up_ratio < 1 and money_effect > 5:
            return "情绪启动期，可关注低位机会"
        else:
            return "情绪中继期，保持观察"
    
    def _analyze_board_structure(self, board_data):
        """千牛哥连板结构分析"""
        themes_count = len(board_data.get('themes', []))
        
        if themes_count > 10:
            return "连板梯队完整，有持续性，主线明确"
        elif themes_count > 5:
            return "连板梯队较好，可关注龙头"
        else:
            return "连板梯队不完整，谨慎参与"
    
    def _analyze_theme_rotation(self, theme_data):
        """千牛哥题材轮动分析"""
        hot_themes = theme_data.get('hot_themes', [])
        
        medical_count = sum(1 for theme in hot_themes if '医药' in theme)
        tech_count = sum(1 for theme in hot_themes if any(x in theme for x in ['人工智能', '芯片', '机器人']))
        
        if medical_count > tech_count:
            return "医药题材占主导，防御性较强"
        elif tech_count > medical_count:
            return "科技题材活跃，成长性较好"
        else:
            return "题材轮动均衡，多元化格局"
    
    def _save_extraction_result(self, result):
        """保存提取结果到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        date = result["date"]
        
        # 保存详细数据
        for data_type, data_content in result["data"].items():
            for sheet_name, sheet_data in data_content.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO extracted_data 
                    (date, data_type, sheet_name, data_content)
                    VALUES (?, ?, ?, ?)
                ''', (date, data_type, sheet_name, json.dumps(sheet_data, ensure_ascii=False)))
        
        # 保存每日汇总
        cursor.execute('''
            INSERT OR REPLACE INTO daily_summary 
            (date, market_overview, risk_scan, opportunity_scan, 
             capital_verification, logic_check, portfolio_management, extraction_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date,
            json.dumps(result["data"].get("market_overview", {}), ensure_ascii=False),
            json.dumps(result["data"].get("risk_scan", {}), ensure_ascii=False),
            json.dumps(result["data"].get("opportunity_scan", {}), ensure_ascii=False),
            json.dumps(result["data"].get("capital_verification", {}), ensure_ascii=False),
            json.dumps(result["data"].get("logic_check", {}), ensure_ascii=False),
            json.dumps(result["data"].get("portfolio_management", {}), ensure_ascii=False),
            "completed"
        ))
        
        conn.commit()
        conn.close()
    
    def get_daily_data(self, date):
        """获取指定日期的复盘数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM daily_summary WHERE date = ?', (date,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                "date": result[1],
                "market_overview": json.loads(result[2]) if result[2] else {},
                "risk_scan": json.loads(result[3]) if result[3] else {},
                "opportunity_scan": json.loads(result[4]) if result[4] else {},
                "capital_verification": json.loads(result[5]) if result[5] else {},
                "logic_check": json.loads(result[6]) if result[6] else {},
                "portfolio_management": json.loads(result[7]) if result[7] else {},
                "status": result[8]
            }
        
        return None

# 自动文档监控类
class DocumentMonitor:
    """文档监控器 - 自动检测新Excel文件"""
    
    def __init__(self, watch_directory, extractor_class=ExcelDataExtractor):
        self.watch_directory = Path(watch_directory)
        self.extractor_class = extractor_class
        self.processed_files = set()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def scan_for_new_files(self):
        """扫描新的Excel文件"""
        excel_files = list(self.watch_directory.glob("*.xlsx"))
        excel_files.extend(list(self.watch_directory.glob("*.xls")))
        
        new_files = []
        for file_path in excel_files:
            if file_path.name not in self.processed_files:
                new_files.append(file_path)
                self.processed_files.add(file_path.name)
        
        return new_files
    
    def process_new_files(self):
        """处理新发现的Excel文件"""
        new_files = self.scan_for_new_files()
        
        for file_path in new_files:
            self.logger.info(f"🔍 发现新文件: {file_path.name}")
            
            try:
                # 创建提取器并提取数据
                extractor = self.extractor_class(str(file_path))
                result = extractor.extract_all_data()
                
                if result:
                    self.logger.info(f"✅ {file_path.name} 数据提取成功")
                else:
                    self.logger.error(f"❌ {file_path.name} 数据提取失败")
                    
            except Exception as e:
                self.logger.error(f"❌ 处理文件 {file_path.name} 时出错: {e}")

if __name__ == "__main__":
    # 测试数据提取
    excel_file = "/Users/jx/Desktop/stock-agent3.0/重启人生计划表2.xlsx"
    
    print("🎮 Excel数据提取器测试")
    print("基于千牛哥复盘方法论")
    print("=" * 50)
    
    if os.path.exists(excel_file):
        extractor = ExcelDataExtractor(excel_file)
        result = extractor.extract_all_data()
        
        if result:
            print("✅ 数据提取成功！")
            print(f"📊 提取日期: {result['date']}")
            print(f"🎯 数据步骤: {list(result['data'].keys())}")
            
            # 显示市场概览样本
            market_data = result['data'].get('market_overview', {})
            if market_data:
                print("\n📈 市场概览样本:")
                for sheet, data in market_data.items():
                    if data:
                        print(f"  {sheet}: {data.get('qianniu_analysis', '数据获取成功')}")
        else:
            print("❌ 数据提取失败")
    else:
        print(f"❌ Excel文件不存在: {excel_file}")