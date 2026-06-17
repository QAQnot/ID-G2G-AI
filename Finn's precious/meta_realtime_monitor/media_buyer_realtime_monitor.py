import requests
import sys
import io
from datetime import datetime
from collections import defaultdict

# Windows UTF-8 输出支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ================= 配置区 =================
ACCESS_TOKEN = 'EAAMyoqUZCW58BQIQeIQipUBwJdxEgRW7bZBZCDb9pycsRqav1wXCcZBfeeLIkUtsr3OYio3x0MDpsqUV3FYoZBi2yy0E3EbWY0hyy8yzNZBWmTAihZBy3KlIGNzOkLkRr3hSxDPe2Q0ZCXAddtAM14BH5uIKaa7E1PfZCipwt70vYwJw7ujymIMX3OjbzPLgAGIYh7wZDZD'
API_VERSION = 'v19.0'

ad_accounts = [
    'act_733057369672818', 'act_613926504488588', 'act_1436423430906009', 'act_756033960164076',
    'act_1766235208109261', 'act_1305975370939999', 'act_1539370044177570', 'act_1415034946381721',
    'act_718815157674879', 'act_1633637413995173', 'act_1188102472395974', 'act_575795291631880',
    'act_688667850516107', 'act_1353114332579095', 'act_1252046832802169', 'act_1106776514703119',
    'act_719777080950105', 'act_566681705977864', 'act_8242472565853392', 'act_2454902224902765',
]

# ================= 核心函数 =================

def get_segment_value(segment_list, action_type):
    """提取 catalog_segment 中的数值"""
    if not segment_list:
        return 0
    for segment in segment_list:
        if segment.get('action_type') == action_type:
            val = segment.get('value', 0)
            return float(val) if '.' in str(val) else int(val)
    return 0

def extract_media_buyer(campaign_name):
    """从 campaign_name 中提取投放人名称
    规则：按优先级匹配特定代码
    WK -> WK
    ZXS -> WL
    WL -> WL
    LLY -> JH
    LZY -> ZY
    JM -> JM
    CJH -> JH
    LKQ -> KQ
    ZQ -> ZQ
    """
    if not campaign_name:
        return '未知'

    # 按优先级顺序匹配
    if 'WK' in campaign_name:
        return 'WK'
    elif 'EZ' in campaign_name:
        return 'EZ'
    elif 'WL' in campaign_name:
        return 'WL'
    elif 'LLY' in campaign_name:
        return 'JH'
    elif 'LZY' in campaign_name:
        return 'ZY'
    elif 'JM' in campaign_name:
        return 'JM'
    elif 'CJH' in campaign_name:
        return 'JH'
    elif 'LKQ' in campaign_name:
        return 'KQ'
    elif 'ZQ' in campaign_name:
        return 'ZQ'
    else:
        return '未知'

def fetch_today_data():
    """抓取今日实时数据"""
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 按投放人聚合数据
    buyer_data = defaultdict(lambda: {'spend': 0.0, 'gmv': 0.0, 'purchases': 0})

    print(f"📊 正在抓取 {today} 的实时数据...")
    print(f"⏰ 拉取时间: {current_time}\n")

    for account_id in ad_accounts:
        url = f"https://graph.facebook.com/{API_VERSION}/{account_id}/insights"
        fields = "campaign_name,spend,catalog_segment_actions,catalog_segment_value"

        params = {
            'access_token': ACCESS_TOKEN,
            'level': 'campaign',
            'fields': fields,
            'time_range': f"{{'since':'{today}','until':'{today}'}}",
            'limit': 1000
        }

        try:
            session = requests.Session()
            while url:
                resp = session.get(url, params=params, timeout=35).json()

                if 'error' in resp:
                    print(f"⚠️ {account_id} 返回错误: {resp['error'].get('message', '未知错误')}")
                    break

                for item in resp.get('data', []):
                    campaign_name = item.get('campaign_name', '')
                    media_buyer = extract_media_buyer(campaign_name)

                    spend = float(item.get('spend', 0))
                    purchases = int(get_segment_value(item.get('catalog_segment_actions', []), 'purchase'))
                    purchase_value = float(get_segment_value(item.get('catalog_segment_value', []), 'purchase'))

                    buyer_data[media_buyer]['spend'] += spend
                    buyer_data[media_buyer]['gmv'] += purchase_value
                    buyer_data[media_buyer]['purchases'] += purchases

                url = resp.get('paging', {}).get('next')
                params = {}

        except Exception as e:
            print(f"⚠️ {account_id} 抓取异常: {e}")
            continue

    return buyer_data

