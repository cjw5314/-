"""
更新metadata文件，添加PDF在线链接(UCL)和发布日期
"""
import csv
import requests
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

def create_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=2.0, status_forcelist=[429,500,502,503,504])
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

def random_headers():
    return {"User-Agent": random.choice(USER_AGENTS),
            "Referer": "http://www.cninfo.com.cn/new/fulltextSearch",
            "Origin": "http://www.cninfo.com.cn"}

def search_report_info(session, stock_code, year, report_type):
    """搜索报告的PDF链接和发布日期"""
    keywords = []
    if report_type == "annual":
        keywords = [
            f"{stock_code} {year}年年度报告",
            f"{year}年年度报告",
        ]
    elif report_type == "esg":
        keywords = [
            f"{stock_code} {year}社会责任报告",
            f"{stock_code} {year}环境、社会及管治报告",
            f"{stock_code} {year} ESG报告",
            f"{year}年度社会责任报告",
        ]
    
    for keyword in keywords:
        params = {
            "searchkey": keyword,
            "sdate": f"{year}-01-01",
            "edate": f"{year+1}-06-30",
            "isfulltext": "false",
            "sortName": "announcementTime",
            "sortType": "desc",
            "pageNum": 1,
            "pageSize": 10
        }

        try:
            time.sleep(random.uniform(1, 2))
            resp = session.post("http://www.cninfo.com.cn/new/fulltextSearch/full",
                               headers=random_headers(), data=params, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                anns = data.get("announcements") or []
                
                for ann in anns:
                    title = ann.get("announcementTitle", "").replace("<em>", "").replace("</em>", "")
                    # 验证年份和类型
                    if str(year) in title:
                        if report_type == "annual":
                            if "年度报告" in title and "摘要" not in title:
                                pdf_url = ann.get("adjunctUrl", "")
                                publish_date = ann.get("announcementTime", "")[:10]
                                return pdf_url, publish_date
                        elif report_type == "esg":
                            if ("社会责任" in title or "环境、社会及管治" in title or "ESG" in title):
                                pdf_url = ann.get("adjunctUrl", "")
                                publish_date = ann.get("announcementTime", "")[:10]
                                return pdf_url, publish_date
        except Exception as e:
            print(f"搜索 {stock_code} {year} {report_type} 出错: {e}")
    
    return "", ""

def main():
    input_file = "/Users/ami/Desktop/巨潮网作业/工作流程/metadata/metadata_downloaded.csv"
    output_file = "/Users/ami/Desktop/巨潮网作业/工作流程/metadata/metadata_with_urls.csv"
    
    session = create_session()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"共 {len(rows)} 条记录需要更新")
    
    for i, row in enumerate(rows):
        stock_code = row['stock_code']
        year = int(row['year'])
        report_type = row['report_type']
        
        print(f"\r处理中: {i+1}/{len(rows)} - {stock_code} {year} {report_type}", end='')
        
        pdf_url, publish_date = search_report_info(session, stock_code, year, report_type)
        
        if pdf_url:
            # 确保URL格式正确
            if not pdf_url.startswith('http'):
                pdf_url = f"http://static.cninfo.com.cn/{pdf_url}"
            row['pdf_url'] = pdf_url
        
        if publish_date:
            row['publish_date'] = publish_date
    
    print("\n\n写入文件...")
    
    # 写入更新后的文件
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['doc_id', 'stock_code', 'company_name', 'report_type', 'year', 
                      'penalty_year', 'title', 'publish_date', 'pdf_url', 
                      'local_pdf_path', 'download_status', 'error_message']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"已更新metadata文件: {output_file}")

if __name__ == "__main__":
    main()
