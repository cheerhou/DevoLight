/**
 * DevoLight Agent Router System
 * 智能体路由系统 - 负责根据用户输入选择合适的智能体
 */

class AgentRouter {
    constructor() {
        this.agents = {
            antioch: {
                id: 'antioch-biblical-teacher',
                name: '安提阿老师',
                icon: '🕊️',
                specialties: ['神学', '解经', '教义', '真理', '救恩', '圣经整体', '新约', '旧约'],
                keywords: ['神学', '真理', '教义', '救恩', '解释', '含义', '为什么', '神', '基督', '圣灵']
            },
            luke: {
                id: 'biblical-historian-luke',
                name: '路加笔者',
                icon: '📜',
                specialties: ['历史', '文化', '背景', '地理', '考古', '时代'],
                keywords: ['历史', '背景', '文化', '当时', '时代', '地点', '风俗', '习惯', '原始读者']
            },
            martha: {
                id: 'spiritual-life-mentor',
                name: '马大姊妹',
                icon: '🌱',
                specialties: ['应用', '生活', '实践', '职场', '家庭', '人际关系'],
                keywords: ['应用', '生活', '工作', '家庭', '实际', '如何', '怎样', '职场', '关系', '实践']
            },
            barnabas: {
                id: 'barnabas-spiritual-companion',
                name: '巴拿巴友伴',
                icon: '🤲',
                specialties: ['祷告', '反思', '陪伴', '默想', '心灵', '情感'],
                keywords: ['祷告', '反思', '心情', '困难', '陪伴', '感受', '痛苦', '喜乐', '平安', '安慰']
            }
        };

        this.scripturePatterns = [
            /([一二三四五六七八九十1234567890]+\s*[\u4e00-\u9fff]+\s*[\u4e00-\u9fff]*)\s*(\d+):?(\d*)/,  // 中文书名
            /([1234567890]*[A-Za-z]+)\s*(\d+):?(\d*)/,  // 英文书名
            /(\w+福音|诗篇|箴言|传道书|雅歌)\s*(\d+)/,  // 常见书名简写
        ];
    }

    /**
     * 路由用户输入到合适的智能体
     * @param {Object} input - 用户输入
     * @param {string} input.message - 用户消息
     * @param {string} input.mode - 交互模式 ('single', 'intelligent', 'sequential')
     * @param {string} input.selectedAgent - 用户选择的智能体（单一模式）
     * @param {Object} input.userProfile - 用户画像信息
     * @returns {Object} 路由结果
     */
    async route(input) {
        const { message, mode, selectedAgent, userProfile } = input;

        // 解析经文引用
        const scripture = this.parseScripture(message);
        
        switch (mode) {
            case 'single':
                return this.singleAgentMode(selectedAgent, message, scripture, userProfile);
            
            case 'intelligent':
                return this.intelligentMode(message, scripture, userProfile);
            
            case 'sequential':
                return this.sequentialMode(message, scripture, userProfile);
            
            default:
                throw new Error(`未知的模式: ${mode}`);
        }
    }

    /**
     * 单一智能体模式
     */
    singleAgentMode(agentId, message, scripture, userProfile) {
        const agent = this.agents[agentId];
        if (!agent) {
            throw new Error(`未找到智能体: ${agentId}`);
        }

        return {
            mode: 'single',
            agents: [agent.id],
            routing: {
                primary: agent.id,
                confidence: 1.0,
                reasoning: `用户指定使用 ${agent.name}`
            },
            context: this.buildContext(message, scripture, userProfile, agent)
        };
    }

    /**
     * 智能协作模式
     */
    intelligentMode(message, scripture, userProfile) {
        // 计算每个智能体的匹配分数
        const scores = this.calculateAgentScores(message, userProfile);
        
        // 选择最佳智能体（分数最高的1-2个）
        const sortedAgents = Object.entries(scores)
            .sort(([,a], [,b]) => b.score - a.score)
            .slice(0, 2)
            .filter(([,data]) => data.score > 0.3); // 过滤掉分数太低的

        if (sortedAgents.length === 0) {
            // 默认使用安提阿老师
            sortedAgents.push(['antioch', { score: 0.5, reasons: ['默认选择'] }]);
        }

        const primaryAgent = sortedAgents[0][0];
        const selectedAgents = sortedAgents.map(([id]) => this.agents[id].id);

        return {
            mode: 'intelligent',
            agents: selectedAgents,
            routing: {
                primary: this.agents[primaryAgent].id,
                confidence: sortedAgents[0][1].score,
                reasoning: `基于内容分析，选择 ${this.agents[primaryAgent].name}`,
                scores: scores
            },
            context: this.buildContext(message, scripture, userProfile, this.agents[primaryAgent])
        };
    }

