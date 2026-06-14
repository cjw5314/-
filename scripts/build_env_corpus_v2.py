"""
构建环保语料库 - 使用扩展关键词列表
从年报中提取环保相关语句，记录页码和段落信息
参考徐巍等[39]的方法
"""
import os
import re
import csv

# 扩展后的环保关键词列表
ENV_KEYWORDS = [
    # 环境相关
    "环境", "环保", "绿色", "生态", "低碳", "减碳", "碳中和", "碳达峰", "碳排放",
    "温室气体", "气候变化", "全球变暖", "环保责任", "环境责任", "生态保护",
    # ESG相关
    "ESG", "可持续发展", "社会责任", "绿色发展", "循环经济", "绿色金融",
    "低碳经济", "生态经济", "绿色转型", "低碳转型", "绿色供应链",
    # 污染相关
    "污染", "排放", "废水", "废气", "废渣", "废弃物", "固废", "危废",
    "污染物", "大气污染", "水污染", "土壤污染", "噪声污染", "光污染",
    "重金属污染", "PM2.5", "PM10", "VOCs", "氮氧化物", "二氧化硫",
    "COD", "BOD", "氨氮", "总磷", "总氮", "悬浮物", "油类",
    # 污染治理
    "治理", "处理", "减排", "节能", "降耗", "清洁生产", "循环利用",
    "回收利用", "资源化", "无害化", "减量化", "再利用", "再循环",
    "污水处理", "废气处理", "固废处置", "危废处理", "土壤修复",
    "脱硫", "脱硝", "除尘", "除油", "除臭", "降噪", "净化",
    # 环保设施
    "环保设施", "污水处理厂", "垃圾填埋场", "焚烧发电厂", "除尘设备",
    "脱硫装置", "脱硝设备", "在线监测", "VOCs治理设施",
    # 政策法规
    "环保法规", "环境标准", "排放标准", "环保政策", "环境法规",
    "排污许可证", "环评", "环境影响评价", "环保验收", "三同时",
    "环保督察", "环保检查", "环境执法", "环境监管", "绿色税制",
    "碳税", "碳交易", "排污权交易", "绿色信贷", "绿色债券",
    # 处罚相关
    "环境处罚", "环保处罚", "行政处罚", "环保罚单", "环境违法",
    "环境污染罪", "环保问责", "生态环境损害赔偿", "公益诉讼",
    # 能源相关
    "清洁能源", "可再生能源", "新能源", "绿色能源", "太阳能",
    "风能", "水能", "地热能", "生物质能", "核能", "氢能",
    "化石能源", "煤炭", "石油", "天然气", "节能减排",
    # 材料相关
    "绿色材料", "环保材料", "可降解材料", "生物降解", "绿色包装",
    "无公害", "有机食品", "绿色食品", "生态农业",
    # 生态保护
    "生态保护", "生态修复", "植树造林", "退耕还林", "退耕还草",
    "水土保持", "荒漠化防治", "生物多样性", "濒危物种",
    "自然保护区", "生态功能区", "生态红线", "生态补偿",
    # 绿色运营
    "绿色办公", "绿色采购", "绿色物流", "绿色建筑", "绿色交通",
    "低碳出行", "绿色出行", "绿色消费", "生态旅游",
    # 环保管理
    "环境管理体系", "ISO14001", "ISO14064", "碳核查", "能源审计",
    "清洁生产审核", "环境应急预案", "环保培训", "环保宣传",
    "碳足迹", "水足迹", "生态足迹", "全生命周期",
    # 环保科技
    "环保科技", "绿色技术", "环保工艺", "节能减排技术", "低碳技术",
    "碳捕获", "CCUS", "储能技术", "节能环保", "绿色制造",
    # 社会责任相关
    "企业社会责任", "CSR报告", "ESG报告", "环境信息披露",
    "公益环保", "环保捐赠", "绿色公益", "生态保护公益",
    # 特殊场景
    "环保事故", "环境污染事件", "环境应急", "环保整改", "环保搬迁",
    "绿色矿山", "绿色工厂", "绿色园区", "绿色港口", "绿色机场",
    # 宏观政策
    "生态文明", "美丽中国", "绿色中国", "两山理论", "生态文明建设",
    "污染防治攻坚战", "蓝天保卫战", "碧水保卫战", "净土保卫战",
    "长江十年禁渔", "黄河流域生态保护", "双碳目标", "双碳战略",
    # 参与主体
    "环保组织", "NGO", "环保协会", "生态环境局", "自然资源部",
    "国家环保总局", "环保部门", "生态环境部", "生态环保局",
    # 其他补充
    "生态安全", "环境安全", "绿色认证", "环保认证", "生态标签",
    "绿色标志", "绿色产品", "环境友好型", "资源节约型",
    "两型社会", "美丽家园", "绿色生活", "低碳生活",
    "环保出行", "环保节能", "环境治理", "生态治理", "绿色发展理念"
]

