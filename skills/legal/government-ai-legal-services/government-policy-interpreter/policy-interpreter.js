// 政府政策智能解读技能 v1.0
// AI政府法律服务全球标准技能
// 开发者：阿拉丁
// 指导：张海洋

class GovernmentPolicyInterpreter {
    constructor() {
        this.version = '1.0.0';
        this.name = '政府政策智能解读技能';
        this.description = 'AI自动解读政府政策，识别政策关键点，生成政策摘要，分析政策影响';
    }
    
    // 政策解读
    async interpretPolicy(policyData, options = {}) {
        const {
            level = 'provincial', // provincial, prefecture, county, township, village
            simplify = false, // 是否简化解读
            includeImpact = true, // 是否包含影响评估
            includeGuidance = true // 是否包含执行指导
        } = options;
        
        // 解析政策内容
        const policyAnalysis = {
            policy: policyData,
            keyPoints: this.extractKeyPoints(policyData.content),
            summary: this.generateSummary(policyData.content, simplify),
            scope: this.determineScope(policyData.content),
            validity: this.determineValidity(policyData.effectiveDate, policyData.expiryDate),
            authority: this.identifyAuthority(policyData.issuingAuthority),
            relatedLaws: this.findRelatedLaws(policyData.content),
            relatedPolicies: this.findRelatedPolicies(policyData.content),
            interpretation: {}
        };
        
        // 政策影响评估
        if (includeImpact) {
            policyAnalysis.impact = this.assessPolicyImpact(policyData.content, level);
        }
        
        // 执行指导
        if (includeGuidance) {
            policyAnalysis.guidance = this.generateImplementationGuidance(policyData.content, level);
        }
        
        // 适用性检查
        policyAnalysis.applicability = this.checkApplicability(policyData.content, level);
        
        // 合规性检查
        policyAnalysis.compliance = this.checkPolicyCompliance(policyData.content);
        
        return policyAnalysis;
    }
    
    // 提取关键点
    extractKeyPoints(content) {
        const keyPoints = [];
        
        // 政策目标
        const goals = this.extractGoals(content);
        if (goals.length > 0) {
            keyPoints.push({
                type: 'goals',
                title: '政策目标',
                points: goals
            });
        }
        
        // 主要措施
        const measures = this.extractMeasures(content);
        if (measures.length > 0) {
            keyPoints.push({
                type: 'measures',
                title: '主要措施',
                points: measures
            });
        }
        
        // 保障措施
        const guarantees = this.extractGuarantees(content);
        if (guarantees.length > 0) {
            keyPoints.push({
                type: 'guarantees',
                title: '保障措施',
                points: guarantees
            });
        }
        
        // 责任主体
        const responsibilities = this.extractResponsibilities(content);
        if (responsibilities.length > 0) {
            keyPoints.push({
                type: 'responsibilities',
                title: '责任主体',
                points: responsibilities
            });
        }
        
        return keyPoints;
    }
    
