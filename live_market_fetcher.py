#!/usr/bin/env python3
"""
实时市场数据获取器 - 获取今日最新真实数据
尝试多种可靠的数据源获取当日实时数据
"""

import requests
import json
import time
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional
import re

class LiveMarketFetcher:
    """实时市场数据获取器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def get_today_real_data(self) -> Dict[str, Any]:
        """获取今日真实市场数据"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = {
            "date": today,
            "data_source": "live_api",
            "limit_up_stocks": [],
            "limit_down_stocks": [],
            "market_overview": {},
            "success": False
        }
        
        self.logger.info(f"🔄 开始获取{today}实时市场数据...")
        
        # 方法1: 尝试东方财富涨停板数据
        try:
            limit_data = self._get_eastmoney_limit_data()
            if limit_data["success"]:
                result.update(limit_data)
                result["success"] = True
                self.logger.info("✅ 东方财富数据获取成功")
                return result
        except Exception as e:
            self.logger.warning(f"东方财富API失败: {e}")
        
        # 方法2: 尝试新浪财经数据
        try:
            sina_data = self._get_sina_market_data()
            if sina_data["success"]:
                result.update(sina_data)
                result["success"] = True
                self.logger.info("✅ 新浪财经数据获取成功")
                return result
        except Exception as e:
            self.logger.warning(f"新浪财经API失败: {e}")
        
        # 方法3: 尝试腾讯财经数据
        try:
            tencent_data = self._get_tencent_market_data()
            if tencent_data["success"]:
                result.update(tencent_data)
                result["success"] = True
                self.logger.info("✅ 腾讯财经数据获取成功")
                return result
        except Exception as e:
            self.logger.warning(f"腾讯财经API失败: {e}")
        
        # 方法4: 网易财经数据
        try:
            netease_data = self._get_netease_market_data()
            if netease_data["success"]:
                result.update(netease_data)
                result["success"] = True
                self.logger.info("✅ 网易财经数据获取成功")
                return result
        except Exception as e:
            self.logger.warning(f"网易财经API失败: {e}")
        
        self.logger.error("❌ 所有实时数据源都失败了")
        return result
    
    def _get_eastmoney_limit_data(self) -> Dict:
        """获取东方财富涨跌停数据"""
        
        # 东方财富涨停板接口
        limit_up_url = "http://push2ex.eastmoney.com/getTopicZTPool"
        limit_down_url = "http://push2ex.eastmoney.com/getTopicDTPool"
        
        params = {
            'ut': 'b2884a393a59ad64002292a3e90d46a5',
            'dpt': 'wz.ztzt',
            'Pageindex': 0,
            'pagesize': 50,
            'sort': 'fbt:desc',
            'rt': int(time.time() * 1000)
        }
        
        result = {"success": False, "limit_up_stocks": [], "limit_down_stocks": []}
        
        # 获取涨停数据
        try:
            response = self.session.get(limit_up_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data and 'pool' in data['data']:
                    stocks = data['data']['pool']
                    for stock in stocks[:20]:  # 取前20只
                        stock_info = {
                            "code": stock.get('c', ''),
                            "name": stock.get('n', ''),
                            "price": float(stock.get('p', 0)),
                            "change_pct": 10.0,  # 涨停固定10%
                            "amount": float(stock.get('amount', 0)) * 1e8,  # 转换为元
                            "sector": self._get_sector_by_code(stock.get('c', '')),
                            "limit_reason": self._analyze_limit_reason(stock.get('c', ''), stock.get('n', ''), "up")
                        }
                        result["limit_up_stocks"].append(stock_info)
                    
                    result["success"] = True
                    self.logger.info(f"获取到{len(result['limit_up_stocks'])}只涨停股")
        except Exception as e:
            self.logger.error(f"涨停数据获取失败: {e}")
        
        # 获取跌停数据
        try:
            dt_params = params.copy()
            dt_params['dpt'] = 'wz.dtdt'
            response = self.session.get(limit_down_url, params=dt_params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data and 'pool' in data['data']:
                    stocks = data['data']['pool']
                    for stock in stocks[:15]:  # 取前15只
                        stock_info = {
                            "code": stock.get('c', ''),
                            "name": stock.get('n', ''),
                            "price": float(stock.get('p', 0)),
                            "change_pct": -10.0,  # 跌停固定-10%
                            "amount": float(stock.get('amount', 0)) * 1e8,
                            "sector": self._get_sector_by_code(stock.get('c', '')),
                            "limit_reason": self._analyze_limit_reason(stock.get('c', ''), stock.get('n', ''), "down")
                        }
                        result["limit_down_stocks"].append(stock_info)
                    
                    self.logger.info(f"获取到{len(result['limit_down_stocks'])}只跌停股")
        except Exception as e:
            self.logger.error(f"跌停数据获取失败: {e}")
        
        return result
    
    def _get_sina_market_data(self) -> Dict:
        """获取新浪财经市场数据"""
        
        # 新浪财经涨停板接口
        url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
        
        params = {
            'page': 1,
            'num': 50,
            'sort': 'changepercent',
            'asc': 0,
            'node': 'hs_a',
            '_s_r_a': 'page'
        }
        
        result = {"success": False, "limit_up_stocks": [], "limit_down_stocks": []}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                # 新浪返回的是JavaScript数组格式，需要解析
                text = response.text
                if text and text.startswith('['):
                    data = json.loads(text)
                    
                    limit_up = [s for s in data if float(s.get('changepercent', 0)) >= 9.5]
                    limit_down = [s for s in data if float(s.get('changepercent', 0)) <= -9.5]
                    
                    # 处理涨停股
                    for stock in limit_up[:20]:
                        stock_info = {
                            "code": stock.get('symbol', '').replace('sh', '').replace('sz', ''),
                            "name": stock.get('name', ''),
                            "price": float(stock.get('trade', 0)),
                            "change_pct": float(stock.get('changepercent', 0)),
                            "amount": float(stock.get('amount', 0)) * 1e4,  # 万元转元
                            "sector": self._get_sector_by_code(stock.get('symbol', '')),
                            "limit_reason": self._analyze_limit_reason(stock.get('symbol', ''), stock.get('name', ''), "up")
                        }
                        result["limit_up_stocks"].append(stock_info)
                    
                    # 处理跌停股
                    for stock in limit_down[:15]:
                        stock_info = {
                            "code": stock.get('symbol', '').replace('sh', '').replace('sz', ''),
                            "name": stock.get('name', ''),
                            "price": float(stock.get('trade', 0)),
                            "change_pct": float(stock.get('changepercent', 0)),
                            "amount": float(stock.get('amount', 0)) * 1e4,
                            "sector": self._get_sector_by_code(stock.get('symbol', '')),
                            "limit_reason": self._analyze_limit_reason(stock.get('symbol', ''), stock.get('name', ''), "down")
                        }
                        result["limit_down_stocks"].append(stock_info)
                    
                    if limit_up or limit_down:
                        result["success"] = True
                        self.logger.info(f"新浪数据: 涨停{len(limit_up)}只, 跌停{len(limit_down)}只")
                        
        except Exception as e:
            self.logger.error(f"新浪财经数据解析失败: {e}")
        
        return result
    
    def _get_tencent_market_data(self) -> Dict:
        """获取腾讯财经数据（简化版）"""
        # 腾讯财经API相对复杂，这里做简化处理
        return {"success": False}
    
    def _get_netease_market_data(self) -> Dict:
        """获取网易财经数据（简化版）"""
        # 网易财经API，这里做简化处理
        return {"success": False}
    
    def _get_sector_by_code(self, code: str) -> str:
        """根据股票代码推断板块"""
        if not code:
            return "其他"
            
        # 清理代码
        clean_code = re.sub(r'[^0-9]', '', code)
        
        # 板块映射规则
        if clean_code.startswith('00'):
            if clean_code in ['000002', '000001', '000069']:
                return "房地产"
            elif clean_code in ['000858', '000876']:
                return "酒类"
            return "主板"
        elif clean_code.startswith('30'):
            return "创业板"
        elif clean_code.startswith('60'):
            if clean_code in ['600036', '600000', '600015']:
                return "银行"
            elif clean_code in ['600519', '600809']:
                return "酒类"
            return "主板"
        elif clean_code.startswith('688'):
            return "科创板"
        else:
            return "其他"
    
    def _analyze_limit_reason(self, code: str, name: str, limit_type: str) -> str:
        """分析涨跌停原因"""
        
        # 基于股票名称和代码的智能推理
        name_lower = name.lower() if name else ""
        
        if limit_type == "up":
            if any(keyword in name_lower for keyword in ['比亚迪', '宁德', '新能源', '电池']):
                return "新能源汽车概念利好"
            elif any(keyword in name_lower for keyword in ['科大讯飞', 'ai', '人工智能', '智能']):
                return "AI概念持续火热"
            elif any(keyword in name_lower for keyword in ['中芯', '芯片', '半导体']):
                return "芯片概念强势"
            else:
                return "资金追捧，题材活跃"
        else:
            if any(keyword in name_lower for keyword in ['万科', '保利', '地产', '房地产']):
                return "地产政策压力"
            elif any(keyword in name_lower for keyword in ['银行', '招商银行', '平安银行']):
                return "金融监管趋严"
            else:
                return "获利回吐，技术调整"

# 测试函数
def test_live_fetcher():
    """测试实时数据获取"""
    fetcher = LiveMarketFetcher()
    
    print("🔄 正在获取今日最新实时数据...")
    data = fetcher.get_today_real_data()
    
    if data["success"]:
        print(f"✅ 数据获取成功！来源: {data['data_source']}")
        print(f"📅 日期: {data['date']}")
        print(f"📈 涨停股票: {len(data['limit_up_stocks'])}只")
        print(f"📉 跌停股票: {len(data['limit_down_stocks'])}只")
        
        if data["limit_up_stocks"]:
            print("\n🔥 今日涨停股票（前5只）:")
            for i, stock in enumerate(data["limit_up_stocks"][:5], 1):
                print(f"{i}. {stock['name']}({stock['code']}) - {stock['sector']}")
                print(f"   原因: {stock['limit_reason']}")
        
        if data["limit_down_stocks"]:
            print("\n💥 今日跌停股票（前3只）:")
            for i, stock in enumerate(data["limit_down_stocks"][:3], 1):
                print(f"{i}. {stock['name']}({stock['code']}) - {stock['sector']}")
                print(f"   原因: {stock['limit_reason']}")
    else:
        print("❌ 实时数据获取失败")

if __name__ == "__main__":
    test_live_fetcher()