    /**
     * 顺序协作模式
     */
    sequentialMode(message, scripture, userProfile) {
        const agentOrder = ['antioch', 'luke', 'martha', 'barnabas'];
        const selectedAgents = agentOrder.map(id => this.agents[id].id);

        return {
            mode: 'sequential',
            agents: selectedAgents,
            routing: {
                primary: this.agents.antioch.id,
                confidence: 1.0,
                reasoning: '完整解经模式，四个智能体依次回应',
                sequence: agentOrder.map(id => ({
                    agent: this.agents[id].id,
                    name: this.agents[id].name,
                    delay: agentOrder.indexOf(id) * 2000 // 每个延迟2秒
                }))
            },
            context: this.buildContext(message, scripture, userProfile, this.agents.antioch)
        };
    }

    /**
     * 计算智能体匹配分数
     */
    calculateAgentScores(message, userProfile) {
        const scores = {};
        
        for (const [id, agent] of Object.entries(this.agents)) {
            let score = 0;
            const reasons = [];

            // 关键词匹配
            const keywordMatches = agent.keywords.filter(keyword => 
                message.toLowerCase().includes(keyword)
            ).length;
            
            if (keywordMatches > 0) {
                score += keywordMatches * 0.3;
                reasons.push(`关键词匹配: ${keywordMatches}个`);
            }

            // 用户画像匹配
            if (userProfile) {
                if (id === 'martha' && (userProfile.profession || userProfile.concerns)) {
                    score += 0.4;
                    reasons.push('适合生活应用指导');
                }
                
                if (id === 'barnabas' && userProfile.spiritualState && 
                    ['感到疲惫', '遇到困难', '需要安慰'].includes(userProfile.spiritualState)) {
                    score += 0.5;
                    reasons.push('适合心灵陪伴');
                }
            }

            // 问题类型分析
            if (message.includes('为什么') || message.includes('什么意思')) {
                if (id === 'antioch') {
                    score += 0.3;
                    reasons.push('神学解释问题');
                }
            }

            if (message.includes('当时') || message.includes('历史')) {
                if (id === 'luke') {
                    score += 0.4;
                    reasons.push('历史背景问题');
                }
            }

            scores[id] = { score, reasons };
        }

        return scores;
    }

    /**
     * 解析经文引用
     */
    parseScripture(message) {
        for (const pattern of this.scripturePatterns) {
            const match = message.match(pattern);
            if (match) {
                return {
                    book: match[1],
                    chapter: match[2],
                    verse: match[3] || null,
                    full: match[0]
                };
            }
        }
        return null;
    }

    /**
     * 构建上下文信息
     */
    buildContext(message, scripture, userProfile, primaryAgent) {
        return {
            originalMessage: message,
            scripture: scripture,
            userProfile: userProfile || {},
            primaryAgent: {
                id: primaryAgent.id,
                name: primaryAgent.name,
                icon: primaryAgent.icon
            },
            timestamp: new Date().toISOString(),
            sessionId: this.generateSessionId()
        };
    }

    /**
     * 生成会话ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 获取智能体信息
     */
    getAgentInfo(agentId) {
        for (const agent of Object.values(this.agents)) {
            if (agent.id === agentId) {
                return agent;
            }
        }
        return null;
    }

    /**
     * 验证路由结果
     */
    validateRouting(routing) {
        if (!routing.agents || routing.agents.length === 0) {
            throw new Error('路由结果必须包含至少一个智能体');
        }

        for (const agentId of routing.agents) {
            if (!this.getAgentInfo(agentId)) {
                throw new Error(`无效的智能体ID: ${agentId}`);
            }
        }

        return true;
    }
}

// 使用示例
async function example() {
    const router = new AgentRouter();
    
    // 示例1: 智能路由
    const result1 = await router.route({
        message: "腓立比书4:13应用到现代生活中，我是30岁的程序员，工作压力很大",
        mode: 'intelligent',
        userProfile: {
            profession: '程序员',
            age: '30岁',
            spiritualState: '感到疲惫'
        }
    });
    
    console.log('智能路由结果:', result1);

    // 示例2: 历史背景询问
    const result2 = await router.route({
        message: "请介绍约翰福音3:16的历史背景",
        mode: 'intelligent'
    });
    
    console.log('历史背景询问:', result2);
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AgentRouter;
} else if (typeof window !== 'undefined') {
    window.AgentRouter = AgentRouter;
}