def display_results(buyer_data):
    """在控制台中格式化显示结果"""
    if not buyer_data:
        print("❌ 未获取到任何数据")
        return

    # 定义分组
    harvest_group = {'WL',  'JH'}  # 收割组
    seeding_group = {'WK', 'JM', 'EZ'}  # 种草组

    # 分组数据
    harvest_buyers = {k: v for k, v in buyer_data.items() if k in harvest_group}
    seeding_buyers = {k: v for k, v in buyer_data.items() if k in seeding_group}

    # 按花费降序排序
    sorted_harvest = sorted(harvest_buyers.items(), key=lambda x: x[1]['spend'], reverse=True)
    sorted_seeding = sorted(seeding_buyers.items(), key=lambda x: x[1]['spend'], reverse=True)

    # 计算分组小计
    harvest_spend = sum(data['spend'] for data in harvest_buyers.values())
    harvest_gmv = sum(data['gmv'] for data in harvest_buyers.values())
    harvest_purchases = sum(data['purchases'] for data in harvest_buyers.values())
    harvest_roi = harvest_gmv / harvest_spend if harvest_spend > 0 else 0

    seeding_spend = sum(data['spend'] for data in seeding_buyers.values())
    seeding_gmv = sum(data['gmv'] for data in seeding_buyers.values())
    seeding_purchases = sum(data['purchases'] for data in seeding_buyers.values())
    seeding_roi = seeding_gmv / seeding_spend if seeding_spend > 0 else 0

    # 计算总计
    total_spend = harvest_spend + seeding_spend
    total_gmv = harvest_gmv + seeding_gmv
    total_purchases = harvest_purchases + seeding_purchases
    total_roi = total_gmv / total_spend if total_spend > 0 else 0

    print("=" * 100)
    print(f"{'投放人':<10} {'花费 (USD)':>15} {'GMV (USD)':>15} {'订单数':>10} {'ROI':>10}")
    print("=" * 100)

    # 显示收割组
    for buyer, data in sorted_harvest:
        spend = data['spend']
        gmv = data['gmv']
        purchases = data['purchases']
        roi = gmv / spend if spend > 0 else 0
        print(f"{buyer:<10} {spend:>15,.2f} {gmv:>15,.2f} {purchases:>10} {roi:>10.2f}")

    # 收割组小计
    if harvest_buyers:
        print(f"{'收割组小计':<10} {harvest_spend:>15,.2f} {harvest_gmv:>15,.2f} {harvest_purchases:>10} {harvest_roi:>10.2f}")
        print("-" * 100)

    # 显示种草组
    for buyer, data in sorted_seeding:
        spend = data['spend']
        gmv = data['gmv']
        purchases = data['purchases']
        roi = gmv / spend if spend > 0 else 0
        print(f"{buyer:<10} {spend:>15,.2f} {gmv:>15,.2f} {purchases:>10} {roi:>10.2f}")

    # 种草组小计
    if seeding_buyers:
        print(f"{'种草组小计':<10} {seeding_spend:>15,.2f} {seeding_gmv:>15,.2f} {seeding_purchases:>10} {seeding_roi:>10.2f}")
        print("-" * 100)

    # 总计
    print(f"{'总计':<10} {total_spend:>15,.2f} {total_gmv:>15,.2f} {total_purchases:>10} {total_roi:>10.2f}")
    print("=" * 100)

# ================= 主程序 =================

if __name__ == "__main__":
    print("🚀 投放人实时数据监控\n")

    buyer_data = fetch_today_data()
    display_results(buyer_data)

    print(f"\n✅ 监控完成！")
