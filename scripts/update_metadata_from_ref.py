"""
从参考文件更新metadata的URL和发布日期
"""
import csv

def main():
    # 读取现有的metadata文件
    with open('工作流程/metadata/metadata_downloaded.csv', 'r', encoding='utf-8') as f:
        downloaded = list(csv.DictReader(f))

    # 读取参考的metadata_final_v2.csv
    with open('工作流程/metadata/metadata_final_v2.csv', 'r', encoding='utf-8') as f:
        reference = list(csv.DictReader(f))

    # 创建参考数据的索引
    ref_index = {}
    for row in reference:
        key = f"{row['stock_code']}_{row['year']}_{row['report_type']}"
        ref_index[key] = {'pdf_url': row['pdf_url'], 'publish_date': row['publish_date']}

    # 更新下载的metadata
    updated_count = 0
    for row in downloaded:
        key = f"{row['stock_code']}_{row['year']}_{row['report_type']}"
        if key in ref_index:
            ref_data = ref_index[key]
            if ref_data['pdf_url']:
                row['pdf_url'] = ref_data['pdf_url']
                updated_count += 1
            if ref_data['publish_date']:
                row['publish_date'] = ref_data['publish_date']

    print(f'从参考文件更新了 {updated_count} 条记录')

    # 写入更新后的文件
    output_file = '工作流程/metadata/metadata_with_urls.csv'
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['doc_id', 'stock_code', 'company_name', 'report_type', 'year', 
                      'penalty_year', 'title', 'publish_date', 'pdf_url', 
                      'local_pdf_path', 'download_status', 'error_message']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(downloaded)

    print(f'文件已写入: {output_file}')

if __name__ == "__main__":
    main()
