/**
 * 股票复盘游戏 - 前端逻辑
 * 基于千牛哥复盘方法论的游戏化交互
 */

class StockFuPanGame {
    constructor() {
        this.sessionId = null;
        this.gameState = {
            currentStep: 1,
            completedSteps: [],
            skillPoints: {
                marketPerception: 50,
                riskSense: 50,
                opportunityCapture: 50,
                capitalSense: 50,
                logicThinking: 50,
                portfolioManagement: 50
            },
            totalScore: 0,
            level: 1,
            status: 'active'
        };
        this.websocket = null;
        this.stepAnalysisData = {};
        
        this.init();
    }

    async init() {
        console.log('🎮 初始化股票复盘游戏...');
        
        // 启动新游戏
        await this.startNewGame();
        
        // 绑定事件监听器
        this.bindEventListeners();
        
        // 建立WebSocket连接
        this.connectWebSocket();
        
        // 加载实时数据
        await this.loadMarketData();
        
        // 显示千牛哥欢迎信息
        this.showQianniuWelcome();
        
        console.log('✅ 游戏初始化完成！');
    }

    async startNewGame() {
        try {
            const response = await fetch('/api/start_game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: 'player_' + Date.now() })
            });
            
            const result = await response.json();
            this.sessionId = result.session_id;
            
            console.log('🎯 游戏会话创建成功:', this.sessionId);
            
        } catch (error) {
            console.error('❌ 启动游戏失败:', error);
            this.showErrorMessage('启动游戏失败，请刷新页面重试');
        }
    }

    bindEventListeners() {
        // 步骤卡片点击事件
        document.querySelectorAll('.step-card').forEach(card => {
            card.addEventListener('click', (e) => this.handleStepCardClick(e));
        });

        // 表单提交事件
        document.addEventListener('submit', (e) => this.handleFormSubmit(e));

        // 输入框变化监听
        document.addEventListener('input', (e) => this.handleInputChange(e));

        // 快捷键支持
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));

        // 千牛哥金句切换
        setInterval(() => this.showQianniuQuote(), 30000);
    }

    connectWebSocket() {
        if (!this.sessionId) return;

        const wsUrl = `ws://localhost:8000/ws/${this.sessionId}`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log('🔗 WebSocket连接成功');
        };

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.websocket.onclose = () => {
            console.log('🔗 WebSocket连接关闭');
            // 5秒后重连
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.websocket.onerror = (error) => {
            console.error('❌ WebSocket错误:', error);
        };
    }

    async loadMarketData() {
        try {
            const response = await fetch('/api/market_data');
            const marketData = await response.json();
            
            this.updateMarketDataDisplay(marketData);
            
        } catch (error) {
            console.error('❌ 加载市场数据失败:', error);
            // 使用模拟数据
            this.updateMarketDataDisplay(this.getMockMarketData());
        }
    }

    handleStepCardClick(event) {
        const card = event.currentTarget;
        const stepNumber = parseInt(card.dataset.step);
        
        // 检查是否可以访问该步骤
        if (stepNumber > this.gameState.currentStep && 
            !this.gameState.completedSteps.includes(stepNumber)) {
            this.showMessage('请按顺序完成复盘步骤！', 'warning');
            return;
        }

        // 更新UI状态
        this.switchToStep(stepNumber);
    }

    switchToStep(stepNumber) {
        // 更新步骤卡片状态
        document.querySelectorAll('.step-card').forEach(card => {
            card.classList.remove('active');
            const cardStep = parseInt(card.dataset.step);
            
            if (cardStep === stepNumber) {
                card.classList.add('active');
            }
            
            if (this.gameState.completedSteps.includes(cardStep)) {
                card.classList.add('completed');
            }
        });

        // 切换输入区域
        this.showAnalysisInput(stepNumber);
        
        // 更新右侧数据面板
        this.updateDataPanelForStep(stepNumber);
    }

    showAnalysisInput(stepNumber) {
        // 隐藏所有输入区域
        document.querySelectorAll('.analysis-input').forEach(input => {
            input.classList.remove('active');
        });

        // 显示对应步骤的输入区域
        let inputElement = document.getElementById(`step${stepNumber}-input`);
        
        if (!inputElement) {
            inputElement = this.createAnalysisInput(stepNumber);
        }
        
        inputElement.classList.add('active');
    }

    createAnalysisInput(stepNumber) {
        const stepConfig = this.getStepConfig(stepNumber);
        const fuPanArea = document.querySelector('.fuPan-area');
        
        const inputDiv = document.createElement('div');
        inputDiv.className = 'analysis-input active fade-in-up';
        inputDiv.id = `step${stepNumber}-input`;
        
        inputDiv.innerHTML = `
            <h4 style="color: #FFD700; margin-bottom: 15px;">
                <i class="${stepConfig.icon}"></i> 第${stepNumber}步：${stepConfig.title}
            </h4>
            <div class="qianniu-tip" style="background: rgba(255,215,0,0.1); padding: 10px; border-radius: 5px; margin-bottom: 15px; border-left: 3px solid #FFD700;">
                <strong>千牛哥提醒：</strong> ${stepConfig.tip}
            </div>
            ${this.generateInputFields(stepNumber)}
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn btn-primary" onclick="game.submitStep(${stepNumber})">
                    <i class="fas fa-check"></i> 完成分析
                </button>
                ${stepNumber < 6 ? `
                    <button class="btn btn-secondary" onclick="game.nextStep(${stepNumber + 1})">
                        <i class="fas fa-arrow-right"></i> 下一步
                    </button>
                ` : `
                    <button class="btn btn-secondary" onclick="game.submitPredictions()">
                        <i class="fas fa-magic"></i> 提交预测
                    </button>
                `}
            </div>
        `;
        
        fuPanArea.appendChild(inputDiv);
        return inputDiv;
    }

    getStepConfig(stepNumber) {
        const configs = {
            1: {
                title: '市场鸟瞰',
                icon: 'fas fa-globe',
                tip: '先看水位再看方向，平均股价、涨跌家数、成交额三大指标缺一不可'
            },
            2: {
                title: '风险扫描',
                icon: 'fas fa-exclamation-triangle',
                tip: '跌幅榜里藏玄机，量能衰减是风险，先知风险才能避险'
            },
            3: {
                title: '机会扫描',
                icon: 'fas fa-search-plus',
                tip: '涨幅榜找龙头，连板股看趋势，量价齐升才可靠'
            },
            4: {
                title: '资金验证',
                icon: 'fas fa-check-double',
                tip: '成交额前50看资金，板块量价看动量，动量资金引导方向'
            },
            5: {
                title: '逻辑核对',
                icon: 'fas fa-puzzle-piece',
                tip: '价格涨在逻辑前，政策宏观要跟上，题材延展性决定持续性'
            },
            6: {
                title: '标记分组',
                icon: 'fas fa-list-alt',
                tip: '分组建池盯重点，趋势股、情绪股、机构票，次日盯盘有重点'
            }
        };
        
        return configs[stepNumber] || configs[1];
    }

    generateInputFields(stepNumber) {
        const fieldConfigs = {
            1: [
                { type: 'select', label: '市场整体走势', options: ['强势上涨', '震荡偏强', '震荡', '震荡偏弱', '弱势下跌'] },
                { type: 'text', label: '涨跌家数比例', placeholder: '如：涨停30家，跌停5家' },
                { type: 'text', label: '成交额水位', placeholder: '如：总成交1.2万亿，较昨日增加15%' },
                { type: 'textarea', label: '市场情绪分析', placeholder: '结合平均股价、资金面等分析市场情绪...' }
            ],
            2: [
                { type: 'textarea', label: '跌幅榜分析', placeholder: '分析跌幅榜前50，找出下跌逻辑...' },
                { type: 'textarea', label: '跌停股统计', placeholder: '统计跌停原因，是否有共性...' },
                { type: 'textarea', label: '风险板块识别', placeholder: '识别资金流出的高风险板块...' },
                { type: 'select', label: '整体风险等级', options: ['低风险', '中等风险', '高风险', '极高风险'] }
            ],
            3: [
                { type: 'textarea', label: '涨幅榜分析', placeholder: '分析涨幅榜前50，找出上涨逻辑...' },
                { type: 'textarea', label: '连板股统计', placeholder: '统计连板股，分析持续性...' },
                { type: 'textarea', label: '量价齐升筛选', placeholder: '筛选量价齐升的强势股...' },
                { type: 'textarea', label: '热门板块锁定', placeholder: '锁定主流热门板块及龙头股...' }
            ],
            4: [
                { type: 'textarea', label: '成交额分析', placeholder: '分析成交额前50股票的资金动向...' },
                { type: 'textarea', label: '板块量价关系', placeholder: '分析主要板块的量价配合情况...' },
                { type: 'textarea', label: '资金流向判断', placeholder: '判断主力资金流向和意图...' },
                { type: 'select', label: '资金情绪', options: ['非常积极', '积极', '中性', '谨慎', '恐慌'] }
            ],
            5: [
                { type: 'textarea', label: '政策逻辑', placeholder: '分析相关政策对市场的影响...' },
                { type: 'textarea', label: '行业逻辑', placeholder: '分析行业基本面逻辑...' },
                { type: 'textarea', label: '题材延展性', placeholder: '判断当前题材的延展空间...' },
                { type: 'select', label: '逻辑强度', options: ['非常强', '强', '中等', '弱', '很弱'] }
            ],
            6: [
                { type: 'textarea', label: '趋势股池', placeholder: '建立趋势股自选股池...' },
                { type: 'textarea', label: '情绪股池', placeholder: '建立短期情绪股池...' },
                { type: 'textarea', label: '机构重仓股', placeholder: '关注机构重仓股动向...' },
                { type: 'textarea', label: '明日盯盘重点', placeholder: '明确明日盯盘的重点股票和板块...' }
            ]
        };

        const fields = fieldConfigs[stepNumber] || [];
        return fields.map(field => this.createInputField(field)).join('');
    }

    createInputField(config) {
        const id = `field_${Math.random().toString(36).substr(2, 9)}`;
        
        let inputHtml = '';
        if (config.type === 'select') {
            inputHtml = `
                <select class="input-field" id="${id}" name="${config.label}">
                    <option value="">请选择</option>
                    ${config.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                </select>
            `;
        } else if (config.type === 'textarea') {
            inputHtml = `
                <textarea class="input-field" id="${id}" name="${config.label}" 
                         placeholder="${config.placeholder || ''}" rows="3"></textarea>
            `;
        } else {
            inputHtml = `
                <input type="text" class="input-field" id="${id}" name="${config.label}" 
                       placeholder="${config.placeholder || ''}">
            `;
        }

        return `
            <div class="input-group">
                <label class="input-label" for="${id}">${config.label}：</label>
                ${inputHtml}
            </div>
        `;
    }

    async submitStep(stepNumber) {
        try {
            // 收集当前步骤的分析数据
            const stepData = this.collectStepData(stepNumber);
            
            if (!this.validateStepData(stepNumber, stepData)) {
                this.showMessage('请完善分析内容再提交', 'warning');
                return;
            }

            // 提交到后端
            const response = await fetch(`/api/submit_step/${this.sessionId}/${stepNumber}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(stepData)
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                // 更新游戏状态
                this.gameState.completedSteps.push(stepNumber);
                this.gameState.skillPoints = result.skill_points;
                
                // 更新UI
                this.updateSkillDisplay();
                this.markStepCompleted(stepNumber);
                
                // 显示奖励
                this.showStepReward(stepNumber, result.skill_reward);
                
                console.log(`✅ 第${stepNumber}步提交成功`);
                
            } else {
                throw new Error(result.message || '提交失败');
            }
            
        } catch (error) {
            console.error(`❌ 提交第${stepNumber}步失败:`, error);
            this.showErrorMessage(`提交失败: ${error.message}`);
        }
    }

    collectStepData(stepNumber) {
        const inputContainer = document.getElementById(`step${stepNumber}-input`);
        const data = { step: stepNumber, timestamp: new Date().toISOString() };
        
        // 收集所有输入字段的数据
        const inputs = inputContainer.querySelectorAll('.input-field');
        inputs.forEach(input => {
            const name = input.name || input.id;
            const value = input.value.trim();
            
            if (value) {
                data[name] = value;
            }
        });
        
        return data;
    }

    validateStepData(stepNumber, data) {
        // 基本验证：至少要有一个有效输入
        const dataKeys = Object.keys(data).filter(key => !['step', 'timestamp'].includes(key));
        return dataKeys.length > 0 && dataKeys.some(key => data[key] && data[key].length > 10);
    }

    nextStep(stepNumber) {
        if (stepNumber <= 6) {
            this.switchToStep(stepNumber);
            
            // 添加动画效果
            const card = document.querySelector(`.step-card[data-step="${stepNumber}"]`);
            if (card) {
                card.classList.add('pulse');
                setTimeout(() => card.classList.remove('pulse'), 1000);
            }
        }
    }

    markStepCompleted(stepNumber) {
        const card = document.querySelector(`.step-card[data-step="${stepNumber}"]`);
        if (card) {
            card.classList.remove('active', 'pulse');
            card.classList.add('completed');
            
            // 添加完成动画
            card.style.transform = 'scale(1.1)';
            setTimeout(() => {
                card.style.transform = 'scale(1)';
            }, 300);
        }
    }

    updateSkillDisplay() {
        const skillItems = document.querySelectorAll('.skill-item');
        const skillNames = ['marketPerception', 'riskSense', 'opportunityCapture', 
                          'capitalSense', 'logicThinking', 'portfolioManagement'];
        
        skillItems.forEach((item, index) => {
            const skillValue = this.gameState.skillPoints[skillNames[index]];
            const progressBar = item.querySelector('.skill-progress-bar');
            const valueSpan = item.querySelector('.skill-name span:last-child');
            
            // 平滑动画更新进度条
            progressBar.style.transition = 'width 0.5s ease';
            progressBar.style.width = skillValue + '%';
            valueSpan.textContent = `${skillValue}/100`;
            
            // 技能点增加时的特效
            if (skillValue > parseInt(progressBar.dataset.oldValue || '0')) {
                item.classList.add('skill-glow');
                setTimeout(() => item.classList.remove('skill-glow'), 1000);
            }
            
            progressBar.dataset.oldValue = skillValue;
        });
    }

    showStepReward(stepNumber, skillReward) {
        const rewards = Object.entries(skillReward).map(([skill, points]) => 
            `${this.getSkillDisplayName(skill)}: +${points}`
        ).join(', ');
        
        this.showAchievement(
            `第${stepNumber}步完成！`,
            `获得技能点: ${rewards}`,
            'success'
        );
    }

    getSkillDisplayName(skill) {
        const nameMap = {
            marketPerception: '市场感知',
            riskSense: '风险嗅觉',
            opportunityCapture: '机会捕捉',
            capitalSense: '资金嗅觉',
            logicThinking: '逻辑思维',
            portfolioManagement: '组合管理'
        };
        return nameMap[skill] || skill;
    }

    async submitPredictions() {
        try {
            // 弹出预测界面
            const predictions = await this.showPredictionDialog();
            
            if (!predictions) return;
            
            // 提交预测
            const response = await fetch(`/api/submit_predictions/${this.sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(predictions)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.showAchievement(
                    '预测提交成功！',
                    '明日收盘后将自动计算得分',
                    'success'
                );
                
                // 24小时后自动计算得分
                setTimeout(() => this.calculateFinalScore(), 24 * 60 * 60 * 1000);
                
            } else {
                throw new Error(result.message || '提交预测失败');
            }
            
        } catch (error) {
            console.error('❌ 提交预测失败:', error);
            this.showErrorMessage(`提交预测失败: ${error.message}`);
        }
    }

    showPredictionDialog() {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'prediction-dialog';
            dialog.innerHTML = `
                <div class="dialog-overlay">
                    <div class="dialog-content">
                        <h3><i class="fas fa-crystal-ball"></i> 明日预测</h3>
                        <div class="prediction-form">
                            <div class="input-group">
                                <label>看好的板块（最多3个）：</label>
                                <input type="text" id="predicted-sectors" placeholder="如：新能源汽车,人工智能,医疗器械">
                            </div>
                            <div class="input-group">
                                <label>看好的个股（最多5只）：</label>
                                <input type="text" id="predicted-stocks" placeholder="如：比亚迪,宁德时代,特斯拉">
                            </div>
                            <div class="input-group">
                                <label>市场方向预测：</label>
                                <select id="market-direction">
                                    <option value="强势上涨">强势上涨</option>
                                    <option value="震荡偏强">震荡偏强</option>
                                    <option value="震荡">震荡</option>
                                    <option value="震荡偏弱">震荡偏弱</option>
                                    <option value="弱势下跌">弱势下跌</option>
                                </select>
                            </div>
                            <div class="input-group">
                                <label>资金情绪预测：</label>
                                <select id="fund-sentiment">
                                    <option value="非常积极">非常积极</option>
                                    <option value="积极">积极</option>
                                    <option value="中性">中性</option>
                                    <option value="谨慎">谨慎</option>
                                    <option value="恐慌">恐慌</option>
                                </select>
                            </div>
                        </div>
                        <div class="dialog-buttons">
                            <button class="btn btn-primary" onclick="submitPredictionDialog()">
                                <i class="fas fa-check"></i> 提交预测
                            </button>
                            <button class="btn btn-secondary" onclick="closePredictionDialog()">
                                <i class="fas fa-times"></i> 取消
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(dialog);
            
            // 全局函数处理对话框
            window.submitPredictionDialog = () => {
                const predictions = {
                    sectors: {
                        hot_sectors: document.getElementById('predicted-sectors').value.split(',').map(s => s.trim()).filter(s => s)
                    },
                    stocks: {
                        strong_stocks: document.getElementById('predicted-stocks').value.split(',').map(s => s.trim()).filter(s => s)
                    },
                    market_sentiment: {
                        direction: document.getElementById('market-direction').value,
                        fund_sentiment: document.getElementById('fund-sentiment').value
                    }
                };
                
                document.body.removeChild(dialog);
                resolve(predictions);
            };
            
            window.closePredictionDialog = () => {
                document.body.removeChild(dialog);
                resolve(null);
            };
        });
    }

    async calculateFinalScore() {
        try {
            const response = await fetch(`/api/calculate_score/${this.sessionId}`);
            const scoreResult = await response.json();
            
            this.showFinalScoreDialog(scoreResult);
            
        } catch (error) {
            console.error('❌ 计算最终得分失败:', error);
        }
    }

    showFinalScoreDialog(scoreResult) {
        const dialog = document.createElement('div');
        dialog.className = 'final-score-dialog';
        dialog.innerHTML = `
            <div class="dialog-overlay">
                <div class="dialog-content">
                    <h2><i class="fas fa-trophy"></i> 复盘结果</h2>
                    <div class="score-summary">
                        <div class="total-score">${scoreResult.total_score.toFixed(1)}分</div>
                        <div class="grade">${scoreResult.grade}</div>
                    </div>
                    <div class="score-breakdown">
                        <div class="score-item">
                            <span>预测准确度：</span>
                            <span>${scoreResult.prediction_score.toFixed(1)}/70分</span>
                        </div>
                        <div class="score-item">
                            <span>分析深度：</span>
                            <span>${scoreResult.depth_score.toFixed(1)}/30分</span>
                        </div>
                        ${scoreResult.skill_bonus > 0 ? `
                        <div class="score-item">
                            <span>技能加分：</span>
                            <span>+${scoreResult.skill_bonus}分</span>
                        </div>
                        ` : ''}
                    </div>
                    <div class="feedback">
                        <h4>千牛哥点评：</h4>
                        <ul>
                            ${scoreResult.detailed_feedback.qianniu_tips.map(tip => `<li>${tip}</li>`).join('')}
                        </ul>
                    </div>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-redo"></i> 再来一局
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
    }

    updateMarketDataDisplay(marketData) {
        // 更新实时市场数据显示
        if (marketData.mock_data) {
            this.updateMockDataDisplay(marketData.mock_data);
        } else {
            // 更新真实数据显示
            this.updateRealDataDisplay(marketData);
        }
    }

    updateMockDataDisplay(mockData) {
        // 更新指数显示
        if (mockData.indices) {
            Object.entries(mockData.indices).forEach(([name, data]) => {
                const element = document.querySelector(`[data-index="${name}"]`);
                if (element) {
                    const color = data.change >= 0 ? '#4ECDC4' : '#FF6B6B';
                    const arrow = data.change >= 0 ? '↑' : '↓';
                    element.innerHTML = `<span style="color: ${color};">${data.value} ${arrow}${Math.abs(data.change)}%</span>`;
                }
            });
        }
        
        // 更新热门板块
        const hotSectorsContainer = document.querySelector('.hot-sectors');
        if (hotSectorsContainer && mockData.hot_sectors) {
            hotSectorsContainer.innerHTML = mockData.hot_sectors.map(sector => 
                `<div class="data-item">
                    <span>${sector.name}:</span>
                    <span style="color: #4ECDC4;">+${sector.change}%</span>
                </div>`
            ).join('');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'market_update':
                this.updateMarketDataDisplay(data.data);
                break;
            case 'score_calculated':
                this.showFinalScoreDialog(data.data);
                break;
            case 'achievement':
                this.showAchievement(data.title, data.description, 'success');
                break;
        }
    }

    showQianniuWelcome() {
        const quotes = [
            '欢迎来到股票复盘游戏！',
            '记住：价格永远领先情绪！',
            '先手赚后手的钱，做市场的先知先觉者！'
        ];
        
        let index = 0;
        const showNext = () => {
            if (index < quotes.length) {
                this.showAchievement('千牛哥提醒', quotes[index], 'info');
                index++;
                setTimeout(showNext, 3000);
            }
        };
        
        setTimeout(showNext, 1000);
    }

    showQianniuQuote() {
        const quotes = [
            '量为价先导，价为王',
            '高低切换永远存在',
            '慢就是快，只做看懂的机会',
            '情绪变化永远落后于价格变化',
            '先板块后个股，主流板块趋势最可靠',
            '复盘=自我进化，每错一次写成教训',
            '等待是一种境界，做对的事在对的时间'
        ];
        
        const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
        this.showMessage(`千牛哥金句：${randomQuote}`, 'quote');
    }

    showAchievement(title, description, type = 'success') {
        const popup = document.getElementById('achievementPopup');
        if (popup) {
            popup.querySelector('.achievement-title').textContent = title;
            popup.querySelector('.achievement-desc').textContent = description;
            popup.classList.add('show');
            
            // 3秒后自动关闭
            setTimeout(() => {
                popup.classList.remove('show');
            }, 3000);
        }
    }

    showMessage(message, type = 'info') {
        // 创建消息提示
        const messageDiv = document.createElement('div');
        messageDiv.className = `game-message ${type}`;
        messageDiv.textContent = message;
        
        messageDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            z-index: 2000;
            animation: slideInRight 0.3s ease-out;
        `;
        
        // 根据类型设置颜色
        const colors = {
            success: '#4ECDC4',
            warning: '#FFA500',
            error: '#FF6B6B',
            info: '#3498db',
            quote: '#FFD700'
        };
        
        messageDiv.style.background = colors[type] || colors.info;
        
        document.body.appendChild(messageDiv);
        
        // 3秒后移除
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }

    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    getMockMarketData() {
        return {
            indices: {
                '上证指数': { value: 3245.67, change: -1.2 },
                '深证成指': { value: 12456.32, change: 0.8 },
                '创业板指': { value: 2876.45, change: 1.5 }
            },
            hot_sectors: [
                { name: '新能源汽车', change: 3.2 },
                { name: '人工智能', change: 2.8 },
                { name: '医疗器械', change: 2.1 }
            ],
            risk_sectors: [
                { name: '房地产', change: -2.8 },
                { name: '银行', change: -1.5 }
            ]
        };
    }

    handleKeyPress(event) {
        // 快捷键支持
        if (event.ctrlKey || event.metaKey) {
            switch (event.key) {
                case 'Enter':
                    // Ctrl+Enter 提交当前步骤
                    event.preventDefault();
                    this.submitStep(this.gameState.currentStep);
                    break;
                case 'ArrowRight':
                    // Ctrl+Right 下一步
                    event.preventDefault();
                    if (this.gameState.currentStep < 6) {
                        this.nextStep(this.gameState.currentStep + 1);
                    }
                    break;
                case 'ArrowLeft':
                    // Ctrl+Left 上一步
                    event.preventDefault();
                    if (this.gameState.currentStep > 1) {
                        this.switchToStep(this.gameState.currentStep - 1);
                    }
                    break;
            }
        }
    }
}

// 全局游戏实例
let game;

// 页面加载完成后初始化游戏
document.addEventListener('DOMContentLoaded', () => {
    game = new StockFuPanGame();
});

// 添加 CSS 样式
const gameStyles = `
    .skill-glow {
        box-shadow: 0 0 20px rgba(78, 205, 196, 0.6);
        transition: box-shadow 0.5s ease;
    }
    
    .game-message {
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .prediction-dialog .dialog-overlay,
    .final-score-dialog .dialog-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 3000;
    }
    
    .prediction-dialog .dialog-content,
    .final-score-dialog .dialog-content {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        border-radius: 20px;
        padding: 30px;
        max-width: 500px;
        width: 90%;
        color: white;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    
    .final-score-dialog .total-score {
        font-size: 48px;
        text-align: center;
        color: #FFD700;
        font-weight: bold;
        margin: 20px 0;
    }
    
    .final-score-dialog .grade {
        font-size: 24px;
        text-align: center;
        color: #4ECDC4;
        margin-bottom: 20px;
    }
    
    .score-breakdown .score-item {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
`;

// 注入样式
const styleSheet = document.createElement('style');
styleSheet.textContent = gameStyles;
document.head.appendChild(styleSheet);