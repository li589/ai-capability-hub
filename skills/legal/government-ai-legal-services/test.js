// 政府AI法律服务技能包测试
// 测试文件
// 开发者：阿拉丁

const GovernmentLegalServicesPackage = require('./index.js');

async function runTests() {
    console.log('='.repeat(80));
    console.log('政府AI法律服务技能包 v1.0 - 测试');
    console.log('='.repeat(80));
    console.log('');
    
    // 初始化技能包
    const servicesPackage = new GovernmentLegalServicesPackage();
    
    // 测试1：获取技能包信息
    console.log('📦 测试1：获取技能包信息');
    console.log('='.repeat(80));
    const packageInfo = servicesPackage.getPackageInfo();
    console.log(JSON.stringify(packageInfo, null, 2));
    console.log('');
    
    // 测试2：快速解读政策
    console.log('📋 测试2：快速解读政策');
    console.log('='.repeat(80));
    const policyContent = `关于推进乡村振兴的政策
为全面推进乡村振兴，促进农业农村现代化，现制定如下政策：

一、政策目标
目标：到2026年底，实现乡村振兴全覆盖，提升农民收入20%。
目的：让农民过上更加美好的生活。
旨在：建设美丽乡村，实现农业农村现代化。

二、主要措施
措施一：加强基础设施建设
措施二：发展特色产业
措施三：培育新型农业经营主体
措施四：推进乡村治理现代化

三、保障措施
保障：设立乡村振兴专项资金
支持：提供政策优惠和税收减免
扶持：加强人才培养和技术服务
补贴：对重点项目给予财政补贴
奖励：对先进地区和个人给予表彰奖励

四、责任主体
由农业农村部负责，各级人民政府组织实施，乡镇人民政府落实具体措施。`;

    const summary = await servicesPackage.generatePolicySummary(policyContent, true);
    console.log('政策摘要：');
    console.log(summary);
    console.log('');
    
    // 测试3：评估政策影响
    console.log('📊 测试3：评估政策影响');
    console.log('='.repeat(80));
    const impact = await servicesPackage.assessPolicyImpact(policyContent, 'county');
    console.log('政策影响评估：');
    console.log(JSON.stringify(impact, null, 2));
    console.log('');
    
    // 测试4：生成实施指导
    console.log('📝 测试4：生成实施指导');
    console.log('='.repeat(80));
    const guidance = await servicesPackage.generateImplementationGuidance(policyContent, 'county');
    console.log('实施指导：');
    console.log(JSON.stringify(guidance, null, 2));
    console.log('');
    
    // 测试5：检查政策适用性
    console.log('✅ 测试5：检查政策适用性');
    console.log('='.repeat(80));
    const applicability = await servicesPackage.checkPolicyApplicability(policyContent, 'county');
    console.log('政策适用性：');
    console.log(JSON.stringify(applicability, null, 2));
    console.log('');
    
    // 测试6：检查政策合规性
    console.log('⚖️ 测试6：检查政策合规性');
    console.log('='.repeat(80));
    const compliance = await servicesPackage.checkPolicyCompliance(policyContent);
    console.log('政策合规性：');
    console.log(JSON.stringify(compliance, null, 2));
    console.log('');
    
    // 测试7：完整解读政策
    console.log('🎯 测试7：完整解读政策');
    console.log('='.repeat(80));
    const policyData = {
        name: '关于推进乡村振兴的政策',
        issuingAuthority: '国务院',
        publishDate: '2026-03-28',
        effectiveDate: '2026-04-01',
        expiryDate: null,
        content: policyContent
    };
    
    const analysis = await servicesPackage.interpretPolicy(policyData, {
        level: 'county',
        simplify: false,
        includeImpact: true,
        includeGuidance: true
    });
    
    console.log('完整分析结果（前100行）：');
    console.log(JSON.stringify(analysis, null, 2).split('\n').slice(0, 100).join('\n'));
    console.log('');
    
    // 测试8：生成Markdown报告
    console.log('📄 测试8：生成Markdown报告');
    console.log('='.repeat(80));
    const report = servicesPackage.generatePolicyReport(analysis, 'markdown');
    console.log('Markdown报告（前50行）：');
    console.log(report.split('\n').slice(0, 50).join('\n'));
    console.log('');
    
    // 测试9：批量解读政策
    console.log('📋 测试9：批量解读政策');
    console.log('='.repeat(80));
    const policies = [
        {
            name: '政策1：关于推进乡村振兴的政策',
            issuingAuthority: '国务院',
            publishDate: '2026-03-28',
            effectiveDate: '2026-04-01',
            expiryDate: null,
            content: policyContent
        },
        {
            name: '政策2：关于加强环境保护的政策',
            issuingAuthority: '环境保护部',
            publishDate: '2026-03-28',
            effectiveDate: '2026-04-01',
            expiryDate: '2027-03-31',
            content: '为加强环境保护，促进绿色发展，现制定如下政策...'
        }
    ];
    
    const batchResults = await servicesPackage.batchInterpretPolicies(policies);
    console.log('批量解读结果：');
    batchResults.forEach(result => {
        console.log(`- ${result.policy}：${result.analysis.summary.substring(0, 50)}...`);
    });
    console.log('');
    
    // 保存测试结果
    const fs = require('fs');
    const testResults = {
        packageInfo: packageInfo,
        summary: summary,
        impact: impact,
        guidance: guidance,
        applicability: applicability,
        compliance: compliance,
        analysis: analysis,
        batchResults: batchResults
    };
    
    fs.writeFileSync(
        '/workspace/projects/agents/legal-ai-team/legal-ceo/workspace/skills/government-services/test-results.json',
        JSON.stringify(testResults, null, 2)
    );
    
    console.log('✅ 所有测试完成！');
    console.log('📁 测试结果已保存到：test-results.json');
    console.log('');
}

// 执行测试
runTests().then(() => {
    console.log('='.repeat(80));
    console.log('🎉 测试成功完成！');
    console.log('='.repeat(80));
}).catch(error => {
    console.error('❌ 测试失败：', error);
});