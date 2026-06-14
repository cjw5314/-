"""
飘绿指标计算脚本
基于年报和CSR报告计算6个飘绿相关指标
"""
import os
import re
import csv
import pandas as pd

# ============ 1. 读取字典文件，创建关键词集合 ============

def load_env_keywords():
    """读取环保字典.csv"""
    env_keywords = set()
    try:
        # 尝试GB18030编码
        df = pd.read_csv('/Users/ami/Desktop/巨潮网作业/标绿/环保字典.csv', encoding='gb18030')
        if '词汇' in df.columns:
            for word in df['词汇'].dropna():
                if word.strip():
                    env_keywords.add(word.strip())
        print(f"环保字典加载完成: {len(env_keywords)} 个词")
    except Exception as e:
        print(f"读取环保字典出错: {e}")
    return env_keywords

def load_vague_words():
    """读取模糊词汇扩展表"""
    vague_words = set()
    try:
        df = pd.read_csv('/Users/ami/Desktop/巨潮网作业/标绿/模糊词汇扩展表——人工标注.csv', encoding='gb18030')
        # 尝试不同的列名
        for col in ['扩展词汇', '词汇', '词语', '模糊词']:
            if col in df.columns:
                for word in df[col].dropna():
                    if word.strip():
                        vague_words.add(word.strip())
                break
        print(f"模糊词汇加载完成: {len(vague_words)} 个词")
    except Exception as e:
        print(f"读取模糊词汇出错: {e}")
    return vague_words

def load_positive_words():
    """读取正面词汇扩展表（Excel格式）"""
    positive_words = set()
    try:
        df = pd.read_excel('/Users/ami/Desktop/巨潮网作业/标绿/正面词汇扩展表——人工标注.xls', engine='xlrd')
        
        # 特殊情况：列名中包含所有正面词汇（用逗号分隔）
        if len(df.columns) == 1:
            header_text = df.columns[0]
            # 用中文逗号或英文逗号分割
            words = re.split(r'[,，、]', header_text)
            for word in words:
                word = word.strip()
                if word and len(word) >= 2:  # 至少2个字符
                    positive_words.add(word)
        else:
            # 标准格式：找词汇列
            for col in df.columns:
                if '词' in str(col) or '词汇' in str(col):
                    for word in df[col].dropna():
                        if isinstance(word, str) and word.strip():
                            positive_words.add(word.strip())
                    break
            # 如果没找到，按顺序找第二列
            if not positive_words and len(df.columns) > 1:
                for word in df.iloc[:, 1].dropna():
                    if isinstance(word, str) and word.strip():
                        positive_words.add(word.strip())
        
        print(f"正面词汇加载完成: {len(positive_words)} 个词")
        if len(positive_words) > 0:
            print(f"  示例: {list(positive_words)[:10]}")
    except Exception as e:
        print(f"读取正面词汇出错: {e}")
    return positive_words

def load_evidence_words():
    """读取新证据词汇扩展表"""
    evidence_words = set()
    try:
        df = pd.read_csv('/Users/ami/Desktop/巨潮网作业/标绿/新证据词汇扩展表——人工标注.csv', encoding='utf-8')
        # 尝试不同的列名
        for col in ['扩展词汇', '词汇', '词语', '证据词']:
            if col in df.columns:
                for word in df[col].dropna():
                    if word.strip():
                        evidence_words.add(word.strip())
                break
        print(f"证据词汇加载完成: {len(evidence_words)} 个词")
    except Exception as e:
        print(f"读取证据词汇出错: {e}")
    return evidence_words

# 加载所有关键词
print("=== 加载关键词字典 ===")
ENV_KEYWORDS = load_env_keywords()
VAGUE_WORDS = load_vague_words()
POSITIVE_WORDS = load_positive_words()
EVIDENCE_WORDS = load_evidence_words()

print(f"\n关键词汇总:")
print(f"  环保关键词: {len(ENV_KEYWORDS)} 个")
print(f"  模糊词汇: {len(VAGUE_WORDS)} 个")
print(f"  正面词汇: {len(POSITIVE_WORDS)} 个")
print(f"  证据词汇: {len(EVIDENCE_WORDS)} 个")

# ============ 2. 处理单个文件的函数 ============

