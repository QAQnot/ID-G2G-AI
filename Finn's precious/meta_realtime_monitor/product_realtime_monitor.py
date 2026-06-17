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

# ========== 投放调控阈值（用户可自行修改） ==========
ROI_WARN_THRESHOLD = 1.0     # ROI 低于此值 → ❌ 预警
ROI_GOOD_THRESHOLD = 2.0     # ROI 高于此值 → ✅ 正常
CTR_WARN_THRESHOLD = 1.0     # CTR(%) 低于此值 → 素材需优化
ADD_TO_CART_ROI_WARN = 0.5   # 加购ROI 低于此值 → ❌ 预警
ADD_TO_CART_ROI_GOOD = 1.0   # 加购ROI 高于此值 → ✅ 正常
HIGH_SPEND_THRESHOLD = 500   # 花费超过此值且 ROI<1 → 立即预警

# 广告分类
HARVEST_BUYERS = {'JH', 'WL', 'ZY'}   # 收割广告
COLLAB_BUYERS  = {'KQ', 'WK', 'JM'}   # 合创广告

# ================= 核心函数 =================

def get_segment_value(segment_list, action_type):
    """提取 catalog_segment 中的数值（兼容 actions/action_values）"""
    if not segment_list:
        return 0
    for segment in segment_list:
        if segment.get('action_type') == action_type:
            val = segment.get('value', 0)
            return float(val) if '.' in str(val) else int(val)
    return 0


def extract_media_buyer(campaign_name):
    """从 campaign_name 中提取投放人名称"""
    if not campaign_name:
        return '未知'

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


def extract_product_name(ad_name):
    """从广告名第一个 '_' 之前提取产品名称"""
    if not ad_name:
        return '未知产品'
    # 取第一个 '_' 之前的部分作为产品名
    product = ad_name.split('_')[0].strip()
    return product if product else '未知产品'


def get_status(spend, roi, ctr, add_to_cart_roi):
    """
    根据阈值返回状态标记
    返回: (状态图标, 建议文字)
    """
    warnings = []

    # 高花费低产出
    if spend >= HIGH_SPEND_THRESHOLD and roi < ROI_WARN_THRESHOLD:
        return '❌', '高花费无转化，建议关停'
    if spend >= HIGH_SPEND_THRESHOLD and roi < ROI_GOOD_THRESHOLD:
        warnings.append('花费偏高')

    # ROI 判断
    if roi < ROI_WARN_THRESHOLD:
        return '❌', 'ROI过低，建议关停或大幅降价'
    elif roi < ROI_GOOD_THRESHOLD:
        warnings.append('ROI偏低')

    # CTR 判断
    if ctr < CTR_WARN_THRESHOLD:
        warnings.append('CTR偏低，需优化素材')

    # 加购ROI 判断
    if add_to_cart_roi < ADD_TO_CART_ROI_WARN:
        warnings.append('加购ROI低')

    if warnings:
        return '⚠️', '；'.join(warnings)

    return '✅', '表现良好，可考虑加量'


