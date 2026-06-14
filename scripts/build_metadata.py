"""
构建metadata.csv文件
根据download目录中已下载的PDF文件生成metadata
"""
import os
import random
import hashlib

DOWNLOAD_DIR = "/Users/ami/Desktop/巨潮网作业/downloads"
OUTPUT_FILE = "/Users/ami/Desktop/巨潮网作业/工作流程/metadata/metadata_downloaded.csv"

# 股票代码到公司全称的映射
STOCK_TO_COMPANY = {
    "000401": "唐山冀东水泥股份有限公司",
    "000488": "山东晨鸣纸业集团股份有限公司",
    "000538": "云南白药集团股份有限公司",
    "000726": "鲁泰纺织股份有限公司",
    "000877": "新疆天山水泥股份有限公司",
    "002042": "华孚时尚股份有限公司",
    "002078": "山东太阳纸业股份有限公司",
    "002422": "四川科伦药业股份有限公司",
    "600028": "中国石油化工股份有限公司",
    "600196": "上海复星医药(集团)股份有限公司",
    "600276": "江苏恒瑞医药股份有限公司",
    "600332": "广州白云山医药集团股份有限公司",
    "600346": "恒力石化股份有限公司",
    "600567": "山鹰国际控股股份公司",
    "600585": "安徽海螺水泥股份有限公司",
    "600801": "华新水泥股份有限公司",
    "002493": "荣盛石化股份有限公司",
}

def generate_doc_id(stock_code, report_type, year):
    """生成唯一doc_id: {stock_code}_{report_type}_{year}_{random4}"""
    random4 = hashlib.md5(f"{stock_code}{report_type}{year}{random.random()}".encode()).hexdigest()[:8]
    return f"{stock_code}_{report_type}_{year}_{random4}"

def get_report_type(file_name):
    """从文件名判断报告类型"""
    if "_年报." in file_name:
        return "annual"
    elif "_CSR." in file_name:
        return "esg"
    return None

def get_title(report_type, year, company_name):
    """生成标题"""
    if report_type == "annual":
        return f"{year}年年度报告"
    elif report_type == "esg":
        return f"{year}年度社会责任报告"
    return ""

def main():
    rows = []
    rows.append([
        "doc_id", "stock_code", "company_name", "report_type", "year", 
        "penalty_year", "title", "publish_date", "pdf_url", 
        "local_pdf_path", "download_status", "error_message"
    ])
    
    # 遍历download目录
    for company_dir in os.listdir(DOWNLOAD_DIR):
        if not os.path.isdir(os.path.join(DOWNLOAD_DIR, company_dir)):
            continue
            
        stock_code = company_dir.split("_")[0]
        company_name = STOCK_TO_COMPANY.get(stock_code, "")
        
        pdf_dir = os.path.join(DOWNLOAD_DIR, company_dir, "pdf")
        if not os.path.exists(pdf_dir):
            continue
            
        for pdf_file in os.listdir(pdf_dir):
            if not pdf_file.endswith(".pdf"):
                continue
                
            # 解析文件名: {stock_code}_{year}_{type}.pdf
            parts = pdf_file.replace(".pdf", "").split("_")
            if len(parts) >= 3:
                year = parts[1]
                report_type = get_report_type(pdf_file)
                
                if report_type and year.isdigit():
                    doc_id = generate_doc_id(stock_code, report_type, year)
                    title = get_title(report_type, year, company_name)
                    local_pdf_path = f"{company_dir}\\pdf\\{pdf_file}"
                    
                    rows.append([
                        doc_id,
                        stock_code,
                        company_name,
                        report_type,
                        int(year),
                        "",  # penalty_year
                        title,
                        "",  # publish_date
                        "",  # pdf_url
                        local_pdf_path,
                        "success",
                        ""   # error_message
                    ])
    
    # 按股票代码和年份排序
    rows[1:] = sorted(rows[1:], key=lambda x: (x[1], x[4]))
    
    # 写入CSV
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        for row in rows:
            # 处理包含逗号的字段
            quoted_row = []
            for item in row:
                if isinstance(item, str) and ',' in item:
                    quoted_row.append(f'"{item}"')
                else:
                    quoted_row.append(str(item))
            f.write(','.join(quoted_row) + '\n')
    
    print(f"已生成metadata文件: {OUTPUT_FILE}")
    print(f"共 {len(rows)-1} 条记录")

if __name__ == "__main__":
    main()
