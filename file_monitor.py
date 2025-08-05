#!/usr/bin/env python3
"""
文件监控系统 - 自动监控新Excel文档
当有新的重启人生计划表放入时自动提取数据
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from excel_data_extractor import ExcelDataExtractor, DocumentMonitor

class ExcelFileHandler(FileSystemEventHandler):
    """Excel文件监控处理器"""
    
    def __init__(self, game_data_system=None):
        super().__init__()
        self.game_data_system = game_data_system
        self.logger = logging.getLogger(__name__)
        
        # 支持的Excel文件扩展名
        self.excel_extensions = {'.xlsx', '.xls', '.xlsm'}
        
        # 延迟处理时间（秒）- 等待文件完全写入
        self.process_delay = 3
        
    def on_created(self, event):
        """当新文件创建时触发"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "创建")
    
    def on_modified(self, event):
        """当文件修改时触发"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "修改")
    
    def _handle_file_event(self, file_path, event_type):
        """处理文件事件"""
        file_path = Path(file_path)
        
        # 检查是否为Excel文件
        if file_path.suffix.lower() in self.excel_extensions:
            self.logger.info(f"🔍 检测到Excel文件{event_type}: {file_path.name}")
            
            # 延迟处理，确保文件完全写入
            time.sleep(self.process_delay)
            
            # 检查是否为复盘相关文件
            if self._is_fuPan_related_file(file_path):
                self._process_fuPan_file(file_path)
    
    def _is_fuPan_related_file(self, file_path):
        """判断是否为复盘相关文件"""
        filename = file_path.name.lower()
        
        # 复盘相关关键词
        fuPan_keywords = [
            '重启人生计划表', '复盘', '股票', '涨停', '龙虎榜', 
            '题材', '连板', '情绪', '市场数据'
        ]
        
        return any(keyword in filename for keyword in fuPan_keywords)
    
    def _process_fuPan_file(self, file_path):
        """处理复盘文件"""
        try:
            self.logger.info(f"📊 开始处理复盘文件: {file_path.name}")
            
            # 创建数据提取器
            extractor = ExcelDataExtractor(str(file_path))
            
            # 提取当日数据
            today = datetime.now().strftime('%Y-%m-%d')
            result = extractor.extract_all_data(today)
            
            if result:
                self.logger.info(f"✅ 复盘数据提取成功: {file_path.name}")
                
                # 通知游戏系统数据更新
                if self.game_data_system:
                    self.game_data_system.notify_data_update(result)
                
                # 生成提取报告
                self._generate_extraction_report(file_path, result)
                
            else:
                self.logger.error(f"❌ 复盘数据提取失败: {file_path.name}")
                
        except Exception as e:
            self.logger.error(f"❌ 处理复盘文件失败 {file_path.name}: {e}")
    
    def _generate_extraction_report(self, file_path, result):
        """生成数据提取报告"""
        report_content = f"""
# 📊 复盘数据提取报告

## 文件信息
- **文件名**: {file_path.name}
- **提取时间**: {result['extraction_time']}
- **数据日期**: {result['date']}

## 千牛哥六步复盘数据提取结果

### 1️⃣ 市场鸟瞰
- **数据状态**: {'✅ 成功' if result['data'].get('market_overview') else '❌ 失败'}
- **数据源**: {list(result['data'].get('market_overview', {}).keys())}

### 2️⃣ 风险扫描  
- **数据状态**: {'✅ 成功' if result['data'].get('risk_scan') else '❌ 失败'}
- **数据源**: {list(result['data'].get('risk_scan', {}).keys())}

### 3️⃣ 机会扫描
- **数据状态**: {'✅ 成功' if result['data'].get('opportunity_scan') else '❌ 失败'}
- **数据源**: {list(result['data'].get('opportunity_scan', {}).keys())}

### 4️⃣ 资金验证
- **数据状态**: {'✅ 成功' if result['data'].get('capital_verification') else '❌ 失败'}
- **数据源**: {list(result['data'].get('capital_verification', {}).keys())}

