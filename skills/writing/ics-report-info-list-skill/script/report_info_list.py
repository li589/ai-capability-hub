import os
import sys
import json
import requests
import time
import re

API_TIMEOUT = 30
MAX_KEYWORD_LENGTH = 100
SQL_INJECTION_PATTERNS = [r"['\";]", r"--", r"\/\*", r"\*\/", r"UNION", r"SELECT", r"INSERT", r"DELETE", r"DROP"]

def validate_keyword(keyword):
    if not keyword or not isinstance(keyword, str):
        return False, "关键词不能为空"
    
    if len(keyword) > MAX_KEYWORD_LENGTH:
        return False, f"关键词长度不能超过{MAX_KEYWORD_LENGTH}个字符"
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, keyword, re.IGNORECASE):
            return False, "关键词包含非法字符"
    
    return True, None

def get_user_info(zd_apikey):
    url = "https://ics.xyzq.cn/icsapp/ai/skill/account/get-user-info"
    params = {
        "apiKey": zd_apikey,
        "opStation": "skillPowser",
        "skillName": "ics-report-info-list-skill"
    }
    
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        result = response.json()
        
        resp_head = result.get("respHead", {})
        resp_code = resp_head.get("respCode", -1)
        
        if str(resp_code) != "0":
            resp_msg = resp_head.get("respMsg", "请求失败")
            return None, resp_msg
        
        resp_body = result.get("respBody", {})
        user_id = resp_body.get("userId")
        
        if not user_id:
            return None, "userId为空"
        
        return user_id, None
    
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except requests.exceptions.RequestException as e:
        return None, f"网络请求失败: {str(e)}"
    except json.JSONDecodeError:
        return None, "数据解析失败"
    except Exception as e:
        return None, f"未知错误: {str(e)}"

def get_report_info_list(user_id, keyword, request_num=20, position_str=None):
    url = "https://ics.xyzq.cn/icsapp/ai/skill/report/infoList"
    
    params = {
        "opStation": "skillPowser",
        "userId": user_id,
        "keyword": keyword,
        "requestNum": max(1, min(request_num, 20))
    }
    
    if position_str:
        params["positionStr"] = position_str
    
    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        result = response.json()
        
        resp_head = result.get("respHead", {})
        resp_code = resp_head.get("respCode", -1)
        
        if str(resp_code) != "0":
            resp_msg = resp_head.get("respMsg", "请求失败")
            return None, None, resp_msg
        
        resp_body = result.get("respBody", {})
        report_info_list = resp_body.get("reportInfoVOList", [])
        position_str = resp_body.get("positionStr", "")
        
        return report_info_list, position_str, None
    
    except requests.exceptions.Timeout:
        return None, None, "请求超时"
    except requests.exceptions.RequestException as e:
        return None, None, f"网络请求失败: {str(e)}"
    except json.JSONDecodeError:
        return None, None, "数据解析失败"
    except Exception as e:
        return None, None, f"未知错误: {str(e)}"

def format_release_time(timestamp):
    try:
        if isinstance(timestamp, int):
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000))
        elif isinstance(timestamp, str):
            if timestamp.isdigit():
                return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(timestamp) / 1000))
            return timestamp
        return str(timestamp)
    except Exception:
        return str(timestamp)

def save_to_output(report_info_list, position_str):
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    output_data = {
        "reportInfoVOList": report_info_list,
        "positionStr": position_str,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    output_path = os.path.join(output_dir, "reportSearchInfos.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    return output_path

def format_markdown(report_info_list):
    markdown_lines = []
    
    for idx, report in enumerate(report_info_list, 1):
        title = report.get("title", "")
        author = report.get("author", "")
        research_team = report.get("researchTeam", "")
        report_summary = report.get("reportSummary", "")
        prn_rpt_type_name = report.get("prnRptTypeName", "")
        sub_rpt_type_name = report.get("subRptTypeName", "")
        release_time = format_release_time(report.get("releaseTime", ""))
        
        markdown_lines.append(f"## {idx}. {title}")
        markdown_lines.append("")
        markdown_lines.append(f"- **作者**: {author}")
        markdown_lines.append(f"- **研究团队**: {research_team}")
        markdown_lines.append(f"- **报告类型**: {prn_rpt_type_name} / {sub_rpt_type_name}")
        markdown_lines.append(f"- **发布时间**: {release_time}")
        markdown_lines.append(f"- **研报摘要**: {report_summary}")
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")
    
    return "\n".join(markdown_lines)

def main():
    zd_apikey = os.environ.get("XYZD_APIKEY")
    if not zd_apikey:
        print("错误：环境变量XYZD_APIKEY未设置")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("用法：python report_info_list.py <查询关键词> [下一页] [数量]")
        sys.exit(1)
    
    user_input = sys.argv[1]
    is_next_page = False
    request_num = 20
    
    if len(sys.argv) > 2:
        if sys.argv[2] == "下一页":
            is_next_page = True
            if len(sys.argv) > 3:
                try:
                    request_num = int(sys.argv[3])
                except ValueError:
                    pass
        else:
            try:
                request_num = int(sys.argv[2])
            except ValueError:
                pass
    
    request_num = max(1, min(request_num, 20))
    
    valid, error = validate_keyword(user_input)
    if not valid:
        print(f"错误：{error}")
        sys.exit(1)
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    position_str = None
    
    if is_next_page:
        output_path = os.path.join(output_dir, "reportSearchInfos.json")
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    position_str = data.get("positionStr", "")
                except json.JSONDecodeError:
                    pass
    
    user_id, error = get_user_info(zd_apikey)
    if error:
        print(f"获取用户信息失败: {error}")
        sys.exit(1)
    
    report_info_list, position_str_result, error = get_report_info_list(user_id, user_input, request_num, position_str)
    if error:
        print(f"查询研报失败: {error}")
        sys.exit(1)
    
    save_to_output(report_info_list, position_str_result)
    
    markdown_result = format_markdown(report_info_list)
    print(markdown_result)

if __name__ == "__main__":
    main()