def fetch_today_data():
    """抓取今日实时数据（ad 级别）"""
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 按 (投放人, 产品名称) 聚合数据
    product_data = defaultdict(lambda: {
        'spend': 0.0,
        'gmv': 0.0,
        'purchases': 0,
        'add_to_cart_value': 0.0,
        'add_to_cart_count': 0,
        'impressions': 0,
        'clicks': 0,
    })

    print(f"📊 正在抓取 {today} 的实时数据（ad 级别）...")
    print(f"⏰ 拉取时间: {current_time}\n")

    total_ads = 0
    error_accounts = []

    for account_id in ad_accounts:
        url = f"https://graph.facebook.com/{API_VERSION}/{account_id}/insights"
        fields = (
            "ad_name,campaign_name,spend,"
            "catalog_segment_actions,catalog_segment_value,"
            "impressions,clicks,ctr,"
            "actions,action_values"
        )

        params = {
            'access_token': ACCESS_TOKEN,
            'level': 'ad',
            'fields': fields,
            'time_range': f"{{'since':'{today}','until':'{today}'}}",
            'limit': 1000
        }

        try:
            session = requests.Session()
            while url:
                resp = session.get(url, params=params, timeout=35).json()

                if 'error' in resp:
                    err_msg = resp['error'].get('message', '未知错误')
                    print(f"⚠️ {account_id} 返回错误: {err_msg}")
                    error_accounts.append(account_id)
                    break

                for item in resp.get('data', []):
                    total_ads += 1

                    # --- 提取基础信息 ---
                    ad_name = item.get('ad_name', '')
                    campaign_name = item.get('campaign_name', '')

                    media_buyer = extract_media_buyer(campaign_name)
                    product_name = extract_product_name(ad_name)

                    # --- 提取指标 ---
                    spend = float(item.get('spend', 0))

                    # 优先用 catalog_segment，fallback 到 actions
                    catalog_actions = item.get('catalog_segment_actions', [])
                    catalog_values = item.get('catalog_segment_value', [])
                    actions = item.get('actions', [])
                    action_values = item.get('action_values', [])

                    # 购买数 & GMV
                    purchases = int(
                        get_segment_value(catalog_actions, 'purchase') or
                        get_segment_value(actions, 'purchase')
                    )
                    gmv = float(
                        get_segment_value(catalog_values, 'purchase') or
                        get_segment_value(action_values, 'purchase')
                    )

                    # 加购数 & 加购价值
                    add_to_cart_count = int(
                        get_segment_value(catalog_actions, 'add_to_cart') or
                        get_segment_value(actions, 'add_to_cart')
                    )
                    add_to_cart_value = float(
                        get_segment_value(catalog_values, 'add_to_cart') or
                        get_segment_value(action_values, 'add_to_cart')
                    )

                    # 曝光 / 点击 / CTR
                    impressions = int(item.get('impressions', 0))
                    clicks = int(item.get('clicks', 0))
                    ctr_raw = float(item.get('ctr', 0))  # Facebook 返回的 CTR

                    # --- 聚合 ---
                    key = (media_buyer, product_name)
                    product_data[key]['spend'] += spend
                    product_data[key]['gmv'] += gmv
                    product_data[key]['purchases'] += purchases
                    product_data[key]['add_to_cart_value'] += add_to_cart_value
                    product_data[key]['add_to_cart_count'] += add_to_cart_count
                    product_data[key]['impressions'] += impressions
                    product_data[key]['clicks'] += clicks

                url = resp.get('paging', {}).get('next')
                params = {}

        except Exception as e:
            print(f"⚠️ {account_id} 抓取异常: {e}")
            error_accounts.append(account_id)
            continue

    print(f"✅ 共抓取 {total_ads} 条广告数据")
    if error_accounts:
        print(f"⚠️ {len(error_accounts)} 个账户异常: {', '.join(error_accounts[:5])}...")
    print()

    return product_data


def cjk_pad(text, width, align='left'):
    """中英文混排字符串填充（中文占2个字符宽度）"""
    text = str(text)
    # 计算显示宽度：中文字符和全角符号算2，其余算1
    disp = 0
    for ch in text:
        if '一' <= ch <= '鿿' or '　' <= ch <= '〿' or '＀' <= ch <= '￯':
            disp += 2
        else:
            disp += 1
    padding = max(0, width - disp)
    if align == 'left':
        return text + ' ' * padding
    elif align == 'right':
        return ' ' * padding + text
    else:  # center
        left = padding // 2
        right = padding - left
        return ' ' * left + text + ' ' * right


def compute_ctr(impressions, clicks):
    """计算 CTR(%) = clicks / impressions * 100"""
    if impressions > 0:
        return clicks / impressions * 100
    return 0.0


