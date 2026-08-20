import os
import json
import requests
from urllib.parse import urlencode

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_zd_apikey():
    return os.environ.get('XYZD_APIKEY')


def request_get(url, params):
    query_string = urlencode(params)
    full_url = f"{url}?{query_string}"
    try:
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()
        print(f"请求URL: {full_url}")
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500] if response.text else 'Empty'}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        raise Exception(f"网络请求失败: {str(e)}")


def validate_request_num(request_num):
    try:
        num = int(request_num)
        if num < 1 or num > 20:
            return 20
        return num
    except (ValueError, TypeError):
        return 20


def get_user_info():
    url = 'https://ics.xyzq.cn/icsapp/ai/skill/account/get-user-info'
    params = {
        'apiKey': get_zd_apikey(),
        'opStation': 'skillPowser',
        'skillName': 'ics-search-info-list-skill'
    }

    result = request_get(url, params)

    if not result or 'respHead' not in result:
        raise Exception('获取用户信息失败：响应格式错误')
    
    if result['respHead']['respCode'] == '0':
        if 'respBody' not in result or 'userId' not in result['respBody']:
            raise Exception('获取用户信息失败：userId 不存在')
        return result['respBody']['userId']
    else:
        error_msg = result['respHead'].get('respMsg', '获取用户信息失败')
        raise Exception(f'获取用户信息失败：{error_msg}')


def search_info(user_id, keyword, request_num=20):
    if not user_id:
        raise ValueError('userId 不能为空')
    
    if not keyword:
        raise ValueError('keyword 不能为空')
    
    url = 'https://ics.xyzq.cn/icsapp/ai/skill/search/searchinfo'
    params = {
        'opStation': 'skillPowser',
        'userId': user_id,
        'keyword': keyword,
        'requestNum': validate_request_num(request_num)
    }

    result = request_get(url, params)

    if not result or 'respHead' not in result:
        raise Exception('搜索失败：响应格式错误')
    
    if result['respHead']['respCode'] == '0':
        if 'respBody' not in result:
            raise Exception('搜索失败：响应体为空')
        return result['respBody']
    else:
        error_msg = result['respHead'].get('respMsg', '搜索请求失败')
        raise Exception(f'搜索失败：{error_msg}')


LIST_NAME_MAPPING = {
    'reportList': '研报列表',
    'activityList': '活动列表',
    'subjectList': '专题列表',
    'researcherList': '研究员列表',
    'projectList': '项目列表',
    'noticeList': '公告列表',
    'articleList': '文章列表',
    'newsList': '资讯列表',
    'stockList': '标的列表'
}


def save_combined_results(resp_body):
    combined_data = {}
    for list_name, chinese_name in LIST_NAME_MAPPING.items():
        data = resp_body.get(list_name)
        if data and isinstance(data, list) and len(data) > 0:
            combined_data[chinese_name] = data

    file_path = os.path.join(OUTPUT_DIR, 'search_results.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)
    print(f'已保存整合结果到: search_results.json')
    return file_path


def get_item_summary(item, list_name):
    common_fields = ['title', 'name', 'content', 'summary', 'description']
    if list_name == '研报列表':
        fields = ['title', 'reportDate', 'author', 'researchTeam']
    elif list_name == '活动列表':
        fields = ['title', 'showTime', 'activityTypeName']
    elif list_name == '专题列表':
        fields = ['title', 'showTime', 'specialIntroduction']
    elif list_name == '研究员列表':
        fields = ['researcherName', 'certificateNo', 'researchTeam', 'researcherProfile']
    elif list_name == '项目列表':
        fields = ['companyName', 'bondName', 'bondCode']
    elif list_name == '公告列表':
        fields = ['noticeTitle', 'noticeType']
    elif list_name == '文章列表':
        fields = ['title', 'showTime', 'articleAuthorsName']
    elif list_name == '资讯列表':
        fields = ['title', 'showTime', 'supplierName']
    elif list_name == '标的列表':
        fields = ['stockName', 'stockCode', 'exchCdDesc']
    else:
        fields = common_fields

    summary = {}
    for field in fields:
        if field in item and item[field]:
            summary[field] = item[field]
    return summary


def print_disclaimer():
    print('\n---')
    print('**免责声明**：以上内容通过技能（skill）自主调用数据生成，其准确性依赖底层模型的理解与处理能力，不保证信息完全无误，仅供参考，实际数据以兴业证券智达app平台数据为准。市场有风险，投资需谨慎。')


def print_markdown_results(resp_body):
    print('\n## 搜索结果\n')

    available_lists = []
    for list_name, chinese_name in LIST_NAME_MAPPING.items():
        data = resp_body.get(list_name)
        if data and isinstance(data, list) and len(data) > 0:
            available_lists.append((list_name, chinese_name, data))
            print(f'- **{chinese_name}**：{len(data)} 条')

    print()

    for list_name, chinese_name, data in available_lists:
        print(f'### {chinese_name}\n')
        for i, item in enumerate(data, 1):
            summary = get_item_summary(item, chinese_name)
            print(f'**{i}.** {json.dumps(summary, ensure_ascii=False)}')
        print()


def main(keyword, request_num=20):
    zd_apikey = get_zd_apikey()
    if not zd_apikey:
        print('错误: 环境变量 XYZD_APIKEY 未设置')
        print_disclaimer()
        return

    if not keyword:
        print('错误: 搜索关键词不能为空')
        print_disclaimer()
        return

    try:
        print('正在获取用户信息...')
        user_id = get_user_info()
        print(f'用户ID: {user_id}')

        print(f'正在搜索: {keyword}')
        resp_body = search_info(user_id, keyword, request_num)

        save_combined_results(resp_body)
        print_markdown_results(resp_body)

        print('搜索完成')

    except ValueError as e:
        print(f'参数错误: {e}')
    except Exception as e:
        print(f'错误: {e}')
    finally:
        print_disclaimer()


if __name__ == '__main__':
    import sys
    keyword = sys.argv[1] if len(sys.argv) > 1 else ''
    request_num = sys.argv[2] if len(sys.argv) > 2 else '20'

    if not keyword:
        print('用法: python search.py <keyword> [requestNum]')
        print('requestNum 范围: 1-20, 默认: 20')
    else:
        main(keyword, request_num)
