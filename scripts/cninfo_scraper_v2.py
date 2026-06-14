"""
============================================================
 巨潮资讯网 (cninfo.com.cn) 年报 & CSR 报告下载爬虫 (v2)
 功能：①下载PDF  ②PDF→txt  ③按 股票代码_年份_类型 命名
 目标：全部A股上市公司 × 2011-2024
 存储：F:\漂绿指标年报
 策略：拟人化（慢速 + 随机UA + 随机延迟 + 分段休息）
 作者：大创项目组 (修正版: 使用 fulltextSearch API)
============================================================
"""

import requests, time, random, os, json, logging, sys, re
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SAVE_DIR = r"F:\漂绿指标年报"
YEARS = list(range(2011, 2025))
REQUEST_DELAY = (3.0, 6.0)
LONG_BREAK_EVERY = 30
LONG_BREAK_SECS = (60, 120)
MAX_RETRIES = 3
BATCH_DELAY = (0.5, 1.5)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

os.makedirs(SAVE_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(os.path.join(SAVE_DIR, "scraper.log"), encoding="utf-8"), logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

def create_session():
    s = requests.Session()
    retry = Retry(total=MAX_RETRIES, backoff_factor=1.5, status_forcelist=[429,500,502,503,504])
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter); s.mount("https://", adapter)
    s.headers.update({"Accept":"*/*","Accept-Language":"zh-CN,zh;q=0.9","Connection":"keep-alive"})
    return s

def random_headers():
    return {"User-Agent":random.choice(USER_AGENTS),"Referer":"http://www.cninfo.com.cn/new/fulltextSearch",
            "Origin":"http://www.cninfo.com.cn","X-Requested-With":"XMLHttpRequest"}

def human_delay(a=REQUEST_DELAY[0], b=REQUEST_DELAY[1]):
    time.sleep(random.uniform(a, b))

def clean_title(title):
    """去掉标题中的 HTML 标签"""
    return re.sub(r'<[^>]+>', '', title).strip()

def is_valid_pdf(path):
    return os.path.exists(path) and os.path.getsize(path) > 50000  # 至少50KB

def get_exchange(code):
    """推断股票所属交易所"""
    c = code.zfill(6)
    if c.startswith("6") or c.startswith("9"):
        return "sh"
    elif c.startswith("8") or c.startswith("4"):
        return "bj"
    else:
        return "sz"

def fetch_stock_list(session):
    """从巨潮 API 获取全部 A 股上市公司列表"""
    logger.info("获取股票列表...")
    for attempt in range(2):
        try:
            resp = session.get("http://www.cninfo.com.cn/new/data/szse_stock.json", headers=random_headers(), timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                sl = data.get("stockList") or data.get("stockInfoList") or data
                if isinstance(sl, dict):
                    sl = list(sl.values())
                if isinstance(sl, list):
                    stocks = []
                    for item in sl:
                        code = str(item.get("code","") or item.get("secCode","")).strip()
                        name = item.get("zwjc","") or item.get("name","") or item.get("secName","") or item.get("shortName","")
                        cat = item.get("category","A股")
                        if code and cat == "A股":
                            stocks.append({"code":code.zfill(6), "name":name, "market":get_exchange(code)})
                    logger.info(f"  -> {len(stocks)} 只 A股")
                    return stocks
        except Exception as e:
            logger.error(f"获取股票列表出错: {e}")
            time.sleep(5)
    return []

def query_one(session, stock_code, year, report_type):
    """
    用 fulltextSearch 查某公司某年某类型报告
    report_type: "年报" 或 "CSR"
    """
    # 年报在"Y年"发布，覆盖的是"Y-1年"的财报
    # 对于年度报告(Year)：搜索 Y-01 ~ Y+1-06
    # 如2023年报在2024年1-4月发布，搜索2024-01-01~2024-06-30
    if report_type == "年报":
        pub_year = year + 1  # 年报实际发布年份
        sdate = f"{pub_year}-01-01"
        edate = f"{pub_year}-06-30"
        keywords = [f"{year}年年度报告", f"{year}年年报"]
        bad_words = ["摘要", "英文", "业绩快报", "业绩预告"]
    else:
        # CSR 报告可能在当年或次年发布
        sdate = f"{year}-01-01"
        edate = f"{year+1}-06-30"
        keywords = ["社会责任报告", "可持续发展报告", "ESG报告", "环境社会及管治报告"]
        bad_words = []

    params = {"searchkey":stock_code, "sdate":sdate, "edate":edate,
              "isfulltext":"false", "sortName":"announcementTime", "sortType":"desc",
              "pageNum":1, "pageSize":30}

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.post("http://www.cninfo.com.cn/new/fulltextSearch/full",
                                headers=random_headers(), data=params, timeout=30)
            if resp.status_code != 200:
                logger.warning(f"  [{stock_code}] {year} {report_type} HTTP {resp.status_code}")
                human_delay()
                continue
            data = resp.json()
            anns = data.get("announcements", [])
            best = None
            for a in anns:
                title = clean_title(a.get("announcementTitle",""))
                # 含 report_type 的关键词
                if any(kw in title for kw in keywords):
                    if any(bw in title for bw in bad_words):
                        continue
                    # 优先选完整的（非摘要、非英文）
                    if "摘要" in title or "英文" in title:
                        if best is None:
                            best = a
                    else:
                        best = a  # 完整报告优先
                        break
            if best:
                return {"title":clean_title(best.get("announcementTitle","")),
                        "adjunctUrl":best.get("adjunctUrl",""),
                        "size":best.get("adjunctSize",0)}
            return None
        except Exception as e:
            logger.error(f"  [{stock_code}] {year} {report_type} 查询出错: {e}")
            if attempt < MAX_RETRIES-1:
                time.sleep(5)
    return None

def download_pdf(session, adjunct_url, save_path):
    if not adjunct_url:
        return False
    url = f"http://static.cninfo.com.cn/{adjunct_url}"
    for attempt in range(MAX_RETRIES):
        try:
            r = session.get(url, headers=random_headers(), timeout=120, stream=True)
            if r.status_code == 200:
                size = 0
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk); size += len(chunk)
                if size > 50000:
                    return True
                os.remove(save_path)
            human_delay(1,2)
        except Exception as e:
            logger.error(f"  下载异常: {e}")
            time.sleep(5)
    return False

