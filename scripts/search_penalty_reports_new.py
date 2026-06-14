"""
搜索新一批上市公司的环境处罚报告
"""
import requests
import time
import random
import csv
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

# 新的17家公司列表
COMPANIES = {
    "600019": "宝钢股份",
    "000898": "鞍钢股份",
    "000932": "华菱钢铁",
    "000709": "河钢股份",
    "600188": "兖矿能源",
    "601088": "中国神华",
    "601225": "陕西煤业",
    "000983": "西山煤电",
    "601899": "紫金矿业",
    "600362": "江西铜业",
    "601600": "中国铝业",
    "603993": "洛阳钼业",
    "600309": "万华化学",
    "002648": "卫星化学",
    "600160": "巨化股份",
    "002001": "新和成",
    "600352": "浙江龙盛",
}

# 环境处罚相关关键词
PENALTY_KEYWORDS = [
    "收到生态环境局行政处罚决定书",
    "收到环保处罚决定书",
    "涉及环境行政处罚",
    "收到环保部门行政处罚书",
    "环境行政处罚事项",
    "收到《行政处罚决定书》",
    "环保处罚公告",
    "环境违法处罚",
    "生态环境处罚",
    "环境处罚",
    "环保处罚",
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

def search_penalty_reports(session, stock_code, company_name):
    """搜索环境处罚报告"""
    results = []
    
    for keyword in PENALTY_KEYWORDS:
        params = {
            "searchkey": f"{stock_code} {keyword}",
            "sdate": "2013-01-01",
            "edate": "2025-06-30",
            "isfulltext": "false",
            "sortName": "announcementTime",
            "sortType": "desc",
            "pageNum": 1,
            "pageSize": 20
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
                    ann_time = ann.get("announcementTime")
                    
                    if "处罚" in title or "行政处罚" in title:
                        pdf_url = f"http://static.cninfo.com.cn/{adjunct_url}" if adjunct_url else ""
                        
                        if ann_time:
                            publish_date = datetime.fromtimestamp(ann_time / 1000).strftime("%Y-%m-%d")
                            penalty_year = publish_date[:4]
                        else:
                            publish_date = ""
                            penalty_year = ""
                        
                        exists = any(r['title'] == title for r in results)
                        if not exists:
                            results.append({
                                "stock_code": stock_code,
                                "company_name": company_name,
                                "title": title,
                                "publish_date": publish_date,
                                "penalty_year": penalty_year,
                                "pdf_url": pdf_url,
                            })
        except Exception as e:
            print(f"搜索 {stock_code} {keyword} 出错: {e}")
    
    return results

def main():
    session = create_session()
    all_results = []
    
    print(f"开始搜索 {len(COMPANIES)} 家公司的环境处罚报告...")
    
    for stock_code, company_name in COMPANIES.items():
        print(f"\n搜索 {stock_code} {company_name}...")
        results = search_penalty_reports(session, stock_code, company_name)
        
        if results:
            print(f"  找到 {len(results)} 条处罚报告:")
            for r in results:
                # 判断是否为环境相关处罚
                is_env = any(keyword in r['title'] for keyword in ['生态环境', '环保', '环境违法', '环境处罚'])
                tag = "[环境处罚]" if is_env else "[其他处罚]"
                print(f"    {tag} {r['title']} ({r['publish_date']})")
            all_results.extend(results)
        else:
            print(f"  未找到处罚报告")
    
    print(f"\n\n共找到 {len(all_results)} 条处罚报告")
    
    output_file = "/Users/ami/Desktop/巨潮网作业/工作流程/metadata/penalty_reports_new.csv"
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['stock_code', 'company_name', 'title', 'publish_date', 'penalty_year', 'pdf_url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"已写入文件: {output_file}")

if __name__ == "__main__":
    main()