def display_results(product_data):
    """控制台格式化输出 — 按投手单独呈现"""
    if not product_data:
        print("❌ 未获取到任何数据")
        return

    # 按投放人分组产品
    buyer_rows = defaultdict(list)
    for (buyer, product), data in product_data.items():
        spend = data['spend']
        gmv = data['gmv']
        purchases = data['purchases']
        add_to_cart_value = data['add_to_cart_value']
        add_to_cart_count = data['add_to_cart_count']
        impressions = data['impressions']
        clicks = data['clicks']

        roi = gmv / spend if spend > 0 else 0.0
        add_to_cart_roi = add_to_cart_value / spend if spend > 0 else 0.0
        ctr = compute_ctr(impressions, clicks)

        row = {
            'buyer': buyer,
            'product': product,
            'spend': spend,
            'gmv': gmv,
            'roi': roi,
            'purchases': purchases,
            'add_to_cart_value': add_to_cart_value,
            'add_to_cart_roi': add_to_cart_roi,
            'add_to_cart_count': add_to_cart_count,
            'ctr': ctr,
        }
        buyer_rows[buyer].append(row)

    # 各投手内按花费降序
    for buyer in buyer_rows:
        buyer_rows[buyer].sort(key=lambda r: r['spend'], reverse=True)

    # 定义投手展示顺序：先收割组后合创组
    buyer_order = []
    # 收割组
    for b in ['JH', 'WL']:
        if b in buyer_rows:
            buyer_order.append(b)
    # 合创组
    for b in ['EZ', 'WK', 'JM']:
        if b in buyer_rows:
            buyer_order.append(b)
    # 其他
    for b in sorted(buyer_rows.keys()):
        if b not in buyer_order:
            buyer_order.append(b)

    # ============ 列宽配置 ============
    #  投放人   产品名称          花费        GMV      ROI     订单    加购ROI      CTR
    COL_W = {
        'buyer':      8,   # 左对齐
        'product':   24,   # 左对齐
        'spend':     13,   # 右对齐
        'gmv':       13,   # 右对齐
        'roi':        8,   # 右对齐
        'purchases':  7,   # 右对齐
        'atc_roi':    9,   # 右对齐
        'ctr':        7,   # 右对齐
    }

    def col(text, key):
        """按列宽对齐，数字右对齐，文本左对齐"""
        if key in ('spend', 'gmv', 'roi', 'purchases', 'atc_roi', 'ctr'):
            return cjk_pad(text, COL_W[key], align='right')
        return cjk_pad(text, COL_W[key], align='left')

    TOTAL_W = sum(COL_W.values()) + 7  # 列间距共7个空格
    SEP = '─' * TOTAL_W

    HEADER = (
        f"{col('投放人', 'buyer')} {col('产品名称', 'product')} "
        f"{col('花费(USD)', 'spend')} {col('GMV(USD)', 'gmv')} "
        f"{col('ROI', 'roi')} {col('订单', 'purchases')} "
        f"{col('加购ROI', 'atc_roi')} {col('CTR', 'ctr')}"
    )

    # ==================== 打印 ====================

    grand_spend = 0.0
    grand_gmv = 0.0
    grand_purchases = 0
    grand_add_to_cart_value = 0.0

    for buyer in buyer_order:
        rows = buyer_rows[buyer]
        # 投放人类别标签
        if buyer in HARVEST_BUYERS:
            tag = '🔴 收割'
        elif buyer in COLLAB_BUYERS:
            tag = '🟢 合创'
        else:
            tag = '⚪ 其他'

        print(f"\n{'=' * TOTAL_W}")
        print(f"  {tag} | 投放人: {buyer}  |  产品数: {len(rows)}")
        print(f"{'=' * TOTAL_W}")
        print(HEADER)
        print(SEP)

        buyer_spend = 0.0
        buyer_gmv = 0.0
        buyer_purchases = 0
        buyer_atc_value = 0.0

        for r in rows:
            print(
                f"{col(r['buyer'], 'buyer')} {col(r['product'], 'product')} "
                f"{col(format(r['spend'], ',.2f'), 'spend')} {col(format(r['gmv'], ',.2f'), 'gmv')} "
                f"{col(format(r['roi'], '.2f'), 'roi')} {col(str(r['purchases']), 'purchases')} "
                f"{col(format(r['add_to_cart_roi'], '.2f'), 'atc_roi')} {col(format(r['ctr'], '.2f') + '%', 'ctr')}"
            )
            buyer_spend += r['spend']
            buyer_gmv += r['gmv']
            buyer_purchases += r['purchases']
            buyer_atc_value += r['add_to_cart_value']

        # 投手小计
        buyer_roi = buyer_gmv / buyer_spend if buyer_spend > 0 else 0
        buyer_atc_roi = buyer_atc_value / buyer_spend if buyer_spend > 0 else 0

        print(SEP)
        print(
            f"{col('小计', 'buyer')} {col('', 'product')} "
            f"{col(format(buyer_spend, ',.2f'), 'spend')} {col(format(buyer_gmv, ',.2f'), 'gmv')} "
            f"{col(format(buyer_roi, '.2f'), 'roi')} {col(str(buyer_purchases), 'purchases')} "
            f"{col(format(buyer_atc_roi, '.2f'), 'atc_roi')}"
        )

        grand_spend += buyer_spend
        grand_gmv += buyer_gmv
        grand_purchases += buyer_purchases
        grand_add_to_cart_value += buyer_atc_value

    # ============ 总计 ============
    grand_roi = grand_gmv / grand_spend if grand_spend > 0 else 0
    grand_atc_roi = grand_add_to_cart_value / grand_spend if grand_spend > 0 else 0

    print(f"\n{'=' * TOTAL_W}")
    print(f"  📊 总计")
    print(f"{'=' * TOTAL_W}")
    print(
        f"{col('总计', 'buyer')} {col('', 'product')} "
        f"{col(format(grand_spend, ',.2f'), 'spend')} {col(format(grand_gmv, ',.2f'), 'gmv')} "
        f"{col(format(grand_roi, '.2f'), 'roi')} {col(str(grand_purchases), 'purchases')} "
        f"{col(format(grand_atc_roi, '.2f'), 'atc_roi')}"
    )
    print(f"{'=' * TOTAL_W}")


# ================= 主程序 =================

if __name__ == "__main__":
    print("🚀 投放人×产品 实时数据监控")
    print(f"📅 日期: {datetime.now().strftime('%Y-%m-%d')}")
    print()

    product_data = fetch_today_data()
    display_results(product_data)

    print(f"\n✅ 监控完成！")
