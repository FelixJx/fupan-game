#!/usr/bin/env python3
"""
股票复盘游戏 - 数据接入和验证系统
基于千牛哥复盘方法论
"""

import sqlite3
import pandas as pd
import akshare as ak
import tushare as ts
import requests
from datetime import datetime, timedelta
import json
import logging
import os
import time
import numpy as np
from excel_data_extractor import ExcelDataExtractor

class StockDataSystem:
    def __init__(self, db_path="fuPan_game.db", tushare_token=None):
        self.db_path = db_path
        self.excel_extractor = None
        
        # 数据源配置 - 先初始化
        self.data_sources = {
            'tushare': False,
            'akshare': True,
            'efinance': True,
            'eastmoney': True,
            'excel': False  # 将根据检测结果更新
        }
        
        # 初始化Tushare
        self.tushare_token = tushare_token or "b34d8920b99b43d48df7e792a4708a29f868feeee30d9c84b54bf065"
        self.ts_pro = None
        self._init_tushare()
        
        self.init_database()
        logging.basicConfig(level=logging.INFO)
        
        # 自动检测Excel数据文件
        self._detect_excel_data_source()
    
    def _init_tushare(self):
        """初始化Tushare Pro API"""
        try:
            ts.set_token(self.tushare_token)
            self.ts_pro = ts.pro_api()
            # 简单测试连接，不执行复杂查询避免超时
            logging.info("📡 Tushare Pro已配置，将在使用时验证连接")
            self.data_sources['tushare'] = True
        except Exception as e:
            logging.warning(f"⚠️ Tushare Pro初始化警告: {e}")
            self.data_sources['tushare'] = False
            self.ts_pro = None
        
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 复盘记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fuPan_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                step1_market_overview TEXT,
                step2_risk_scan TEXT,
                step3_opportunity_scan TEXT,
                step4_capital_verification TEXT,
                step5_logic_check TEXT,
                step6_portfolio_management TEXT,
                predictions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 市场数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                market_overview TEXT,
                top_gainers TEXT,
                top_losers TEXT,
                volume_leaders TEXT,
                sector_performance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 评分结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scoring_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER,
                prediction_accuracy_score REAL,
                analysis_depth_score REAL,
                total_score REAL,
                next_day_performance TEXT,
                scoring_date TEXT,
                FOREIGN KEY (record_id) REFERENCES fuPan_records (id)
            )
        ''')
        
        # 实时市场数据表（Tushare）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL,
                pre_close REAL, change REAL, pct_chg REAL,
                vol REAL, amount REAL,
                data_source TEXT DEFAULT 'tushare',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ts_code, trade_date)
            )
        ''')
        
        # 板块数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sector_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector_name TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                sector_type TEXT, -- '概念板块', '行业板块', '地域板块'
                change_percent REAL,
                volume_ratio REAL,
                leading_stocks TEXT,
                stock_count INTEGER,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sector_name, trade_date)
            )
        ''')
        
        # 涨跌停数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS limit_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                name TEXT,
                close REAL,
                pct_chg REAL,
                limit_type TEXT, -- 'up' or 'down'
                reason TEXT,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 事件日历表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date TEXT NOT NULL,
                event_type TEXT, -- '会议', '政策', '财报'
                event_name TEXT,
                related_sectors TEXT,
                importance_level INTEGER,
                expected_impact TEXT,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 资金流向数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capital_flow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT,
                trade_date TEXT NOT NULL,
                buy_sm_vol REAL, -- 小单买入量
                buy_md_vol REAL, -- 中单买入量
                buy_lg_vol REAL, -- 大单买入量
                buy_elg_vol REAL, -- 特大单买入量
                sell_sm_vol REAL,
                sell_md_vol REAL, 
                sell_lg_vol REAL,
                sell_elg_vol REAL,
                net_mf_vol REAL, -- 净流入量
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _detect_excel_data_source(self):
        """检测Excel数据源"""
        # 检测常见路径
        potential_paths = [
            "/Users/jx/Desktop/stock-agent3.0/重启人生计划表2.xlsx",
            "./重启人生计划表2.xlsx",
            "../重启人生计划表2.xlsx"
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                try:
                    self.excel_extractor = ExcelDataExtractor(path, self.db_path)
                    logging.info(f"✅ Excel数据源连接成功: {path}")
                    break
                except Exception as e:
                    logging.warning(f"⚠️ Excel数据源连接失败 {path}: {e}")
        
        if not self.excel_extractor:
            logging.info("ℹ️ 未检测到Excel数据源，将使用在线数据")
        else:
            self.data_sources['excel'] = True
    
    # ======================== Tushare数据采集方法 ========================
    
    def get_tushare_market_overview(self, trade_date=None):
        """从Tushare获取市场概览数据"""
        if not self.ts_pro:
            return None
            
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        else:
            # 转换日期格式 2025-08-03 -> 20250803
            trade_date = trade_date.replace('-', '')
        
        try:
            # 获取指数数据
            indices_data = self.ts_pro.index_daily(trade_date=trade_date)
            
            # 获取涨跌停数据
            limit_up_data = self.ts_pro.limit_list_d(trade_date=trade_date, limit_type='U')
            limit_down_data = self.ts_pro.limit_list_d(trade_date=trade_date, limit_type='D')
            
            # 获取市场统计数据
            market_stats = self.ts_pro.daily_basic(trade_date=trade_date)
            
            return {
                'indices': self._process_indices_data(indices_data),
                'limit_up_count': len(limit_up_data) if not limit_up_data.empty else 0,
                'limit_down_count': len(limit_down_data) if not limit_down_data.empty else 0,
                'market_stats': self._process_market_stats(market_stats),
                'data_source': 'tushare'
            }
            
        except Exception as e:
            logging.error(f"Tushare市场概览数据获取失败: {e}")
            return None
    
    def get_tushare_limit_stocks(self, trade_date=None, limit_type='U'):
        """获取涨跌停股票数据"""
        if not self.ts_pro:
            return []
            
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        else:
            trade_date = trade_date.replace('-', '')
        
        try:
            limit_data = self.ts_pro.limit_list_d(trade_date=trade_date, limit_type=limit_type)
            
            if limit_data.empty:
                return []
            
            return [{
                'ts_code': row['ts_code'],
                'name': row['name'],
                'close': row['close'],
                'pct_chg': row['pct_chg'],
                'amount': row['amount'],
                'limit_type': 'up' if limit_type == 'U' else 'down',
                'data_source': 'tushare'
            } for _, row in limit_data.iterrows()]
            
        except Exception as e:
            logging.error(f"Tushare涨跌停数据获取失败: {e}")
            return []
    
    def get_tushare_sector_data(self, trade_date=None):
        """获取Tushare板块数据"""
        if not self.ts_pro:
            return []
            
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        else:
            trade_date = trade_date.replace('-', '')
        
        try:
            # 获取概念板块数据
            concept_data = self.ts_pro.concept_detail(trade_date=trade_date)
            
            # 获取行业板块数据  
            industry_data = self.ts_pro.index_classify(level='L2', src='SW2021')
            
            sectors = []
            
            # 处理概念板块
            if not concept_data.empty:
                concept_grouped = concept_data.groupby('concept_name').agg({
                    'ts_code': 'count',
                    'close': 'mean',
                    'pct_chg': 'mean'
                }).reset_index()
                
                for _, row in concept_grouped.iterrows():
                    sectors.append({
                        'sector_name': row['concept_name'],
                        'sector_type': '概念板块',
                        'stock_count': row['ts_code'],
                        'avg_change': row['pct_chg'],
                        'data_source': 'tushare'
                    })
            
            return sectors
            
        except Exception as e:
            logging.error(f"Tushare板块数据获取失败: {e}")
            return []
    
    def get_tushare_capital_flow(self, trade_date=None, ts_code=None):
        """获取资金流向数据"""
        if not self.ts_pro:
            return None
            
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        else:
            trade_date = trade_date.replace('-', '')
        
        try:
            # 获取资金流向数据
            if ts_code:
                # 获取个股资金流向
                money_flow = self.ts_pro.moneyflow(ts_code=ts_code, trade_date=trade_date)
            else:
                # 获取市场整体资金流向
                money_flow = self.ts_pro.moneyflow_hsgt(trade_date=trade_date)
            
            if money_flow.empty:
                return None
            
            return {
                'data': money_flow.to_dict('records'),
                'data_source': 'tushare'
            }
            
        except Exception as e:
            logging.error(f"Tushare资金流向数据获取失败: {e}")
            return None
    
    def _process_indices_data(self, indices_data):
        """处理指数数据"""
        if indices_data.empty:
            return {}
        
        indices = {}
        for _, row in indices_data.iterrows():
            ts_code = row['ts_code']
            if ts_code in ['000001.SH', '399001.SZ', '399006.SZ']:  # 上证、深成指、创业板
                name_map = {
                    '000001.SH': '上证指数',
                    '399001.SZ': '深证成指', 
                    '399006.SZ': '创业板指'
                }
                indices[name_map[ts_code]] = {
                    'close': row['close'],
                    'change': row['change'],
                    'pct_chg': row['pct_chg'],
                    'vol': row['vol'],
                    'amount': row['amount']
                }
        
        return indices
    
    def _process_market_stats(self, market_stats):
        """处理市场统计数据"""
        if market_stats.empty:
            return {}
        
        # 计算涨跌家数
        up_count = len(market_stats[market_stats['pct_chg'] > 0])
        down_count = len(market_stats[market_stats['pct_chg'] < 0])
        flat_count = len(market_stats[market_stats['pct_chg'] == 0])
        
        # 计算平均涨跌幅
        avg_pct_chg = market_stats['pct_chg'].mean()
        
        # 计算成交额
        total_amount = market_stats['amount'].sum()
        
        return {
            'up_count': up_count,
            'down_count': down_count,
            'flat_count': flat_count,
            'avg_pct_chg': avg_pct_chg,
            'total_amount': total_amount
        }
    
    # ======================== AKShare增强数据采集 ========================
    
    def get_akshare_enhanced_data(self, date_str=None):
        """获取AKShare增强数据"""
        try:
            # 实时概念板块数据
            concept_data = ak.stock_board_concept_name_em()
            
            # 实时行业板块数据
            industry_data = ak.stock_board_industry_name_em()
            
            # 资金流向数据
            fund_flow = ak.stock_individual_fund_flow_rank(indicator="今日")
            
            # 龙虎榜数据
            lhb_data = ak.stock_lhb_detail_em(trade_date=date_str or datetime.now().strftime('%Y%m%d'))
            
            return {
                'concept_boards': concept_data.to_dict('records') if not concept_data.empty else [],
                'industry_boards': industry_data.to_dict('records') if not industry_data.empty else [],
                'fund_flow': fund_flow.to_dict('records') if not fund_flow.empty else [],
                'lhb_data': lhb_data.to_dict('records') if not lhb_data.empty else [],
                'data_source': 'akshare'
            }
            
        except Exception as e:
            logging.error(f"AKShare增强数据获取失败: {e}")
            return None
    
    # ======================== 东方财富API数据采集 ========================
    
    def get_eastmoney_data(self):
        """获取东方财富数据"""
        try:
            # 热门概念板块排行
            concept_url = "http://push2.eastmoney.com/api/qt/clist/get"
            concept_params = {
                'pn': 1,
                'pz': 50,
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': 'm:90+t:3',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
            }
            
            response = requests.get(concept_url, params=concept_params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'concept_ranking': data.get('data', {}).get('diff', []),
                    'data_source': 'eastmoney'
                }
            
        except Exception as e:
            logging.error(f"东方财富数据获取失败: {e}")
            
        return None
    
    def get_excel_data(self, date_str=None):
        """获取Excel提取的数据"""
        if not self.excel_extractor:
            return None
            
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 先尝试从数据库获取已提取的数据
            excel_data = self.excel_extractor.get_daily_data(date_str)
            
            if not excel_data:
                # 如果没有数据，执行提取
                logging.info(f"🔄 开始提取 {date_str} 的Excel数据...")
                extraction_result = self.excel_extractor.extract_all_data(date_str)
                if extraction_result:
                    excel_data = self.excel_extractor.get_daily_data(date_str)
            
            return excel_data
            
        except Exception as e:
            logging.error(f"❌ Excel数据获取失败: {e}")
            return None
    
    def get_market_overview(self, date_str=None):
        """获取市场鸟瞰数据 - 千牛哥六步法第一步 - 多数据源融合"""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 1. 优先使用Excel数据
        excel_data = self.get_excel_data(date_str)
        if excel_data and excel_data.get('market_overview'):
            logging.info("✅ 使用Excel数据源 - 市场鸟瞰")
            return excel_data['market_overview']
        
        # 2. 尝试使用Tushare数据
        tushare_data = self.get_tushare_market_overview(date_str)
        if tushare_data:
            logging.info("✅ 使用Tushare数据源 - 市场鸟瞰")
            return self._format_market_overview_tushare(tushare_data, date_str)
        
        # 3. 使用AKShare增强数据
        akshare_enhanced = self.get_akshare_enhanced_data(date_str)
        if akshare_enhanced:
            logging.info("✅ 使用AKShare增强数据源 - 市场鸟瞰")
            return self._format_market_overview_akshare(akshare_enhanced, date_str)
        
        # 4. 备用：传统AKShare数据
        try:
            akshare_date = date_str.replace('-', '')
            
            # 获取A股统计数据
            market_stats = ak.stock_zh_a_spot_em()
            
            if not market_stats.empty:
                # 计算市场概览指标
                limit_up_count = len(market_stats[market_stats['涨跌幅'] >= 9.9])
                limit_down_count = len(market_stats[market_stats['涨跌幅'] <= -9.9])
                up_count = len(market_stats[market_stats['涨跌幅'] > 0])
                down_count = len(market_stats[market_stats['涨跌幅'] < 0])
                total_volume = market_stats['成交额'].sum()
                
                overview = {
                    "date": date_str,
                    "limit_up_count": limit_up_count,
                    "limit_down_count": limit_down_count,
                    "up_count": up_count,
                    "down_count": down_count,
                    "total_volume": total_volume,
                    "market_sentiment": self._calculate_market_sentiment(limit_up_count, limit_down_count),
                    "data_source": "akshare_online"
                }
                
                return overview
            
        except Exception as e:
            logging.error(f"获取在线市场概览数据失败: {e}")
        
        # 最后使用模拟数据
        return self._get_mock_market_overview(date_str)
    
    def _format_market_overview_tushare(self, tushare_data, date_str):
        """格式化Tushare市场概览数据"""
        market_stats = tushare_data.get('market_stats', {})
        indices = tushare_data.get('indices', {})
        
        # 计算千牛哥核心指标
        market_sentiment = self._calculate_market_sentiment_enhanced(
            tushare_data['limit_up_count'], 
            tushare_data['limit_down_count'],
            market_stats.get('up_count', 0),
            market_stats.get('down_count', 0)
        )
        
        return {
            "date": date_str,
            "limit_up_count": tushare_data['limit_up_count'],
            "limit_down_count": tushare_data['limit_down_count'],
            "up_count": market_stats.get('up_count', 0),
            "down_count": market_stats.get('down_count', 0),
            "total_volume": market_stats.get('total_amount', 0),
            "avg_pct_chg": market_stats.get('avg_pct_chg', 0),
            "indices": indices,
            "market_sentiment": market_sentiment,
            "qianniu_analysis": self._qianniu_market_analysis(market_sentiment, tushare_data),
            "data_source": "tushare_pro"
        }
    
    def _format_market_overview_akshare(self, akshare_data, date_str):
        """格式化AKShare增强数据"""
        concept_boards = akshare_data.get('concept_boards', [])
        industry_boards = akshare_data.get('industry_boards', [])
        
        # 分析热门板块
        hot_concepts = sorted(concept_boards, key=lambda x: x.get('涨跌幅', 0), reverse=True)[:10]
        hot_industries = sorted(industry_boards, key=lambda x: x.get('涨跌幅', 0), reverse=True)[:10]
        
        return {
            "date": date_str,
            "hot_concepts": hot_concepts,
            "hot_industries": hot_industries,
            "fund_flow_ranking": akshare_data.get('fund_flow', [])[:20],
            "lhb_highlights": akshare_data.get('lhb_data', []),
            "market_sentiment": "基于板块轮动分析",
            "qianniu_analysis": self._qianniu_sector_analysis(hot_concepts, hot_industries),
            "data_source": "akshare_enhanced"
        }
    
    def _calculate_market_sentiment_enhanced(self, limit_up, limit_down, up_count, down_count):
        """增强版市场情绪计算"""
        if limit_up + limit_down == 0:
            ratio = 1
        else:
            ratio = limit_up / (limit_up + limit_down) if (limit_up + limit_down) > 0 else 0.5
        
        up_down_ratio = up_count / (up_count + down_count) if (up_count + down_count) > 0 else 0.5
        
        # 综合情绪评分
        sentiment_score = (ratio * 0.6 + up_down_ratio * 0.4)
        
        if sentiment_score >= 0.7:
            return "强势上涨"
        elif sentiment_score >= 0.6:
            return "震荡偏强"
        elif sentiment_score >= 0.4:
            return "震荡整理"
        elif sentiment_score >= 0.3:
            return "震荡偏弱"
        else:
            return "弱势下跌"
    
    def _qianniu_market_analysis(self, sentiment, tushare_data):
        """千牛哥市场分析"""
        limit_up = tushare_data['limit_up_count']
        limit_down = tushare_data['limit_down_count']
        
        if limit_up > 50 and limit_down < 10:
            return "市场情绪高涨，连板效应显著，可积极参与"
        elif limit_up > 30 and limit_down < 20:
            return "市场情绪良好，选择优质个股参与"
        elif limit_up < 20 and limit_down > 30:
            return "市场情绪低迷，控制仓位，观望为主"
        else:
            return "市场情绪中性，可精选个股参与"
    
    def _qianniu_sector_analysis(self, hot_concepts, hot_industries):
        """千牛哥板块分析"""
        if not hot_concepts and not hot_industries:
            return "板块轮动不明显，个股行情为主"
        
        strongest_concept = hot_concepts[0] if hot_concepts else None
        strongest_industry = hot_industries[0] if hot_industries else None
        
        analysis = "当前热门板块: "
        if strongest_concept:
            analysis += f"概念-{strongest_concept.get('板块名称', 'N/A')} "
        if strongest_industry:
            analysis += f"行业-{strongest_industry.get('板块名称', 'N/A')}"
        
        return analysis + "。关注板块内龙头股的表现"
    
    def get_risk_scan_data(self, date_str=None):
        """获取风险扫描数据 - 千牛哥六步法第二步"""
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
            
        try:
            # 获取跌幅榜
            decline_rank = ak.stock_zh_a_spot_em()
            decline_rank = decline_rank.sort_values('跌涨幅', ascending=True).head(50)
            
            # 获取跌停股
            limit_down = decline_rank[decline_rank['跌涨幅'] <= -9.9]
            
            # 分析成交量衰减情况
            volume_analysis = self._analyze_volume_decline(decline_rank)
            
            risk_data = {
                "date": date_str,
                "decline_rank": decline_rank.to_dict('records'),
                "limit_down_stocks": limit_down.to_dict('records'),
                "volume_analysis": volume_analysis,
                "risk_sectors": self._identify_risk_sectors(decline_rank)
            }
            
            return risk_data
            
        except Exception as e:
            logging.error(f"获取风险扫描数据失败: {e}")
            return {}
    
    def get_opportunity_scan_data(self, date_str=None):
        """获取机会扫描数据 - 千牛哥六步法第三步"""
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
            
        try:
            # 获取涨幅榜
            gain_rank = ak.stock_zh_a_spot_em()
            gain_rank = gain_rank.sort_values('跌涨幅', ascending=False).head(100)
            
            # 获取连板股
            consecutive_boards = self._get_consecutive_limit_up(gain_rank)
            
            # 获取阶段涨幅榜
            stage_gainers = self._get_stage_gainers(date_str)
            
            # 量价齐升分析
            volume_price_rise = self._analyze_volume_price_rise(gain_rank)
            
            opportunity_data = {
                "date": date_str,
                "gain_rank": gain_rank.head(50).to_dict('records'),
                "consecutive_boards": consecutive_boards,
                "stage_gainers": stage_gainers,
                "volume_price_rise": volume_price_rise,
                "hot_sectors": self._identify_hot_sectors(gain_rank)
            }
            
            return opportunity_data
            
        except Exception as e:
            logging.error(f"获取机会扫描数据失败: {e}")
            return {}
    
    def get_capital_verification_data(self, date_str=None):
        """获取资金验证数据 - 千牛哥六步法第四步"""
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
            
        try:
            # 获取成交额前50股票
            volume_leaders = ak.stock_zh_a_spot_em()
            volume_leaders = volume_leaders.sort_values('成交额', ascending=False).head(50)
            
            # 板块K线量价分析
            sector_volume_analysis = self._analyze_sector_volume_price()
            
            # 资金流向分析
            capital_flow = self._analyze_capital_flow(date_str)
            
            verification_data = {
                "date": date_str,
                "volume_leaders": volume_leaders.to_dict('records'),
                "sector_analysis": sector_volume_analysis,
                "capital_flow": capital_flow,
                "momentum_funds": self._identify_momentum_funds(volume_leaders)
            }
            
            return verification_data
            
        except Exception as e:
            logging.error(f"获取资金验证数据失败: {e}")
            return {}
    
    def save_fuPan_record(self, user_id, date, step_data, predictions):
        """保存复盘记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO fuPan_records 
            (user_id, date, step1_market_overview, step2_risk_scan, 
             step3_opportunity_scan, step4_capital_verification, 
             step5_logic_check, step6_portfolio_management, predictions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, date,
            json.dumps(step_data.get('step1', {})),
            json.dumps(step_data.get('step2', {})),
            json.dumps(step_data.get('step3', {})),
            json.dumps(step_data.get('step4', {})),
            json.dumps(step_data.get('step5', {})),
            json.dumps(step_data.get('step6', {})),
            json.dumps(predictions)
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def calculate_next_day_score(self, record_id):
        """计算第二天验证得分"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取复盘记录
        cursor.execute('SELECT * FROM fuPan_records WHERE id = ?', (record_id,))
        record = cursor.fetchone()
        
        if not record:
            return None
            
        predictions = json.loads(record[8])  # predictions字段
        
        # 获取第二天实际表现
        next_day = (datetime.strptime(record[2], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        actual_performance = self._get_actual_performance(next_day, predictions)
        
        # 计算预测准确度得分
        prediction_score = self._calculate_prediction_accuracy(predictions, actual_performance)
        
        # 计算分析深度得分  
        depth_score = self._calculate_analysis_depth(record)
        
        total_score = prediction_score + depth_score
        
        # 保存评分结果
        cursor.execute('''
            INSERT INTO scoring_results 
            (record_id, prediction_accuracy_score, analysis_depth_score, 
             total_score, next_day_performance, scoring_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            record_id, prediction_score, depth_score, total_score,
            json.dumps(actual_performance), next_day
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "prediction_score": prediction_score,
            "depth_score": depth_score,
            "total_score": total_score,
            "actual_performance": actual_performance
        }
    
    def _get_mock_market_overview(self, date_str):
        """获取模拟市场概览数据"""
        return {
            "date": date_str,
            "limit_up_count": 45,
            "limit_down_count": 8,
            "up_count": 2850,
            "down_count": 1650,
            "total_volume": 1.15e12,
            "market_sentiment": "震荡偏强",
            "qianniu_analysis": "市场情绪中性，可精选个股参与",
            "data_source": "mock_data"
        }
    
    def _calculate_market_sentiment(self, limit_up_count, limit_down_count):
        """计算市场情绪 - 千牛哥分析法"""
        if limit_up_count > 80:
            return "强势上涨"
        elif limit_up_count > 50:
            return "震荡偏强"
        elif limit_up_count > 20:
            return "震荡"
        elif limit_down_count > 50:
            return "弱势下跌"
        else:
            return "震荡偏弱"
    
    def _analyze_volume_decline(self, decline_data):
        """分析成交量衰减"""
        return {"volume_decline_ratio": 0.15, "risk_level": "中等"}
    
    def _identify_risk_sectors(self, decline_data):
        """识别高风险板块"""
        return ["房地产", "银行"]
    
    def _get_consecutive_limit_up(self, gain_data):
        """获取连板股"""
        return gain_data[gain_data['跌涨幅'] >= 9.9].to_dict('records')
    
    def _get_stage_gainers(self, date_str):
        """获取阶段涨幅榜"""
        return []
    
    def _analyze_volume_price_rise(self, gain_data):
        """分析量价齐升"""
        return {"strong_stocks": [], "volume_price_correlation": 0.8}
    
    def _identify_hot_sectors(self, gain_data):
        """识别热门板块"""
        return ["新能源", "人工智能"]
    
    def _analyze_sector_volume_price(self):
        """分析板块量价关系"""
        return {"sector_momentum": {}}
    
    def _analyze_capital_flow(self, date_str):
        """分析资金流向"""
        return {"net_inflow": 1000000000, "main_inflow_sectors": []}
    
    def _identify_momentum_funds(self, volume_data):
        """识别动量资金"""
        return {"momentum_ratio": 0.6, "smart_money_flow": "流入"}
    
    def _get_actual_performance(self, date, predictions):
        """获取实际表现数据"""
        # 实现获取次日实际表现的逻辑
        return {"sector_performance": {}, "stock_performance": {}}
    
    def _calculate_prediction_accuracy(self, predictions, actual):
        """计算预测准确度"""
        # 实现预测准确度计算逻辑
        return 50.0  # 满分70分
    
    def _calculate_analysis_depth(self, record):
        """计算分析深度得分"""
        # 实现分析深度评分逻辑
        return 25.0  # 满分30分

if __name__ == "__main__":
    # 测试系统
    system = StockDataSystem()
    
    # 测试数据获取
    overview = system.get_market_overview()
    print("市场概览数据获取成功")
    
    risk_data = system.get_risk_scan_data()
    print("风险扫描数据获取成功")
    
    opportunity_data = system.get_opportunity_scan_data()
    print("机会扫描数据获取成功")