flowchart TB
    subgraph Systems["Application Systems"]
        direction LR
        sys-crm["CRM"]
        sys-pos["POS"]
        sys-erp["ERP"]
        sys-ai["AI平台"]
        sys-partner["伙伴门户"]
    end
    subgraph 产品智能化["产品智能化"]
        direction TB
        subgraph row_产品智能化_0[""]
            direction LR
            cap-ai-recommend["AI智能推荐"]
            cap-smart-search["智能搜索"]
            cap-auto-tag["自动标签"]
            cap-content-gen["内容生成"]
        end
        cap-knowledge["知识库"]
    end
    subgraph 客户服务智能化["客户服务智能化"]
        direction TB
        subgraph row_客户服务智能化_0[""]
            direction LR
            cap-smart-service["智能客服"]
            cap-sentiment["情感分析"]
            cap-auto-reply["自动回复"]
            cap-feedback["反馈管理"]
        end
    end
    subgraph 运营管理智能化["运营管理智能化"]
        direction TB
        subgraph row_运营管理智能化_0[""]
            direction LR
            cap-data-analysis["数据分析"]
            cap-inventory["库存管理"]
            cap-supply-chain["供应链优化"]
            cap-financial["财务分析"]
        end
    end
    subgraph 生态伙伴赋能["生态伙伴赋能"]
        direction TB
        subgraph row_生态伙伴赋能_0[""]
            direction LR
            cap-partner-mgmt["伙伴管理"]
            cap-channel["渠道管理"]
            cap-co-marketing["联合营销"]
            cap-data-share["数据共享"]
        end
    end
    subgraph Actors["参与者"]
        direction LR
        actor-store-guide["门店导购"]
        actor-service["客服"]
        actor-manager["店长"]
        actor-partner["合作伙伴"]
        actor-admin["系统管理员"]
    end
    sys-crm --> cap-smart-service
    sys-crm --> cap-auto-reply
    sys-crm --> cap-feedback
    sys-pos --> cap-inventory
    sys-pos --> cap-data-analysis
    sys-erp --> cap-supply-chain
    sys-erp --> cap-financial
    sys-erp --> cap-partner-mgmt
    sys-ai --> cap-ai-recommend
    sys-ai --> cap-smart-search
    sys-ai --> cap-auto-tag
    sys-ai --> cap-content-gen
    sys-ai --> cap-knowledge
    sys-partner --> cap-channel
    sys-partner --> cap-co-marketing
    sys-partner --> cap-data-share
    actor-store-guide -- "" --> cap-pos
    actor-service -- "" --> cap-smart-service
    actor-service -- "" --> cap-auto-reply
    actor-manager -- "" --> cap-data-analysis
    actor-manager -- "" --> cap-inventory
    actor-partner -- "" --> cap-partner-mgmt
    actor-partner -- "" --> cap-channel
