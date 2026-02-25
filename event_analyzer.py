import win32evtlog
import ctypes
import argparse
import json
import sys
import os
import subprocess
from datetime import datetime
from collections import Counter
import xml.etree.ElementTree as ET

LEVEL_MAP = {
    0: "LogAlways",
    1: "Critical",
    2: "Error",
    3: "Warning",
    4: "Info",
    5: "Verbose"
}

XML_NS = {"ns": "http://schemas.microsoft.com/win/2004/08/events/event"}

provider_meta_cache = {}
VERBOSE = False


# ===============================
# 终端输出同时写入文件
# ===============================
class TeeStdout:
    def __init__(self, filename, encoding="utf-8"):
        self.terminal = sys.stdout
        self.file = open(filename, "w", encoding=encoding)

    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)

    def flush(self):
        self.terminal.flush()
        self.file.flush()

    def close(self):
        self.file.close()


def debug(msg):
    if VERBOSE:
        print(f"[DEBUG] {msg}")


# ===============================
# 执行系统命令并返回输出
# ===============================
def run_command(cmd):
    try:
        result = subprocess.check_output(
            cmd,
            shell=True,
            encoding="gbk",  # Windows 中文系统避免乱码
            errors="ignore"
        )
        return result
    except Exception as e:
        return f"[命令执行失败] {cmd} | {e}\n"


def get_publisher_meta(provider_name):
    if provider_name in provider_meta_cache:
        return provider_meta_cache[provider_name]

    try:
        meta = win32evtlog.EvtOpenPublisherMetadata(provider_name)
        provider_meta_cache[provider_name] = meta
        return meta
    except Exception as e:
        debug(f"打开 PublisherMetadata 失败: {provider_name} | {e}")
        return None


def parse_event_xml(xml_string):
    try:
        root = ET.fromstring(xml_string)
        system = root.find("ns:System", XML_NS)

        event_id = int(system.find("ns:EventID", XML_NS).text)
        level = int(system.find("ns:Level", XML_NS).text)
        provider = system.find("ns:Provider", XML_NS).attrib.get("Name")
        time_str = system.find("ns:TimeCreated", XML_NS).attrib.get("SystemTime")

        event_time = datetime.fromisoformat(
            time_str.replace("Z", "+00:00")
        ).astimezone()

        return {
            "时间": event_time.isoformat(),
            "级别": LEVEL_MAP.get(level, f"Level{level}"),
            "来源": provider,
            "事件ID": event_id,
            "原始级别": level,
            "消息": "",
            "_provider": provider
        }

    except Exception as e:
        debug(f"XML 解析失败: {e}")
        return None


def format_event_message(provider_name, event_handle):
    try:
        meta = get_publisher_meta(provider_name)
        if not meta:
            return "[无发布者元数据]"

        message = win32evtlog.EvtFormatMessage(
            meta,
            event_handle,
            win32evtlog.EvtFormatMessageEvent
        )
        return message.strip()

    except Exception as e:
        debug(f"消息格式化失败: {provider_name} | {e}")
        return "[无法格式化消息]"


def get_recent_events(log_type="System", hours=1, max_events=100000):
    milliseconds = hours * 60 * 60 * 1000

    query = f"""
    *[System[TimeCreated[timediff(@SystemTime) <= {milliseconds}]]]
    """

    print(f"[*] 读取 {log_type} 最近{hours}小时日志...")

    flags = win32evtlog.EvtQueryReverseDirection
    events = []

    try:
        query_handle = win32evtlog.EvtQuery(log_type, flags, query)

        while True:
            try:
                event_handles = win32evtlog.EvtNext(query_handle, 50)
            except Exception:
                break

            if not event_handles:
                break

            for event_handle in event_handles:
                if len(events) >= max_events:
                    print(f"[!] 达到事件上限 {max_events}，截断")
                    return events

                try:
                    xml = win32evtlog.EvtRender(
                        event_handle,
                        win32evtlog.EvtRenderEventXml
                    )

                    event_data = parse_event_xml(xml)
                    if not event_data:
                        continue

                    if event_data["级别"] in ("Error", "Critical"):
                        event_data["消息"] = format_event_message(
                            event_data["_provider"],
                            event_handle
                        )

                    del event_data["_provider"]
                    events.append(event_data)

                except Exception as e:
                    debug(f"单条事件处理失败: {e}")
                    continue

    except Exception as e:
        print(f"[!] 查询失败: {e}")

    return events