    // 提取政策目标
    extractGoals(content) {
        const goalPatterns = [
            /目标[：:]\s*([^。\n]+)/g,
            /旨在[：:]\s*([^。\n]+)/g,
            /为了[：:]\s*([^。\n]+)/g,
            /目的[：:]\s*([^。\n]+)/g
        ];
        
        const goals = [];
        goalPatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                goals.push(match[1].trim());
            }
        });
        
        return [...new Set(goals)]; // 去重
    }
    
    // 提取主要措施
    extractMeasures(content) {
        const measurePatterns = [
            /措施[：:]\s*([^。\n]+)/g,
            /对策[：:]\s*([^。\n]+)/g,
            /方法[：:]\s*([^。\n]+)/g,
            /途径[：:]\s*([^。\n]+)/g,
            /一是([^。]+)；二是([^。]+)；三是([^。]+)/g
        ];
        
        const measures = [];
        measurePatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                if (match.index > 0) {
                    const matches = match.slice(1).filter(m => m);
                    measures.push(...matches.map(m => m.trim()));
                }
            }
        });
        
        return [...new Set(measures)]; // 去重
    }
    
    // 提取保障措施
    extractGuarantees(content) {
        const guaranteePatterns = [
            /保障[：:]\s*([^。\n]+)/g,
            /支持[：:]\s*([^。\n]+)/g,
            /扶持[：:]\s*([^。\n]+)/g,
            /补贴[：:]\s*([^。\n]+)/g,
            /奖励[：:]\s*([^。\n]+)/g
        ];
        
        const guarantees = [];
        guaranteePatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                guarantees.push(match[1].trim());
            }
        });
        
        return [...new Set(guarantees)]; // 去重
    }
    
    // 提取责任主体
    extractResponsibilities(content) {
        const responsibilityPatterns = [
            /由([^。]+)负责/g,
            /([^。]+)主管部门/g,
            /([^。]+)牵头/g,
            /([^。]+)组织实施/g,
            /([^。]+)监督管理/g
        ];
        
        const responsibilities = [];
        responsibilityPatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                responsibilities.push(match[1].trim());
            }
        });
        
        return [...new Set(responsibilities)]; // 去重
    }
    
    // 生成政策摘要
    generateSummary(content, simplify = false) {
        const sentences = content.match(/[^。！？]+[。！？]/g) || [];
        
        if (simplify && sentences.length > 5) {
            // 简化版：提取前3句和最后2句
            const firstThree = sentences.slice(0, 3);
            const lastTwo = sentences.slice(-2);
            return firstThree.join('') + '...' + lastTwo.join('');
        } else {
            // 完整版：提取前5句
            return sentences.slice(0, 5).join('');
        }
    }
    
    // 确定政策适用范围
    determineScope(content) {
        const scopePatterns = [
            /适用范围[：:]\s*([^。\n]+)/g,
            /适用于[：:]\s*([^。\n]+)/g,
            /覆盖[：:]\s*([^。\n]+)/g
        ];
        
        const scopes = [];
        scopePatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                scopes.push(match[1].trim());
            }
        });
        
        return scopes.length > 0 ? scopes : ['未明确'];
    }
    
    // 确定政策有效期
    determineValidity(effectiveDate, expiryDate) {
        const now = new Date();
        const effective = new Date(effectiveDate);
        const expiry = expiryDate ? new Date(expiryDate) : null;
        
        let status = '有效';
        if (effective > now) {
            status = '尚未生效';
        } else if (expiry && expiry < now) {
            status = '已失效';
        }
        
        return {
            effectiveDate: effectiveDate,
            expiryDate: expiryDate || '长期有效',
            status: status,
            daysValid: expiry ? Math.floor((expiry - effective) / (1000 * 60 * 60 * 24)) : null
        };
    }
    
    // 识别政策发布机关
    identifyAuthority(issuingAuthority) {
        const authorityLevels = {
            '国务院': '国家级',
            '国务院办公厅': '国家级',
            '财政部': '国家级',
            '教育部': '国家级',
            '省级': '省级',
            '省人民政府': '省级',
            '市人民政府': '市级',
            '县/区人民政府': '县级',
            '乡镇/街道办事处': '乡镇级'
        };
        
        for (const [authority, level] of Object.entries(authorityLevels)) {
            if (issuingAuthority.includes(authority)) {
                return {
                    authority: issuingAuthority,
                    level: level
                };
            }
        }
        
        return {
            authority: issuingAuthority,
            level: '未知'
        };
    }
    
    // 查找相关法律法规
    findRelatedLaws(content) {
        const lawPatterns = [
            /《([^》]+)》/g
        ];
        
        const laws = [];
        lawPatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                laws.push(match[1]);
            }
        });
        
        return [...new Set(laws)]; // 去重
    }
    
    // 查找相关政策
    findRelatedPolicies(content) {
        // 基于关键词查找相关政策
        const keywords = this.extractKeywords(content);
        
        // 这里应该是连接到政策数据库的查询
        // 模拟返回相关政策
        const relatedPolicies = [
            {
                title: `关于${keywords[0] || '相关事项'}的通知`,
                authority: '同级部门',
                date: '近期'
            },
            {
                title: `${keywords[1] || '相关事项'}实施办法`,
                authority: '上级部门',
                date: '近期'
            }
        ];
        
        return relatedPolicies;
    }
    
    // 提取关键词
    extractKeywords(content) {
        // 简单的关键词提取（实际应该使用NLP）
        const keywords = [];
        const commonWords = ['的', '了', '是', '在', '和', '有', '我', '你', '他', '她', '它'];
        
        const words = content.split(/[\s，。！？、；：]/);
        const wordCount = {};
        
        words.forEach(word => {
            if (word.length > 1 && !commonWords.includes(word)) {
                wordCount[word] = (wordCount[word] || 0) + 1;
            }
        });
        
        Object.entries(wordCount)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .forEach(([word]) => keywords.push(word));
        
        return keywords;
    }
    
    // 政策影响评估
    assessPolicyImpact(content, level) {
        return {
            economic: this.assessEconomicImpact(content, level),
            social: this.assessSocialImpact(content, level),
            legal: this.assessLegalImpact(content, level),
            environmental: this.assessEnvironmentalImpact(content, level),
            overall: this.calculateOverallImpact(content, level)
        };
    }
    
    // 评估经济影响
    assessEconomicImpact(content, level) {
        const economicKeywords = ['经济', '资金', '投资', '补贴', '奖励', '税收', '费用', '成本', '收入', '利润'];
        const impact = this.assessImpactByKeywords(content, economicKeywords);
        
        return {
            level: impact > 5 ? '重大影响' : impact > 2 ? '中等影响' : '轻微影响',
            score: impact,
            description: impact > 5 ? '政策将对经济发展产生重大影响' : 
                       impact > 2 ? '政策将对经济发展产生一定影响' : 
                       '政策对经济发展影响较小'
        };
    }
    
    // 评估社会影响
    assessSocialImpact(content, level) {
        const socialKeywords = ['民生', '就业', '教育', '医疗', '养老', '住房', '社会保障', '公共服务', '福利', '待遇'];
        const impact = this.assessImpactByKeywords(content, socialKeywords);
        
        return {
            level: impact > 5 ? '重大影响' : impact > 2 ? '中等影响' : '轻微影响',
            score: impact,
            description: impact > 5 ? '政策将对社会民生产生重大影响' : 
                       impact > 2 ? '政策将对社会民生产生一定影响' : 
                       '政策对社会民生影响较小'
        };
    }
    
    // 评估法律影响
    assessLegalImpact(content, level) {
        const legalKeywords = ['法律', '法规', '规定', '办法', '条例', '合规', '违法', '处罚', '权利', '义务'];
        const impact = this.assessImpactByKeywords(content, legalKeywords);
        
        return {
            level: impact > 5 ? '重大影响' : impact > 2 ? '中等影响' : '轻微影响',
            score: impact,
            description: impact > 5 ? '政策将产生重大法律影响' : 
                       impact > 2 ? '政策将产生一定法律影响' : 
                       '政策法律影响较小'
        };
    }
    
    // 评估环境影响
    assessEnvironmentalImpact(content, level) {
        const environmentalKeywords = ['环保', '环境', '污染', '生态', '绿色', '低碳', '节能', '减排', '资源', '可持续'];
        const impact = this.assessImpactByKeywords(content, environmentalKeywords);
        
        return {
            level: impact > 5 ? '重大影响' : impact > 2 ? '中等影响' : '轻微影响',
            score: impact,
            description: impact > 5 ? '政策将对环境产生重大影响' : 
                       impact > 2 ? '政策将对环境产生一定影响' : 
                       '政策对环境影响较小'
        };
    }
    
    // 计算总体影响
    calculateOverallImpact(content, level) {
        const economic = this.assessEconomicImpact(content, level).score;
        const social = this.assessSocialImpact(content, level).score;
        const legal = this.assessLegalImpact(content, level).score;
        const environmental = this.assessEnvironmentalImpact(content, level).score;
        
        const overallScore = (economic + social + legal + environmental) / 4;
        
        return {
            score: overallScore,
            level: overallScore > 5 ? '重大影响' : overallScore > 2 ? '中等影响' : '轻微影响'
        };
    }
    
    // 基于关键词评估影响
    assessImpactByKeywords(content, keywords) {
        let score = 0;
        keywords.forEach(keyword => {
            const regex = new RegExp(keyword, 'g');
            const matches = content.match(regex);
            if (matches) {
                score += matches.length;
            }
        });
        return score;
    }
    
    // 生成实施指导
    generateImplementationGuidance(content, level) {
        const guidance = {
            steps: [],
            timeline: '',
            requirements: [],
            resources: [],
            risks: [],
            monitoring: []
        };
        
        // 提取实施步骤
        guidance.steps = this.extractImplementationSteps(content);
        
        // 确定实施时间线
        guidance.timeline = this.determineTimeline(content, level);
        
        // 提取实施要求
        guidance.requirements = this.extractRequirements(content);
        
        // 提取所需资源
        guidance.resources = this.extractResources(content);
        
        // 识别实施风险
        guidance.risks = this.identifyRisks(content);
        
        // 建议监控措施
        guidance.monitoring = this.suggestMonitoring(content);
        
        return guidance;
    }
    
    // 提取实施步骤
    extractImplementationSteps(content) {
        const stepPatterns = [
            /步骤[一二三四五六七八九十][：:]\s*([^。\n]+)/g,
            /第[一二三四五六七八九十]步[：:]\s*([^。\n]+)/g,
            /首先([^。]+)；其次([^。]+)；再次([^。]+)；最后([^。]+)/g
        ];
        
        const steps = [];
        stepPatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                if (match.index > 0) {
                    const matches = match.slice(1).filter(m => m);
                    steps.push(...matches.map(m => m.trim()));
                }
            }
        });
        
        if (steps.length === 0) {
            // 如果没有明确步骤，生成通用步骤
            steps.push('政策宣传解读', '制定实施方案', '组织实施', '监督检查', '总结评估');
        }
        
        return steps;
    }
    
    // 确定实施时间线
    determineTimeline(content, level) {
        const timelines = {
            provincial: '6-12个月',
            prefecture: '3-6个月',
            county: '2-4个月',
            township: '1-3个月',
            village: '1-2个月'
        };
        
        return timelines[level] || '3-6个月';
    }
    
    // 提取实施要求
    extractRequirements(content) {
        const requirementPatterns = [
            /要求[：:]\s*([^。\n]+)/g,
            /需要[：:]\s*([^。\n]+)/g,
            /必须[：:]\s*([^。\n]+)/g,
            /应当[：:]\s*([^。\n]+)/g
        ];
        
        const requirements = [];
        requirementPatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                requirements.push(match[1].trim());
            }
        });
        
        return requirements.length > 0 ? requirements : ['符合法律法规', '保障实施条件', '明确责任分工'];
    }
    
    // 提取所需资源
    extractResources(content) {
        const resourcePatterns = [
            /资金[：:]\s*([^。\n]+)/g,
            /人力[：:]\s*([^。\n]+)/g,
            /设备[：:]\s*([^。\n]+)/g,
            /技术[：:]\s*([^。\n]+)/g,
            /经费[：:]\s*([^。\n]+)/g
        ];
        
        const resources = [];
        resourcePatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                resources.push(match[1].trim());
            }
        });
        
        return resources.length > 0 ? resources : ['政策文件', '实施方案', '培训材料', '监督机制'];
    }
    
    // 识别实施风险
    identifyRisks(content) {
        const risks = [
            {
                type: '政策理解偏差风险',
                description: '基层对政策理解可能存在偏差',
                mitigation: '加强政策解读培训'
            },
            {
                type: '资源不足风险',
                description: '基层资源可能不足',
                mitigation: '争取上级支持'
            },
            {
                type: '执行不力风险',
                description: '政策执行可能不到位',
                mitigation: '建立监督机制'
            }
        ];
        
        return risks;
    }
    
    // 建议监控措施
    suggestMonitoring(content) {
        const monitoring = [
            {
                type: '进度监控',
                description: '定期检查实施进度',
                frequency: '每月'
            },
            {
                type: '效果评估',
                description: '评估政策实施效果',
                frequency: '每季度'
            },
            {
                type: '问题反馈',
                description: '收集实施过程中的问题',
                frequency: '随时'
            },
            {
                type: '总结改进',
                description: '总结经验，改进措施',
                frequency: '每年'
            }
        ];
        
        return monitoring;
    }
    
    // 检查适用性
    checkApplicability(content, level) {
        const applicability = {
            applicable: true,
            reasons: [],
            conditions: []
        };
        
        // 检查是否明确限制适用范围
        const scopePatterns = [
            /适用于([^。]+)地区/,
            /限于([^。]+)单位/,
            /([^。]+)除外/
        ];
        
        let limitedScope = null;
        scopePatterns.forEach(pattern => {
            const match = content.match(pattern);
            if (match) {
                limitedScope = match[1];
            }
        });
        
        if (limitedScope) {
            applicability.conditions.push(`政策适用于${limitedScope}`);
        }
        
        // 检查是否需要特定条件
        const conditionPatterns = [
            /满足([^。]+)条件/,
            /具备([^。]+)资格/
        ];
        
        conditionPatterns.forEach(pattern => {
            let match;
            const regex = new RegExp(pattern, 'g');
            while ((match = regex.exec(content)) !== null) {
                if (match.index > 0) {
                    const matches2 = match.slice(1).filter(m => m);
                    applicability.conditions.push(...matches2);
                }
            }
        });
        
        if (applicability.conditions.length > 0) {
            applicability.reasons.push('政策有适用条件限制');
        }
        
        return applicability;
    }
    
    // 检查政策合规性
    checkPolicyCompliance(content) {
        const compliance = {
            compliant: true,
            issues: [],
            warnings: []
        };
        
        // 检查是否与上位法冲突
        const conflictPatterns = [
            /违反([^。]+)法律/,
            /与([^。]+)规定不一致/
        ];
        
        conflictPatterns.forEach(pattern => {
            const match = content.match(pattern);
            if (match) {
                compliance.compliant = false;
                compliance.issues.push(`可能与${match[1]}存在冲突`);
            }
        });
        
        // 检查是否涉及敏感内容
        const sensitiveKeywords = ['涉密', '保密', '秘密', '机密'];
        sensitiveKeywords.forEach(keyword => {
            if (content.includes(keyword)) {
                compliance.warnings.push('政策包含敏感内容，需注意保密');
            }
        });
        
        return compliance;
    }
    
    // 生成政策解读报告
    generateReport(analysis, format = 'markdown') {
        if (format === 'json') {
            return JSON.stringify(analysis, null, 2);
        }
        
        // Markdown格式
        let report = `# 政策解读报告\n\n`;
        report += `**政策名称：** ${analysis.policy.name}\n`;
        report += `**发布机关：** ${analysis.policy.issuingAuthority}\n`;
        report += `**发布日期：** ${analysis.policy.publishDate}\n`;
        report += `**生效日期：** ${analysis.policy.effectiveDate}\n\n`;
        
        report += `## 📋 政策摘要\n\n`;
        report += `${analysis.summary}\n\n`;
        
        report += `## 🎯 政策关键点\n\n`;
        analysis.keyPoints.forEach(point => {
            report += `### ${point.title}\n\n`;
            point.points.forEach(p => {
                report += `- ${p}\n`;
            });
            report += `\n`;
        });
        
        report += `## 📐 适用范围\n\n`;
        analysis.scope.forEach(scope => {
            report += `- ${scope}\n`;
        });
        report += `\n`;
        
        report += `## 📅 政策有效期\n\n`;
        report += `- **生效日期：** ${analysis.validity.effectiveDate}\n`;
        report += `- **失效日期：** ${analysis.validity.expiryDate}\n`;
        report += `- **当前状态：** ${analysis.validity.status}\n\n`;
        
        if (analysis.impact) {
            report += `## 📊 政策影响评估\n\n`;
            report += `| 维度 | 影响程度 | 描述 |\n`;
            report += `|------|---------|------|\n`;
            report += `| 经济影响 | ${analysis.impact.economic.level} | ${analysis.impact.economic.description} |\n`;
            report += `| 社会影响 | ${analysis.impact.social.level} | ${analysis.impact.social.description} |\n`;
            report += `| 法律影响 | ${analysis.impact.legal.level} | ${analysis.impact.legal.description} |\n`;
            report += `| 环境影响 | ${analysis.impact.environmental.level} | ${analysis.impact.environmental.description} |\n`;
            report += `| 总体影响 | ${analysis.impact.overall.level} | - |\n\n`;
        }
        
        if (analysis.guidance) {
            report += `## 📝 实施指导\n\n`;
            report += `### 实施步骤\n\n`;
            analysis.guidance.steps.forEach((step, index) => {
                report += `${index + 1}. ${step}\n`;
            });
            report += `\n`;
            
            report += `### 实施时间线\n\n`;
            report += `${analysis.guidance.timeline}\n\n`;
            
            report += `### 实施要求\n\n`;
            analysis.guidance.requirements.forEach(req => {
                report += `- ${req}\n`;
            });
            report += `\n`;
            
            report += `### 所需资源\n\n`;
            analysis.guidance.resources.forEach(res => {
                report += `- ${res}\n`;
            });
            report += `\n`;
            
            report += `### 实施风险\n\n`;
            analysis.guidance.risks.forEach(risk => {
                report += `- **${risk.type}**：${risk.description}（应对措施：${risk.mitigation}）\n`;
            });
            report += `\n`;
            
            report += `### 监控措施\n\n`;
            analysis.guidance.monitoring.forEach(monitor => {
                report += `- **${monitor.type}**：${monitor.description}（频率：${monitor.frequency}）\n`;
            });
            report += `\n`;
        }
        
        report += `## ⚖️ 相关法律法规\n\n`;
        analysis.relatedLaws.forEach(law => {
            report += `- 《${law}》\n`;
        });
        report += `\n`;
        
        report += `## 📑 相关政策\n\n`;
        analysis.relatedPolicies.forEach(policy => {
            report += `- ${policy.title}（${policy.authority}，${policy.date}）\n`;
        });
        report += `\n`;
        
        report += `## ✅ 适用性检查\n\n`;
        report += `**是否适用：** ${analysis.applicability.applicable ? '是' : '否'}\n\n`;
        if (analysis.applicability.conditions.length > 0) {
            report += `**适用条件：**\n\n`;
            analysis.applicability.conditions.forEach(condition => {
                report += `- ${condition}\n`;
            });
            report += `\n`;
        }
        
        report += `## 📋 合规性检查\n\n`;
        report += `**是否合规：** ${analysis.compliance.compliant ? '是' : '否'}\n\n`;
        if (analysis.compliance.issues.length > 0) {
            report += `**合规问题：**\n\n`;
            analysis.compliance.issues.forEach(issue => {
                report += `- ${issue}\n`;
            });
            report += `\n`;
        }
        
        if (analysis.compliance.warnings.length > 0) {
            report += `**合规警告：**\n\n`;
            analysis.compliance.warnings.forEach(warning => {
                report += `- ${warning}\n`;
            });
            report += `\n`;
        }
        
        return report;
    }
}

module.exports = GovernmentPolicyInterpreter;