def process_one_file(file_path, report_type, company, year):
    """
    处理单个报告文件，计算6个飘绿指标
    
    返回:
        dict: 包含公司名、年份、报告类型、6个指标及基础统计
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except:
        try:
            with open(file_path, 'r', encoding='gb18030', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return None
    
    # 基础统计
    total_chars = len(text)
    
    # 分句：按句号、问号、感叹号、分号、换行分割
    sentences = re.split(r'[。！？；\n]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_sentences = len(sentences)
    
    if total_sentences == 0:
        total_sentences = 1  # 避免除零
    
    # ============ 计算6个指标 ============
    
    # 1. 环境关键词密度 env_density
    env_count = 0
    for keyword in ENV_KEYWORDS:
        env_count += text.count(keyword)
    env_density = (env_count / total_chars) * 1000 if total_chars > 0 else 0
    
    # 2. 模糊表述比例 vague_sent_ratio
    vague_sent_count = 0
    for sentence in sentences:
        for vague_word in VAGUE_WORDS:
            if vague_word in sentence:
                vague_sent_count += 1
                break  # 一个句子只计算一次
    vague_sent_ratio = vague_sent_count / total_sentences
    
    # 3. 量化披露比例 quant_sent_ratio
    # 匹配数字+常用环境单位
    quant_pattern = r'\d+(?:\.\d+)?\s*(?:[万亿千百]?[吨千瓦时]?|%|万元|亿|千克|立方米|次|个|项|套|人|天|年|ha|℃|mg|Nm3)'
    quant_sent_count = 0
    for sentence in sentences:
        matches = re.findall(quant_pattern, sentence)
        # 过滤掉纯年份（如"2015年"在某些语境下不算量化）
        valid_matches = []
        for m in matches:
            # 排除单独的年份数字
            if not re.match(r'^\d{4}$', m.strip()):
                valid_matches.append(m)
            elif '年' not in m:  # 如果不是"X年"格式
                valid_matches.append(m)
        if valid_matches:
            quant_sent_count += 1
    quant_sent_ratio = quant_sent_count / total_sentences
    
    # 4. 环保投入是否披露 has_investment
    investment_pattern = r'(?:环保投入|环境投资|环保支出|环保资金|环境治理投入)[^\d]*(\d+(?:\.\d+)?)\s*(?:万|亿)?元?'
    investment_match = re.search(investment_pattern, text)
    has_investment = 1 if investment_match else 0
    
    # 5. 正面宣传强度 positive_intensity
    positive_count = 0
    for keyword in POSITIVE_WORDS:
        positive_count += text.count(keyword)
    positive_intensity = (positive_count / total_chars) * 1000 if total_chars > 0 else 0
    
    # 6. 证据密度（每页）evidence_per_page
    evidence_count = 0
    for keyword in EVIDENCE_WORDS:
        evidence_count += text.count(keyword)
    
    # 估算页数：总字符数 ÷ 500
    estimated_pages = max(1, round(total_chars / 500))
    evidence_per_page = evidence_count / estimated_pages
    
    return {
        '公司': company,
        '年份': year,
        '报告类型': report_type,
        'env_density': round(env_density, 4),
        'vague_sent_ratio': round(vague_sent_ratio, 4),
        'quant_sent_ratio': round(quant_sent_ratio, 4),
        'has_investment': has_investment,
        'positive_intensity': round(positive_intensity, 4),
        'evidence_per_page': round(evidence_per_page, 4),
        '总字符数': total_chars,
        '总句子数': total_sentences
    }

# ============ 3. 遍历所有公司报告 ============

def main():
    download_dir = "/Users/ami/Desktop/巨潮网作业/downloads"
    output_file = "/Users/ami/Desktop/巨潮网作业/标绿/greenwashing_results.csv"
    
    results = []
    processed_count = 0
    
    print("\n=== 开始处理报告 ===")
    
    # 遍历所有公司目录
    for company_dir in os.listdir(download_dir):
        company_path = os.path.join(download_dir, company_dir)
        if not os.path.isdir(company_path):
            continue
        
        # 解析公司名称
        parts = company_dir.split("_")
        company_name = parts[1] if len(parts) > 1 else company_dir
        
        txt_dir = os.path.join(company_path, "txt")
        if not os.path.exists(txt_dir):
            continue
        
        # 遍历所有TXT文件
        for txt_file in os.listdir(txt_dir):
            if not txt_file.endswith(".txt"):
                continue
            
            # 解析文件名
            file_parts = txt_file.replace(".txt", "").split("_")
            if len(file_parts) < 3:
                continue
            
            stock_code = file_parts[0]
            year = file_parts[1]
            report_type = "年报" if "年报" in file_parts[2] else "CSR"
            
            txt_path = os.path.join(txt_dir, txt_file)
            print(f"处理: {company_name}_{year}_{report_type}")
            
            result = process_one_file(txt_path, report_type, company_name, year)
            if result:
                results.append(result)
                processed_count += 1
    
    print(f"\n共处理 {processed_count} 份报告")
    
    # ============ 4. 输出结果 ============
    if results:
        df = pd.DataFrame(results)
        # 按指定列排序
        columns = ['公司', '年份', '报告类型', 'env_density', 'vague_sent_ratio', 
                   'quant_sent_ratio', 'has_investment', 'positive_intensity', 
                   'evidence_per_page', '总字符数', '总句子数']
        df = df[columns]
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"结果已保存到: {output_file}")
        print(f"共 {len(results)} 条记录")
        
        # 打印统计摘要
        print("\n=== 统计摘要 ===")
        print(f"平均环境关键词密度: {df['env_density'].mean():.4f}")
        print(f"平均模糊表述比例: {df['vague_sent_ratio'].mean():.4f}")
        print(f"平均量化披露比例: {df['quant_sent_ratio'].mean():.4f}")
        print(f"有环保投入披露的比例: {df['has_investment'].mean()*100:.2f}%")
        print(f"平均正面宣传强度: {df['positive_intensity'].mean():.4f}")
        print(f"平均证据密度: {df['evidence_per_page'].mean():.4f}")

if __name__ == "__main__":
    main()
