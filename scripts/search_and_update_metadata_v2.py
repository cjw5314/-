"""
搜索并更新metadata的PDF URL和发布日期
修复版本：处理时间戳格式
"""
import csv
import requests
import time
import random
from datetime import datetime
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

def search_report_info(session, stock_code, year_str, report_type):
    """搜索报告的PDF链接和发布日期"""
    year = int(year_str)
    
    # 根据报告类型构建搜索关键词
    if report_type == "annual":
        keyword = f"{stock_code} {year}年年度报告"
    elif report_type == "esg":
        keyword = f"{stock_code} {year}社会责任报告"
    else:
        return "", ""
    
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
                adjunct_url = ann.get("adjunctUrl", "")
                
                # 验证条件
                if str(year) in title:
                    if report_type == "annual":
                        # 必须包含年度报告，排除摘要和问询函
                        if "年度报告" in title and "摘要" not in title and "问询函" not in title:
                            if adjunct_url:
                                pdf_url = f"http://static.cninfo.com.cn/{adjunct_url}"
                            else:
                                pdf_url = ""
                            
                            # 处理时间戳
                            ann_time = ann.get("announcementTime")
                            if ann_time:
                                # 时间戳是毫秒
                                publish_date = datetime.fromtimestamp(ann_time / 1000).strftime("%Y-%m-%d")
                            else:
                                publish_date = ""
                            
                            return pdf_url, publish_date
                    elif report_type == "esg":
                        if ("社会责任" in title or "环境、社会及管治" in title or "ESG" in title):
                            if adjunct_url:
                                pdf_url = f"http://static.cninfo.com.cn/{adjunct_url}"
                            else:
                                pdf_url = ""
                            
                            ann_time = ann.get("announcementTime")
                            if ann_time:
                                publish_date = datetime.fromtimestamp(ann_time / 1000).strftime("%Y-%m-%d")
                            else:
                                publish_date = ""
                            
                            return pdf_url, publish_date
    except Exception as e:
        print(f"搜索 {stock_code} {year} {report_type} 出错: {e}")
    
    return "", ""

def main():
    input_file = "/Users/ami/Desktop/巨潮网作业/工作流程/metadata/metadata_downloaded.csv"
    output_file = "/Users/ami/Desktop/巨潮网作业/工作流程/metadata/metadata_with_urls.csv"
    
    session = create_session()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        downloaded = list(csv.DictReader(f))
    
    success_count = 0
    total_count = len(downloaded)
    
    print(f"开始搜索 {total_count} 条记录的URL和发布日期...")
    
    for i, row in enumerate(downloaded):
        stock_code = row['stock_code']
        year_str = str(row['year'])
        report_type = row['report_type']
        
        print(f"\r处理进度: {i+1}/{total_count} - {stock_code} {year_str} {report_type}", end='')
        
        pdf_url, publish_date = search_report_info(session, stock_code, year_str, report_type)
        
        if pdf_url:
            row['pdf_url'] = pdf_url
            success_count += 1
        if publish_date:
            row['publish_date'] = publish_date
    
    print(f"\n\n成功获取 {success_count}/{total_count} 条记录的URL和日期")
    print("写入文件...")
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['doc_id', 'stock_code', 'company_name', 'report_type', 'year', 
                      'penalty_year', 'title', 'publish_date', 'pdf_url', 
                      'local_pdf_path', 'download_status', 'error_message']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(downloaded)
    
    print(f"已更新metadata文件: {output_file}")

if __name__ == "__main__":
    main()