def pdf_to_txt(pdf_path, txt_path):
    try:
        import pdfplumber
    except ImportError:
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texts = [p.extract_text() or "" for p in pdf.pages]
        full = "\n".join(texts)
        if not full.strip():
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                full = "\\n".join(p.extract_text() or "" for p in reader.pages)
            except:
                pass
        if full.strip():
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(full)
            return True
    except Exception as e:
        logger.error(f"  PDF转txt失败: {e}")
    return False

def download_company(session, stock_info, years=None, download=True, convert=True):
    code, name, market = stock_info["code"], stock_info["name"], stock_info["market"]
    if years is None:
        years = YEARS
    cdir = os.path.join(SAVE_DIR, f"{code}_{name}")
    pdf_dir = os.path.join(cdir, "pdf"); txt_dir = os.path.join(cdir, "txt")
    os.makedirs(pdf_dir, exist_ok=True); os.makedirs(txt_dir, exist_ok=True)
    count = 0
    for year in years:
        for rtype in ["年报", "CSR"]:
            pdf_path = os.path.join(pdf_dir, f"{code}_{year}_{rtype}.pdf")
            txt_path = os.path.join(txt_dir, f"{code}_{year}_{rtype}.txt")
            if is_valid_pdf(pdf_path):
                if convert and not os.path.exists(txt_path):
                    pdf_to_txt(pdf_path, txt_path)
                continue
            if download:
                logger.info(f"[{code}] {name} {year} {rtype}...")
                ann = query_one(session, code, year, rtype)
                if ann and ann["adjunctUrl"]:
                    if download_pdf(session, ann["adjunctUrl"], pdf_path):
                        logger.info(f"  v {rtype}成功 ({ann['title'][:30]})")
                        count += 1
                        if convert:
                            pdf_to_txt(pdf_path, txt_path)
                    else:
                        logger.warning(f"  x {rtype}下载失败")
                else:
                    logger.info(f"  - 未找到{rtype}")
                human_delay(*BATCH_DELAY)
        human_delay(1,2)
    return count

def run(session, stock_list=None, test_mode=False, offset=0, limit=0):
    if stock_list is None:
        stock_list = fetch_stock_list(session)
    if test_mode:
        logger.info("=== 测试模式: 只跑 000001 平安银行 ===")
        stock_list = [s for s in stock_list if s["code"]=="000001"] or [{"code":"000001","name":"平安银行","market":"sz"}]
    if limit > 0:
        stock_list = stock_list[offset:offset+limit]
        logger.info(f"=== 分段模式: offset={offset}, limit={limit}, 本次处理 {len(stock_list)} 家 ===")
    total = len(stock_list)
    logger.info(f"=== 开始，共 {total} 家，存储到 {SAVE_DIR} ===")
    gcount = 0
    for idx, stock in enumerate(stock_list, 1):
        logger.info(f"\n[{idx}/{total}] {stock['code']} {stock['name']}")
        try:
            c = download_company(session, stock)
            gcount += c
            logger.info(f"  -> 完成，本次下载 {c} 个")
        except Exception as e:
            logger.error(f"  异常: {e}")
            human_delay(10,20)
        if idx % LONG_BREAK_EVERY == 0:
            rest = random.uniform(*LONG_BREAK_SECS)
            logger.info(f"=== 已处理 {idx}/{total}，休息 {rest:.0f}秒 ===")
            time.sleep(rest)
        else:
            human_delay(2,5)
    logger.info(f"\n=== 全部完成！共下载 {gcount} 个文件 ===")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="巨潮资讯网年报/CSR爬虫 v2")
    parser.add_argument("--test", action="store_true", help="测试模式")
    parser.add_argument("--max", type=int, default=0, help="最大公司数")
    parser.add_argument("--offset", type=int, default=0, help="起始索引")
    parser.add_argument("--limit", type=int, default=0, help="处理数量（0=全部）")
    args = parser.parse_args()
    logger.info("="*50)
    logger.info(f"爬虫启动 | 存储: {SAVE_DIR} | 年份: {YEARS[0]}-{YEARS[-1]}")
    logger.info("="*50)
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber未安装, PDF转txt不可用。运行: pip install pdfplumber")
    session = create_session()
    run(session, test_mode=args.test, offset=args.offset, limit=args.limit if args.limit > 0 else args.max)
