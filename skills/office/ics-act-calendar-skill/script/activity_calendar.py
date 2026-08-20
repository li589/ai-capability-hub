import os
import json
import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
BASE_URL = 'https://ics.xyzq.cn/icsapp'

def get_zd_apikey() -> Optional[str]:
    return os.environ.get('XYZD_APIKEY')

def parse_relative_date(date_str: str) -> Optional[str]:
    today = datetime.now().date()
    date_str = date_str.strip()
    
    relative_mapping = {
        '今天': 0, '今日': 0, '今天日期': 0, '今日日期': 0,
        '明天': 1, '明日': 1, '明天日期': 1, '明日日期': 1,
        '昨天': -1, '昨日': -1, '昨天日期': -1, '昨日日期': -1,
        '前天': -2, '前日': -2, '前天日期': -2, '前日日期': -2,
        '大前天': -3, '大前日': -3, '大前天日期': -3, '大前日日期': -3
    }
    
    if date_str in relative_mapping:
        delta_days = relative_mapping[date_str]
        return (today + timedelta(days=delta_days)).strftime('%Y%m%d')
    
    if date_str.endswith('天后'):
        try:
            days = int(date_str[:-2])
            return (today + timedelta(days=days)).strftime('%Y%m%d')
        except ValueError:
            return None
    
    if date_str.endswith('天前'):
        try:
            days = int(date_str[:-2])
            return (today - timedelta(days=days)).strftime('%Y%m%d')
        except ValueError:
            return None
    
    if date_str == '本周':
        weekday = today.weekday()
        monday = today - timedelta(days=weekday)
        return monday.strftime('%Y%m%d')
    
    if date_str == '下周':
        weekday = today.weekday()
        next_monday = today + timedelta(days=(7 - weekday))
        return next_monday.strftime('%Y%m%d')
    
    if date_str == '本月':
        return today.replace(day=1).strftime('%Y%m%d')
    
    if date_str == '下月':
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        return next_month.strftime('%Y%m%d')
    
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%Y%m%d')
    except ValueError:
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return date_str
        except ValueError:
            return None

def validate_date_range(start_date: str, end_date: str) -> bool:
    try:
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        
        if end_dt < start_dt:
            raise ValueError("结束日期必须大于或等于开始日期")
        
        date_diff = (end_dt - start_dt).days
        if date_diff >= 5:
            raise ValueError("日期跨度必须小于5天")
        
        return True
    except ValueError as e:
        raise Exception(f"日期验证失败: {e}")

def format_display_date(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, '%Y%m%d')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return date_str

def get_weekday(date_str: str) -> str:
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    try:
        dt = datetime.strptime(date_str, '%Y%m%d')
        return weekdays[dt.weekday()]
    except ValueError:
        return ''

def format_datetime(datetime_str: Optional[Any]) -> str:
    if datetime_str is None:
        return ''
    
    datetime_str = str(datetime_str).strip()
    
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']
    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            continue
    
    try:
        timestamp = int(datetime_str)
        if len(datetime_str) == 13:
            dt = datetime.fromtimestamp(timestamp / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        elif len(datetime_str) == 10:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        pass
    
    return datetime_str

def request_get(url: str, params: Dict[str, str]) -> Dict[str, Any]:
    try:
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()
        
        print(f"请求URL: {full_url}")
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500] if response.text else 'Empty'}")
        
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP请求失败: {str(e)}")

def get_user_info() -> str:
    url = f"{BASE_URL}/ai/skill/account/get-user-info"
    params = {
        'apiKey': get_zd_apikey(),
        'opStation': 'skillPowser',
        'skillName': 'ics-act-calendar-skill'
    }

    result = request_get(url, params)

    if result['respHead']['respCode'] == '0':
        return result['respBody']['userId']
    else:
        error_msg = result['respHead'].get('respMsg', '获取用户信息失败')
        raise Exception(error_msg)