### 5️⃣ 逻辑核对
- **数据状态**: {'✅ 成功' if result['data'].get('logic_check') else '❌ 失败'}
- **数据源**: {list(result['data'].get('logic_check', {}).keys())}

### 6️⃣ 标记分组
- **数据状态**: {'✅ 成功' if result['data'].get('portfolio_management') else '❌ 失败'}
- **数据源**: {list(result['data'].get('portfolio_management', {}).keys())}

## 🎮 游戏数据更新
- **总提取步骤**: {len([k for k, v in result['data'].items() if v])}
- **状态**: 数据已同步到复盘游戏系统

---
*自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
        """
        
        # 保存报告
        report_path = Path("extraction_reports") / f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"📋 提取报告已生成: {report_path}")

class FileMonitorService:
    """文件监控服务"""
    
    def __init__(self, watch_directories=None, game_data_system=None):
        self.watch_directories = watch_directories or [
            "/Users/jx/Desktop/stock-agent3.0",
            "/Users/jx/Downloads",
            "/Users/jx/Desktop"
        ]
        
        self.game_data_system = game_data_system
        self.observer = None
        self.event_handler = ExcelFileHandler(game_data_system)
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('file_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """启动文件监控"""
        self.logger.info("🚀 启动Excel文件监控服务...")
        
        self.observer = Observer()
        
        # 为每个监控目录添加监听器
        for directory in self.watch_directories:
            if os.path.exists(directory):
                self.observer.schedule(
                    self.event_handler, 
                    directory, 
                    recursive=True
                )
                self.logger.info(f"📁 监控目录: {directory}")
            else:
                self.logger.warning(f"⚠️ 监控目录不存在: {directory}")
        
        self.observer.start()
        self.logger.info("✅ 文件监控服务启动成功！")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("⏹️ 文件监控服务已停止")
    
    def scan_existing_files(self):
        """扫描现有的Excel文件"""
        self.logger.info("🔍 扫描现有Excel文件...")
        
        for directory in self.watch_directories:
            if os.path.exists(directory):
                for file_path in Path(directory).rglob("*.xlsx"):
                    if self.event_handler._is_fuPan_related_file(file_path):
                        self.logger.info(f"📁 发现现有复盘文件: {file_path.name}")
                        self.event_handler._process_fuPan_file(file_path)

# 游戏数据系统扩展类
class GameDataSystemExtended:
    """游戏数据系统扩展 - 支持文件监控"""
    
    def __init__(self, original_data_system):
        self.original_system = original_data_system
        self.logger = logging.getLogger(__name__)
        
        # 数据更新回调列表
        self.update_callbacks = []
    
    def notify_data_update(self, extraction_result):
        """通知数据更新"""
        self.logger.info(f"🔄 接收到数据更新通知: {extraction_result['date']}")
        
        # 执行所有注册的回调
        for callback in self.update_callbacks:
            try:
                callback(extraction_result)
            except Exception as e:
                self.logger.error(f"❌ 数据更新回调执行失败: {e}")
    
    def register_update_callback(self, callback_func):
        """注册数据更新回调"""
        self.update_callbacks.append(callback_func)
        self.logger.info(f"✅ 注册数据更新回调: {callback_func.__name__}")
    
    def get_latest_extracted_data(self):
        """获取最新提取的数据"""
        # 可以从原始系统获取最新数据
        return self.original_system.get_excel_data()

if __name__ == "__main__":
    print("📁 Excel文件监控服务")
    print("自动监控新复盘文档并提取数据")
    print("=" * 50)
    
    # 创建监控服务
    monitor_service = FileMonitorService()
    
    # 先扫描现有文件
    monitor_service.scan_existing_files()
    
    # 启动实时监控
    print("\n🚀 启动实时监控...")
    print("📂 监控以下目录的Excel文件变化:")
    for directory in monitor_service.watch_directories:
        print(f"  - {directory}")
    
    print("\n按 Ctrl+C 停止监控")
    
    try:
        monitor_service.start_monitoring()
    except KeyboardInterrupt:
        print("\n👋 监控服务已停止")