def extract_env_sentences(file_path):
    """从TXT文件中提取环保相关语句"""
    env_sentences = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 尝试按页码分割
    pages = re.split(r'[\f\n]*第\s*[零一二三四五六七八九十\d]+\s*页[\f\n]*', content)
    
    for page_num, page_content in enumerate(pages, 1):
        if not page_content.strip():
            continue
        
        # 按段落分割
        paragraphs = re.split(r'[\n\n]+', page_content)
        
        for para_num, paragraph in enumerate(paragraphs, 1):
            if not paragraph.strip():
                continue
            
            # 按句子分割
            sentences = re.split(r'(?<=[。！？])', paragraph)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 10:
                    continue
                
                # 检查是否包含环保关键词
                has_env_keyword = any(keyword in sentence for keyword in ENV_KEYWORDS)
                
                if has_env_keyword:
                    env_sentences.append({
                        "page": page_num,
                        "paragraph": para_num,
                        "sentence": sentence
                    })
    
    return env_sentences

def main():
    download_dir = "/Users/ami/Desktop/巨潮网作业/downloads"
    output_file = "/Users/ami/Desktop/巨潮网作业/工作流程/metadata/env_corpus.csv"
    
    results = []
    file_count = 0
    
    # 遍历所有公司目录
    for company_dir in os.listdir(download_dir):
        company_path = os.path.join(download_dir, company_dir)
        if not os.path.isdir(company_path):
            continue
        
        stock_code = company_dir.split("_")[0]
        company_name = company_dir.split("_")[1] if "_" in company_dir else company_dir
        
        txt_dir = os.path.join(company_path, "txt")
        if not os.path.exists(txt_dir):
            continue
        
        # 遍历所有TXT文件
        for txt_file in os.listdir(txt_dir):
            if not txt_file.endswith(".txt"):
                continue
            
            parts = txt_file.replace(".txt", "").split("_")
            if len(parts) >= 3:
                year = parts[1]
                report_type = "annual" if "年报" in txt_file else "esg"
                
                txt_path = os.path.join(txt_dir, txt_file)
                print(f"处理: {txt_file}")
                file_count += 1
                
                env_sentences = extract_env_sentences(txt_path)
                
                for item in env_sentences:
                    results.append({
                        "stock_code": stock_code,
                        "company_name": company_name,
                        "year": year,
                        "report_type": report_type,
                        "file_name": txt_file,
                        "page": item["page"],
                        "paragraph": item["paragraph"],
                        "sentence": item["sentence"]
                    })
    
    print(f"\n共处理 {file_count} 份报告")
    print(f"共提取 {len(results)} 条环保相关语句")
    
    # 写入CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['stock_code', 'company_name', 'year', 'report_type', 
                      'file_name', 'page', 'paragraph', 'sentence']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"已写入文件: {output_file}")

if __name__ == "__main__":
    main()