def get_activity_calendar(user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    if not user_id:
        raise ValueError('userId 不能为空')
    
    url = f"{BASE_URL}/ai/skill/activity/calendar/single"
    params = {
        'opStation': 'skillPowser',
        'userId': user_id,
        'startDate': start_date,
        'endDate': end_date
    }

    result = request_get(url, params)

    if result['respHead']['respCode'] == '0':
        return result['respBody']
    else:
        error_msg = result['respHead'].get('respMsg', '获取活动日历失败')
        raise Exception(error_msg)

def process_activity_data(resp_body: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    status_mapping = {
        '1': '未开始',
        '2': '进行中',
        '3': '已结束'
    }
    
    processed_data = []
    for item in resp_body:
        activities = []
        for activity in item.get('activityList', []):
            status_code = str(activity.get('activityStatus', ''))
            activities.append({
                'title': activity.get('title', ''),
                'activityTypeName': activity.get('activityTypeName', ''),
                'primaryIndustry': activity.get('primaryIndustry', ''),
                'secondaryIndustry': activity.get('secondaryIndustry', ''),
                'activeAddress': activity.get('activeAddress', ''),
                'startTime': format_datetime(activity.get('startTime', '')),
                'endTime': format_datetime(activity.get('endTime', '')),
                'activityStatus': status_mapping.get(status_code, status_code)
            })
        
        processed_data.append({
            'date': item.get('date', ''),
            'activityCount': item.get('activityCount', 0),
            'activityList': activities
        })
    return processed_data

def save_results(data: List[Dict[str, Any]]) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(OUTPUT_DIR, 'calendar_results.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'已保存结果到: {file_path}')
    return file_path

def print_disclaimer() -> None:
    print('\n---')
    print('**免责声明**：以上内容通过技能（skill）自主调用数据生成，其准确性依赖底层模型的理解与处理能力，不保证信息完全无误，仅供参考，实际数据以兴业证券智达app平台数据为准。市场有风险，投资需谨慎。')

def print_markdown_results(data: List[Dict[str, Any]]) -> None:
    if not data:
        print('\n## 活动日历查询结果')
        print('\n查询期间无活动')
        return
    
    start_date = format_display_date(data[0]["date"])
    end_date = format_display_date(data[-1]["date"])
    print(f'\n## 活动日历查询结果 ({start_date} 至 {end_date})\n')
    
    total_activities = sum(item['activityCount'] for item in data)
    print(f'查询期间共 **{total_activities}** 场活动\n')
    
    for item in data:
        display_date = format_display_date(item['date'])
        weekday = get_weekday(item['date'])
        print(f'### {display_date} ({weekday})')
        print(f'活动数量：**{item["activityCount"]}** 场\n')
        
        if item['activityCount'] > 0:
            for i, activity in enumerate(item['activityList'], 1):
                print(f'**{i}. {activity["title"]}**')
                print(f'   - 活动类型：{activity["activityTypeName"]}')
                print(f'   - 活动状态：{activity["activityStatus"]}')
                print(f'   - 一级行业：{activity["primaryIndustry"]}')
                print(f'   - 二级行业：{activity["secondaryIndustry"]}')
                print(f'   - 活动城市：{activity["activeAddress"]}')
                print(f'   - 开始时间：{activity["startTime"]}')
                print(f'   - 结束时间：{activity["endTime"]}')
                print()
        else:
            print('   当日无活动\n')

def main(start_date: str, end_date: str) -> None:
    zd_apikey = get_zd_apikey()
    if not zd_apikey:
        print('错误: 环境变量 XYZD_APIKEY 未设置')
        print_disclaimer()
        return

    try:
        parsed_start = parse_relative_date(start_date)
        parsed_end = parse_relative_date(end_date)
        
        if parsed_start is None:
            raise Exception(f"无法解析开始日期: {start_date}")
        if parsed_end is None:
            raise Exception(f"无法解析结束日期: {end_date}")
        
        display_start = format_display_date(parsed_start)
        display_end = format_display_date(parsed_end)
        
        print(f"解析日期: {start_date} -> {display_start}, {end_date} -> {display_end}")
        
        validate_date_range(parsed_start, parsed_end)
        
        print('正在获取用户信息...')
        user_id = get_user_info()
        print(f'用户ID: {user_id}')

        print(f'正在查询活动日历: {display_start} 至 {display_end}')
        resp_body = get_activity_calendar(user_id, parsed_start, parsed_end)

        processed_data = process_activity_data(resp_body)
        save_results(processed_data)
        print_markdown_results(processed_data)

        print('查询完成')

    except Exception as e:
        print(f'错误: {e}')
    finally:
        print_disclaimer()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print('用法: python activity_calendar.py <startDate> <endDate>')
        print()
        print('日期格式支持:')
        print('  • 绝对日期: YYYY-MM-DD (如 2024-01-01)')
        print('  • 绝对日期: YYYYMMDD (如 20240101)')
        print('  • 相对日期: 今天, 明天, 昨天, 前天, 大前天')
        print('  • 相对天数: N天前, N天后 (如 3天前, 5天后)')
        print('  • 其他: 本周, 下周, 本月, 下月')
        print()
        print('日期约束:')
        print('  • 结束日期必须大于或等于开始日期')
        print('  • 日期跨度必须小于5天')
        print()
        print('示例:')
        print('  python activity_calendar.py 2024-01-01 2024-01-03')
        print('  python activity_calendar.py 今天 3天后')
        print('  python activity_calendar.py 前天 明天')
    else:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        main(start_date, end_date)
