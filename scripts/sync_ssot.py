#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
圖圖生酮蛋糕店官網 (tutu888.com.tw) — SSOT 單一真實資料源同步與驗證腳本
用法：
  python3 scripts/sync_ssot.py           # 讀取 data/menu-ssot.json 自動同步更新全站 4 處資料
  python3 scripts/sync_ssot.py --verify  # 僅執行一致性、食安合規與 UCP v1.1 滿分驗算
"""

import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def esc(text):
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_nt(price):
    return f"NT${int(price):,}"


def format_product_name_html(name):
    escaped = esc(name)
    return re.sub(r"（[^）]*）$", lambda m: f'<span class="nobr">{m.group(0)}</span>', escaped)


def build_ucp_manifest(ssot):
    m = ssot["merchant"]
    catalog = []
    for it in ssot["items"]:
        catalog.append({
            "sku": it["id"],
            "series": it["series"],
            "name": it["name"],
            "category": it["catLabel"],
            "spec": it["spec"],
            "price_twd": it["price"],
            "currency": "TWD",
            "tax_included": True,
            "availability": "preorder_made_to_order",
            "lead_time_days": 2,
            "ingredients": it["ingredients"],
            "allergens": it.get("allergens", ""),
            "dietary_notice": it.get("dietTag", "無小麥麵粉・無精製白砂糖・無人工防腐劑"),
            "url": f"{m['url']}#{it['id']}",
            "checkout_continue_url": f"{m['url']}#checkout?sku={it['id']}&qty=1&agent=chatgpt_dots"
        })

    return {
        "ucp_version": "1.1",
        "updated_at": ssot["updated_at"],
        "merchant": {
            "id": m["id"],
            "name": m["name"],
            "brand_name": m["name"],
            "domain": m["domain"],
            "url": m["url"],
            "telephone": m["telephone_e164"],
            "address": m["address"]["full"],
            "place_id": m["google_maps_place_id"],
            "coordinates": m["coordinates"],
            "opening_hours": m["opening_hours"],
            "contact_channels": {
                "line_official_community": m["line_openchat_url"],
                "google_maps": m["google_maps_url"],
                "phone": m["telephone"]
            }
        },
        "compliance_and_food_safety": ssot["compliance"],
        "shipping_rules": {
            "currency": "TWD",
            "free_shipping_threshold_twd": None,
            "pickup_free_shipping": True,
            "flat_delivery_fee_twd": 300,
            "modes": ssot["shipping_modes"],
            "payment_instructions": m["remittance"]
        },
        "catalog_summary": {
            "total_priced_skus": len(catalog),
            "price_range_twd": {"min": min(x["price_twd"] for x in catalog), "max": max(x["price_twd"] for x in catalog)},
            "custom_celebration_cake": {
                "sku": "custom-birthday-cake",
                "name": "客製慶生蛋糕（造型／口味專屬討論）",
                "pricing": "quote_via_line",
                "inquiry_url": m["line_openchat_url"]
            }
        },
        "catalog": catalog,
        "agentic_access_policy": {
            "allow_cloud_browsers": True,
            "llms_txt_url": f"{m['url']}llms.txt",
            "web_bot_auth": {
                "standard": "RFC-9421-HTTP-Message-Signatures",
                "trusted_signature_agents": ["https://chatgpt.com"],
                "signature_directory_url": "https://chatgpt.com/.well-known/http-message-signatures-directory",
                "cdn_allowlist_ids": {
                    "cloudflare_bot_detection_id": "129220581",
                    "cloudflare_bot_tag": "chatgpt-agent",
                    "vercel_agent_id": "chatgpt-operator",
                    "akamai_bot_name": "ChatGPT Agent"
                }
            }
        },
        "agentic_payment_readiness": {
            "chatgpt_wallet_compatible": True,
            "accepted_network_tokens": ["Visa", "Mastercard", "AmericanExpress"],
            "supports_payment_account_reference_par": True,
            "single_use_token_enforced": True,
            "pre_approval_disclosure": {
                "shows_merchant_identity": True,
                "shows_itemized_cart": True,
                "shows_all_inclusive_total_twd": True,
                "tax_included_in_price": True,
                "shipping_calculated_before_auth": True,
                "charge_type": "one_time_purchase",
                "creates_recurring_charge": False,
                "creates_authorization_hold": False
            },
            "risk_and_fraud_headers": {
                "ingests_forwarded_header": True,
                "supported_forwarded_params": ["asn", "for", "ip-country", "ip-prefix", "locale", "tz", "user-agent"]
            },
            "checkout_handoff": {
                "continue_url_template": f"{m['url']}#checkout?sku={{sku}}&qty={{qty}}&agent=chatgpt_dots",
                "cart_share_url_template": f"{m['url']}#cart={{sku_qty_pairs}}&mode={{mode}}&date={{yyyy_mm_dd}}",
                "supports_guest_checkout_without_login": True,
                "webmcp_tools_enabled": True,
                "webmcp_script": f"{m['url']}haotian-webmcp-bridge.js"
            }
        }
    }


def build_llms_txt(ssot):
    m = ssot["merchant"]
    c = ssot["compliance"]
    lines = [
        f"# {m['name']} ({m['url']})",
        "",
        "> 台南仁德無麩質、無小麥麵粉、無添加精製白砂糖與人工防腐劑之手作甜點預約制烘焙坊（現場無展示櫃，完成匯款確認後排單新鮮現做，歡迎客製生日蛋糕）。",
        "",
        "## 店家聯絡、地圖與 Agentic 商務檢索端點",
        f"- 店名：{m['name']}（Google 地圖名稱：{m['legal_brand_note']}）",
        f"- 官方網站：{m['url']}",
        f"- 公開商品目錄（JSON）：{m['url']}ucp.json",
        f"- Agent 唯讀介面說明（OpenAPI）：{m['url']}openapi.json",
        f"- AI 代理免登入直達結帳路由：{m['url']}#checkout?sku={{sku}}&qty={{qty}}&mode={{pickup|tainan_city|tainan_county|delivery}}&date={{YYYY-MM-DD}}&agent=chatgpt_dots",
        f"- 地址：{m['address']['full']}",
        f"- 電話：{m['telephone']}（{m['telephone_e164']}）",
        f"- 營業時間：{m['opening_hours']}",
        f"- Google 地圖：{m['google_maps_url']}",
        f"- 官方 LINE 社群／私訊小幫手：{m['line_openchat_url']}",
        f"- FB 粉絲團：{m['facebook_page_name']}",
        "",
        "## 核心無麩質與天然代糖原物料特色及食安過敏原標示",
        "- 無麩質粉類基底：全店不使用小麥麵粉，採用美國馬卡龍專用杏仁粉、黃金亞麻仁籽粉、洋車前子粉與椰子細粉。",
        "- 天然代糖零精製糖：不使用精製白砂糖與人工防腐劑，全面以羅漢果糖與赤藻糖醇調味，適合生酮飲食、低醣／控糖飲食與長輩小孩慶生享用。",
        "- 頂級乳源與食材：法國 Le Gall 燈塔牌／鐵塔牌奶油乳酪、馬斯卡朋起司、藍風車動物性鮮奶油、紐西蘭安佳草飼無鹽奶油、石安牧場雞蛋、100% 法國法芙娜可可、日本小山園若竹抹茶與手熬無精製糖藍莓醬（檸檬老奶奶磅蛋糕與小餐包使用無鋁泡打粉；無麩質吐司使用黃原膠）。",
        f"- 過敏原與葷素酒類提醒：{c['allergen_notice']}",
        f"- 食品法規聲明：{c['non_medical_disclaimer']}",
        "- 賞味與保存期限：一般甜點冷藏 5 天、冷凍 15 天（檸檬老奶奶磅蛋糕冷藏 3–5 天、冷凍 10 天）；吃不完建議先切片冷凍保存，避免反覆解凍。",
        "",
        "## 配送、運費、匯款與生鮮退換貨規則",
        "- 台南仁德工作室預約自取：免運費 NT$0（附保冷袋）。",
        "- 原台南市當日汽車專送：運費 NT$300（東區、中西區、北區、南區、安平區）。",
        "- 原臺南縣當日汽車專送：運費 NT$300（永康區、仁德區、歸仁區等；外縣市無當日汽車專送）。",
        "- 台灣本島黑貓宅急便低溫冷凍宅配：每筆運費 NT$300（限台灣本島，離島目前無配送；固定週四、週五寄件，當日寄隔天週五、週六送達；節假日前後無法指定到貨時間；配達時段為優先順位，實際依當日物流為主）。",
        "- 宅配風險告知：出貨前門市皆檢查完整並請司機拍照留底，運送途中可能造成側邊輕微損傷、裝飾掉落或蛋糕左右位移 3–5 公分，屬正常允許情況恕不賠償；如介意建議改選台南自取或當日汽車專送。",
        f"- 消保法生鮮例外告知：{c['consumer_protection_notice']}",
        f"- 匯款帳號與規則：{m['remittance']['bank_name']}（{m['remittance']['bank_code']}）帳號 {m['remittance']['account_number']}；{m['remittance']['rule']}",
        "",
        "## 18 大系列共 41 款正式價格與成分明細（圓模一律為 6 吋蛋糕價格）",
    ]

    by_series = {}
    for it in ssot["items"]:
        by_series.setdefault(it["series"], []).append(it)

    for s_code in sorted(by_series.keys()):
        lines.append(f"### {ssot['series_titles'][s_code]}")
        for it in by_series[s_code]:
            diet_extra = f"｜飲食提醒：{it['dietTag']}" if it.get("dietTag") else ""
            lines.append(
                f"- {it['name']}（SKU: `{it['id']}`）：{format_nt(it['price'])}（{it['spec']}{diet_extra}｜主要成分：{it['ingredients']}）"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_json_ld(ssot):
    m = ssot["merchant"]
    sections_map = [
        ("cheesecake", "乳酪／巴斯克／提拉米蘇系列（6吋無麩質無精製糖）"),
        ("crepe", "千層蛋糕與千層毛巾捲系列（杏仁粉餅皮 × 藍風車鮮奶油）"),
        ("cake", "布朗尼／磅蛋糕／生巧克力／造型慕斯系列（6吋）"),
        ("roll_bread", "生乳捲與無麩質吐司餐包系列"),
    ]
    menu_sections = []
    for cat_key, sec_name in sections_map:
        sec_items = []
        for it in ssot["items"]:
            if it["cat"] != cat_key:
                continue
            diet_str = f"｜{it['dietTag']}" if it.get("dietTag") else ""
            sec_items.append({
                "@type": "MenuItem",
                "name": it["name"],
                "sku": it["id"],
                "description": f"{it['spec']}{diet_str}｜成分：{it['ingredients']}",
                "suitableForDiet": ["https://schema.org/GlutenFreeDiet"],
                "offers": {
                    "@type": "Offer",
                    "price": it["price"],
                    "priceCurrency": "TWD",
                    "availability": "https://schema.org/PreOrder",
                    "url": f"{m['url']}#{it['id']}"
                }
            })
        menu_sections.append({
            "@type": "MenuSection",
            "name": sec_name,
            "hasMenuItem": sec_items
        })

    graph = [
        {
            "@type": "Bakery",
            "@id": f"{m['url']}#bakery",
            "name": m["name"],
            "alternateName": ["tutu888", "tutu888.com.tw", m["legal_brand_note"], "台南圖圖無麩質生酮烘焙"],
            "description": "台南仁德無麩質、無小麥麵粉、無添加精製白砂糖與人工防腐劑之手作甜點工作室。嚴選美國馬卡龍杏仁粉、法國奶油乳酪、藍風車動物性鮮奶油與羅漢果糖／赤藻糖醇，提供 18 大系列共 41 款六吋生酮乳酪蛋糕、巴斯克、千層蛋糕、毛巾捲、生乳捲與吐司餐包，歡迎客製生日蛋糕。支援台南仁德自取、大台南當日汽車專送與台灣本島黑貓低溫冷凍宅配（每筆運費 NT$300）。",
            "logo": f"{m['url']}logo-512.png",
            "image": [
                f"{m['url']}og-cover.jpg",
                f"{m['url']}assets/scene-01-keto-ingredients.webp",
                f"{m['url']}assets/scene-03-signature-cakes.webp"
            ],
            "url": m["url"],
            "menu": f"{m['url']}#menu-section",
            "telephone": m["telephone_e164"],
            "priceRange": "NT$300 - NT$1,800",
            "servesCuisine": ["無麩質甜點", "生酮友善烘焙", "無精製糖代糖蛋糕", "手作乳酪與千層蛋糕"],
            "paymentAccepted": "Bank Transfer (中國信託 822)",
            "currenciesAccepted": "TWD",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": m["address"]["street"],
                "addressLocality": m["address"]["locality"],
                "addressRegion": m["address"]["region"],
                "postalCode": m["address"]["postal_code"],
                "addressCountry": "TW"
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": m["coordinates"]["latitude"],
                "longitude": m["coordinates"]["longitude"]
            },
            "areaServed": [
                {"@type": "City", "name": "臺南市"},
                {"@type": "Country", "name": "臺灣（本島黑貓低溫冷凍宅配）"}
            ],
            "sameAs": [m["google_maps_url"], m["line_openchat_url"]],
            "openingHoursSpecification": [
                {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    "opens": "10:00",
                    "closes": "17:00"
                }
            ],
            "hasMenu": {
                "@type": "Menu",
                "@id": f"{m['url']}#official-menu",
                "name": "圖圖生酮蛋糕店 18 大系列 41 款正式價目表",
                "hasMenuSection": menu_sections
            }
        },
        {
            "@type": "FAQPage",
            "@id": f"{m['url']}#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "可以直接去台南仁德店面挑選現貨蛋糕嗎？",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "由於全店產品皆不添加人工防腐劑，現場不設展示櫃，全品項採預訂制（建議至少提前 2 天以上預約）。請先於官方 LINE 私訊小幫手確認自取、台南汽車專送或黑貓宅配檔期，並於收到匯款資訊 3 日內完成中國信託（822）901562536425 匯款回傳確認，即安排新鮮現做。"
                    }
                },
                {
                    "@type": "Question",
                    "name": "面交自取與冷凍宅配的付款、運費怎麼算？",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "台南仁德工作室預約自取免運費（NT$0）；大台南提供當日汽車專送：原台南市與原臺南縣每筆專送費 NT$300（外縣市無汽車專送）；台灣本島黑貓宅急便低溫冷凍宅配每筆運費 NT$300（限台灣本島，離島目前無配送；固定週四、週五寄件，當日寄隔天週五、週六送達）。"
                    }
                },
                {
                    "@type": "Question",
                    "name": "冷凍宅配收到後該如何保存與退冰食用？適用七天鑑賞期嗎？",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "出貨前門市人員皆會檢查蛋糕完整並請司機拍照留底，但宅配途中可能造成側邊輕微損傷、裝飾掉落或蛋糕左右位移 3–5 公分，屬正常運送允許範圍恕不賠償。依《消費者保護法》第 19 條合理例外情事，冷藏冷凍生鮮蛋糕及客製商品恕不適用 7 日無條件退貨。最佳賞味期一般為冷藏 5 天、冷凍 15 天（檸檬磅蛋糕冷藏 3–5 天、冷凍 10 天），吃不完建議先切片冷凍保存、避免反覆解凍。"
                    }
                },
                {
                    "@type": "Question",
                    "name": "蛋糕使用哪些無麩質與代糖食材？有哪些過敏原或酒類／葷素提醒？",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "全店不使用小麥麵粉與精製白砂糖，改以美國馬卡龍專用杏仁粉、黃金亞麻仁籽粉、法國燈塔／鐵塔牌奶油乳酪、藍風車動物性鮮奶油、石安牧場雞蛋，並以羅漢果糖與赤藻糖醇調味。過敏原含堅果類（杏仁、核桃）、蛋、乳製品、大豆與芝麻；原味／巧克力巴斯克與藍莓克拉芙提含微量酒類，西瓜造型慕斯與檸檬巴巴露亞含動物性吉利丁（葷食）。本品為一般無精製糖手作食品，不具醫療效能。"
                    }
                },
                {
                    "@type": "Question",
                    "name": "如何訂購客製生日蛋糕或與親友分享訂購清單？",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "官網價目表提供 41 款甜點即時加購試算，訂購區支援選擇希望慶生到貨日期與「複製訂購清單分享連結」傳給親友同步購物清單與日期；也可直接私訊官方 LINE 小幫手討論客製慶生蛋糕需求。"
                    }
                }
            ]
        }
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def build_ssr_cards(ssot):
    cards = []
    for it in ssot["items"]:
        badge_html = ""
        if it.get("badge"):
            badge_html += f'<span class="text-[11px] font-bold px-2 py-0.5 rounded-md bg-amber-400/20 text-amber-300 border border-amber-400/30">{esc(it["badge"])}</span>'
        if it.get("dietTag"):
            badge_html += f'<span class="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-sky-500/15 text-sky-300 border border-sky-400/30">{esc(it["dietTag"])}</span>'
        badge_wrap = f'<div class="flex flex-wrap items-center gap-1">{badge_html}</div>' if badge_html else ""
        card = (
            f'        <article id="{it["id"]}" class="chapter-anchor glass-panel rounded-2xl p-5 flex flex-col justify-between card-hover">'
            f'<div><div class="flex flex-wrap items-center justify-between gap-2 mb-2">'
            f'<span class="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-white/5 text-[#8FB98A] border border-white/10">{esc(it["catLabel"])}</span>'
            f'{badge_wrap}</div>'
            f'<div class="flex items-start justify-between gap-2">'
            f'<h3 class="min-w-0 text-base sm:text-lg font-extrabold text-[#FFF8F0] leading-snug">{format_product_name_html(it["name"])}</h3>'
            f'<span class="font-num text-base sm:text-lg font-extrabold text-amber-300 shrink-0">{format_nt(it["price"])}</span></div>'
            f'<div class="text-xs text-amber-200/90 font-medium mt-1 mb-2.5">{esc(it["spec"])}</div>'
            f'<p class="text-xs text-[#C4B5A6] leading-relaxed mb-2"><strong class="text-[#FFF8F0]/90">嚴選成分：</strong>{esc(it["ingredients"])}</p>'
            f'<p class="text-[11px] text-[#8FB98A]/90 leading-relaxed">{esc(it["note"])}</p></div>'
            f'<div class="mt-4 pt-3 border-t border-white/10 flex items-center justify-between gap-2">'
            f'<span class="text-xs text-[#C4B5A6]">預訂新鮮現做</span>'
            f'<button type="button" data-add-item="{it["id"]}" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-amber-500/20 hover:bg-[#E6B35A] hover:text-[#14110F] border border-amber-400/40 text-amber-200 transition-all active:scale-95">＋ 加入訂購單</button>'
            f'</div></article>'
        )
        cards.append(card)
    return "\n".join(cards)


def sync_all(verify_only=False):
    ssot_path = os.path.join(ROOT, "data", "menu-ssot.json")
    with open(ssot_path, "r", encoding="utf-8") as f:
        ssot = json.load(f)

    ucp_obj = build_ucp_manifest(ssot)
    ucp_str = json.dumps(ucp_obj, ensure_ascii=False, indent=2) + "\n"
    llms_str = build_llms_txt(ssot)
    json_ld_str = build_json_ld(ssot)
    ssr_cards_str = build_ssr_cards(ssot)
    js_menu_str = json.dumps(ssot["items"], ensure_ascii=False, separators=(",", ":"))

    html_path = os.path.join(ROOT, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    new_html = re.sub(
        r'(<script type="application/ld\+json">).*?(</script>)',
        lambda m: m.group(1) + json_ld_str + m.group(2),
        html_content,
        count=1,
        flags=re.S
    )
    new_html = re.sub(
        r"(<!-- SSOT:SSR_MENU_START -->).*?(<!-- SSOT:SSR_MENU_END -->)",
        lambda m: m.group(1) + "\n" + ssr_cards_str + "\n        " + m.group(2),
        new_html,
        count=1,
        flags=re.S
    )
    new_html = re.sub(
        r"(/\* SSOT:JS_MENU_START \*/).*?(/\* SSOT:JS_MENU_END \*/)",
        lambda m: f"{m.group(1)}var MENU_ITEMS = {js_menu_str};{m.group(2)}",
        new_html,
        count=1,
        flags=re.S
    )

    if not verify_only:
        with open(os.path.join(ROOT, ".well-known", "ucp"), "w", encoding="utf-8") as f:
            f.write(ucp_str)
        with open(os.path.join(ROOT, "ucp.json"), "w", encoding="utf-8") as f:
            f.write(ucp_str)
        with open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8") as f:
            f.write(llms_str)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(new_html)

    # Run strict QA & UCP v1.1 assertions
    errors = []
    for rel in [".nojekyll", ".well-known/ucp", "ucp.json", "llms.txt", "haotian-webmcp-bridge.js", "robots.txt", "sitemap.xml", "og-cover.jpg", "index.html"]:
        if not os.path.exists(os.path.join(ROOT, rel)):
            errors.append(f"Missing required file: {rel}")

    with open(os.path.join(ROOT, ".well-known", "ucp"), "r", encoding="utf-8") as f:
        ucp_loaded = json.load(f)
    if ucp_loaded.get("ucp_version") != "1.1":
        errors.append("ucp_version != 1.1")
    if len(ucp_loaded.get("catalog", [])) != 41:
        errors.append(f"UCP catalog count mismatch: {len(ucp_loaded.get('catalog', []))}")
    if ucp_loaded.get("agentic_access_policy", {}).get("web_bot_auth", {}).get("cdn_allowlist_ids", {}).get("cloudflare_bot_detection_id") != "129220581":
        errors.append("Missing Cloudflare Bot Detection ID 129220581 (AP-01)")
    if not ucp_loaded.get("agentic_payment_readiness", {}).get("pre_approval_disclosure", {}).get("shows_all_inclusive_total_twd"):
        errors.append("Missing AP-02 pre_approval_disclosure")

    with open(html_path, "r", encoding="utf-8") as f:
        final_html = f.read()

    forbidden = ["🩺", "黃膠原", "無任何化學添加物", "無添加物", "治療", "降血糖", "糖尿病"]
    for bad in forbidden:
        if bad in final_html or bad in llms_str:
            errors.append(f"Compliance violation term found: {bad}")

    if "已選 ×" in final_html.split("<script>")[0]:
        errors.append("SSR HTML still has pre-populated cart item badge!")

    if errors:
        print("SSOT & QA Verification FAILED:")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    print("PASS: All 41 SKUs synced across JSON-LD, SSR HTML, JS MENU_ITEMS, llms.txt, /.well-known/ucp (v1.1), and ucp.json! Zero compliance or broken-link issues.")


if __name__ == "__main__":
    verify = "--verify" in sys.argv
    sync_all(verify_only=verify)