def analyze_recent(hours=1, log_types=None, max_events=100000):
    if log_types is None:
        log_types = ["System", "Application"]

    all_events = []

    for log_type in log_types:
        events = get_recent_events(log_type, hours, max_events)
        all_events.extend(events)

    if not all_events:
        print(f"[!] 最近{hours}小时暂无事件或权限不足")
        return

    print("\n" + "=" * 60)
    print(f"最近{hours}小时事件统计（共 {len(all_events)} 条）")
    print("=" * 60)

    level_counter = Counter(event['级别'] for event in all_events)
    print("\n[级别分布]")
    for level, count in level_counter.items():
        print(f"{level}: {count}")

    print("\n[Top 10 事件来源]")
    source_counter = Counter(event['来源'] for event in all_events)
    for source, count in source_counter.most_common(10):
        print(f"{source}: {count}")

    print("\n[Top 10 EventID]")
    eventid_counter = Counter(event['事件ID'] for event in all_events)
    for eid, count in eventid_counter.most_common(10):
        print(f"{eid}: {count}")

    print(f"\n[Error 详细列表]")
    errors = [e for e in all_events if e['级别'] in ("Error", "Critical")]

    if errors:
        for event in errors:
            msg_short = event['消息'][:80] + ('...' if len(event['消息']) > 80 else '')
            print(f"{event['时间']} | {event['来源']} | EventID:{event['事件ID']} | {msg_short}")
    else:
        print("无 Error")

    filename = f"event_report_last{hours}h_{datetime.now().strftime('%H%M%S')}.jsonl"

    with open(filename, 'w', encoding='utf-8') as f:
        for event in all_events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

    print(f"\n[+] 报告已保存: {filename}")


def main():
    global VERBOSE

    run_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 启用终端输出双写
    console_file = f"console_output_{run_time}.log"
    tee = TeeStdout(console_file)
    sys.stdout = tee

    print(f"[+] 控制台输出记录文件: {console_file}")

    # ===============================
    # 采集 systeminfo + GPU 信息
    # ===============================
    sysinfo_file = f"system_info_{run_time}.txt"
    print("[+] 正在采集系统详细信息...")

    systeminfo_output = run_command("systeminfo")
    gpu_output = run_command("wmic path win32_VideoController get name, adapterram, driverversion")

    with open(sysinfo_file, "w", encoding="utf-8") as f:
        f.write("===== systeminfo 输出 =====\n\n")
        f.write(systeminfo_output)
        f.write("\n\n===== GPU 信息 =====\n\n")
        f.write(gpu_output)

    print(f"[+] 系统信息已保存: {sysinfo_file}")

    parser = argparse.ArgumentParser(
        description="Windows 日志分析工具（工程增强版）"
    )

    parser.add_argument("-t", "--hours", type=int, default=1)
    parser.add_argument("-l", "--logs", action="append",
                        choices=['System', 'Application', 'Security', 'Setup', 'ForwardedEvents'])
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--max", type=int, default=100000)

    args = parser.parse_args()

    VERBOSE = args.verbose
    log_types = args.logs if args.logs else ["System", "Application"]

    analyze_recent(hours=args.hours, log_types=log_types, max_events=args.max)

    print("\n程序执行完毕")

    sys.stdout = tee.terminal
    tee.close()


if __name__ == "__main__":
    main()
    input("\n按回车键退出...")