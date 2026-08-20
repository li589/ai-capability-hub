"""
Mini App Order - 业务 API 客户端 + CLI 入口
==========================================
业务接口（商品搜索/详情、收货地址、订单创建）封装。
认证与 Token 管理逻辑已拆分至 auth.py。

CLI 用法：
  python api_client.py --get-qr
  python api_client.py --poll-login --pcKey <key>
  python api_client.py --logout
"""

import json
import os
import sys
import uuid
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Optional

try:
    from .common import (
        BASE_URL,
        API_PREFIX,
        ENV_LABEL,
        TIMEOUT,
        SEARCH_HEADERS,
        get_client_type,
        get_os,
    )
    from .auth import (
        get_qr_code,
        poll_for_token,
        get_valid_token,
        logout,
        _clear_token_cache,
    )
except ImportError:
    from common import (
        BASE_URL,
        API_PREFIX,
        ENV_LABEL,
        TIMEOUT,
        SEARCH_HEADERS,
        get_client_type,
        get_os,
    )
    from auth import (
        get_qr_code,
        poll_for_token,
        get_valid_token,
        logout,
        _clear_token_cache,
    )


# =====================================================
# API 客户端（自动携带 token）
# =====================================================

class AuthRequiredError(RuntimeError):
    """需要扫码登录的特殊异常。WorkBuddy 捕获此异常后应触发两阶段扫码登录流程。"""
    pass


class NoAddressError(RuntimeError):
    """用户没有收货地址。需引导用户先去小程序中补充收货地址。"""
    pass


def _check_api_result(result: dict):
    """检查 API 返回结果，code 非 "000" 时抛出异常。"""
    code = result.get("code", "")
    if code != "000":
        msg = result.get("message", "") or result.get("msg", "") or "未知错误"
        raise RuntimeError(f"API 返回错误 (code={code}): {msg}")


class MiniAppClient:
    """
    公司小程序 API 客户端。
    每次调用前自动获取有效 token，无需手动管理登录状态。
    """

    def __init__(self, base_url: str = BASE_URL, api_prefix: str = API_PREFIX):
        self.base_url = base_url.rstrip("/")
        self.api_prefix = api_prefix  # 正式环境 "/api"，测试环境 "/api2"

    def _request(self, method: str, path: str, data: Optional[dict] = None, with_auth: bool = True) -> dict:
        """
        发送 HTTP 请求。
        path 以 /api/... 开头，会自动替换为环境对应的 api_prefix。
        with_auth=False 时，不携带 AccessToken（用于游客接口）。
        """
        # 将 /api/xxx 统一替换为当前环境的 api_prefix（如 /api2/xxx）
        if path.startswith("/api"):
            path = self.api_prefix + path[len("/api"):]
        url = f"{self.base_url}{path}"
        headers = SEARCH_HEADERS.copy()
        if with_auth:
            token = get_valid_token()
            if not token:
                raise AuthRequiredError(
                    "需要微信扫码登录。请先调用 get_qr_code() 获取二维码展示给用户，"
                    "用户扫码后调用 poll_for_token(pc_key) 获取 token，然后重试此操作。"
                )
            headers["AccessToken"] = token
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            # HTTP 402 是微信 AI 支付的关键标识状态码，正常返回数据，不抛异常
            if e.code == 402:
                return json.loads(error_body)
            if e.code == 401 and with_auth:
                _clear_token_cache()
                raise AuthRequiredError(
                    "身份验证失败（Token 已失效）。请重新扫码登录。"
                )
            raise RuntimeError(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"网络错误: {e.reason}")

    # =====================================================
    # Helpers
    # =====================================================

    def _build_image_url(self, relative_url: str) -> str:
        """将商品 url 相对路径拼成完整图片 URL，并附加腾讯云 COS 图片处理缩略图后缀。"""
        if not relative_url:
            return ""
        if relative_url.startswith("http"):
            base = relative_url
        else:
            base = "https://img.wawo.cc" + relative_url
        return base + "?imageMogr2/thumbnail/300x"

    # =====================================================
    # Product APIs
    # =====================================================

    def search_products(
        self,
        keyword: str,
        page_num: int = 1,
        page_size: int = 9,
        from_source: int = 2,
    ) -> dict:
        """
        搜索商品（游客接口，无需登录）。

        接口：POST https://7.wawo.cc/api/item/wx/launch/un/searchConvert
        认证：无需 Token（游客可直接搜索）

        返回结构（已处理）：
        {
            "goods": [{"name", "price", "launchNo", "url", "image_url", ...}, ...],
            "total": 107,          # 商品总数
            "page_num": 1,        # 当前页码
            "page_size": 9,        # 每页数量
            "has_more": True,      # 是否还有下一页
        }

        ⚠️ 商品数据在 API 原始返回的 data.records.goodsShowInfo 中，
        本函数已自动提取并附加 image_url 字段。

        Args:
            keyword:     搜索关键词，例如 "水果"
            page_num:    页码，默认 1
            page_size:   每页数量，默认 9
            from_source: 来源，默认 2

        Returns:
            包含商品列表和分页信息的 dict，见上方返回结构。
        """
        payload = {
            "pageNum": page_num,
            "pageSize": page_size,
            "name": keyword,
            "fromSource": from_source,
            "convert": 1,
            "searchWordType": "用户输入",
            "requestId": None,
        }
        result = self._request("POST", "/api/item/wx/launch/un/searchConvert", data=payload, with_auth=False)
        data = result.get("data", {})
        records = data.get("records", {})
        # 商品列表在 data.records.goodsShowInfo 中
        goods = records.get("goodsShowInfo", [])
        total = data.get("total", 0)

        # 为每条商品补上完整图片 URL
        for item in goods:
            item["image_url"] = self._build_image_url(item.get("url", ""))

        return {
            "goods": goods,
            "total": total,
            "page_num": page_num,
            "page_size": page_size,
            "has_more": page_num * page_size < total,
        }

    def list_products(self, category: str = "", page: int = 1, limit: int = 20) -> dict:
        """列出商品列表（待接入真实接口）。"""
        params = urllib.parse.urlencode({"category": category, "page": page, "limit": limit})
        return self._request("GET", f"/api/products?{params}")

    def get_product_detail(self, launch_no: str) -> dict:
        """
        获取商品详情（游客接口，无需登录）。

        接口：POST https://7.wawo.cc/api/item/wx/detail/un/info_v2
        认证：无需 Token（游客可直接查看商品详情）
        入参：launchNo — 搜索商品返回的 launchNo 字段

        Returns:
            接口原始返回的 dict，关键字段：
            - data.name: 商品名称
            - data.des: 描述
            - data.url: 主图（相对路径，拼上 https://img.wawo.cc）
            - data.msg: 详情图 HTML（含 <img> 标签）
            - data.skuList[]: SKU 规格列表
              - skuId, price（元）, stock, specsV1, unit, deliveryTime
              - finalPriceStr: 优惠后最终价格（仅 voucherVO 存在时附带，如 "52"）
            - data.splBrandName: 品牌
            - data.shelfTags.titleLeft[]: 标签（如"爆品"）
            - data.stock: 总库存
            - data.voucherVO: 优惠信息（存在时 sku 价格取 skuPriceItemList.finalPriceStr）
        """
        payload = {
            "launchNo": launch_no,
            "moduleId": "",
            "marketCategoryId": "",
            "collectionType": "",
        }
        result = self._request("POST", "/api/item/wx/detail/un/info_v2", data=payload, with_auth=False)
        data = result.get("data", {})

        # 当 voucherVO 存在时，将 skuPriceItemList 中的 finalPriceStr 合并到对应 SKU
        voucher_vo = data.get("voucherVO")
        if voucher_vo and voucher_vo.get("skuPriceItemList"):
            # 按 skuId 建立索引，方便快速查找
            price_map = {}
            for item in voucher_vo["skuPriceItemList"]:
                price_map[item.get("skuId")] = item
            for sku in data.get("skuList", []):
                sku_id = sku.get("skuId")
                price_item = price_map.get(sku_id)
                if price_item:
                    sku["finalPriceStr"] = price_item.get("finalPriceStr", "")

        # 为 skuList 中的图片补全 URL
        for sku in data.get("skuList", []):
            sku["image_url"] = self._build_image_url(sku.get("img", ""))
        # 主图补全
        data["image_url"] = self._build_image_url(data.get("url", ""))
        return result

    # =====================================================
    # Address API
    # =====================================================

    def get_address(self) -> dict:
        """
        获取用户默认收货地址（需登录）。

        接口：GET https://7.wawo.cc/api/account/wx/address/first
        认证：需 AccessToken
        说明：该接口返回加密数据，直接回显即可，无需解密。

        Returns:
            加密后的收货地址 dict：
            - id: 地址ID
            - name: 收件人姓名（加密，如 "*"）
            - phone: 收件人电话（脱敏，如 "155****8416"）
            - address: 详细地址（脱敏，如 "山东省济南市****立下小楼"）

        Raises:
            NoAddressError: 用户没有收货地址
        """
        result = self._request("GET", "/api/account/wx/address/first")
        data = result.get("data") or {}

        if not data or not data.get("id"):
            raise NoAddressError(
                "您还没有收货地址，请先去小程序中补充收货地址后再来下单。"
            )

        return {
            "id": data.get("id"),
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "address": data.get("address", ""),
        }

    # =====================================================
    # Order APIs
    # =====================================================

    def create_order(
        self,
        launch_no: str,
        sku: dict,
        quantity: int = 1,
        address: dict = None,
    ) -> dict:
        """
        创建订单（需登录）。

        接口：POST https://7.wawo.cc/api/cart/wx/order/wb_cr
        认证：需 AccessToken

        Args:
            launch_no: 商品 launchNo（从搜索或商详获取）
            sku:       选中的 SKU 信息，需包含 id、skuId、price 字段（来自商详 skuList）
            quantity:  购买数量，默认 1
            address:   收货地址 dict（来自 get_address() 返回值），仅需 id 字段

        Returns:
            {
                "mainOrderNo": "1020260605000014713891",  # 主订单号，展示给用户时必须取这个
                "subOrderNo": "1020260605043004953900"    # 子订单号，仅用于内部记录
            }

        生单成功后，展示订单号时**必须取 mainOrderNo**。
        """
        if not address:
            address = self.get_address()

        request_id = str(uuid.uuid4()).replace("-", "")

        # actualAmount 取值：优先使用 finalPriceStr（voucherVO 存在时），否则回退到 price
        final_price_str = sku.get("finalPriceStr")
        if final_price_str:
            actual_amount = float(final_price_str) * quantity
        else:
            actual_amount = sku["price"] * quantity

        payload = {
            "vipLevel": 0,
            "actualAmount": actual_amount,
            "orderAddressList": [{
                "id": address.get("id"),
            }],
            "orderGoodsList": [{
                "launchNo": launch_no,
                "num": quantity,
                "launchSkuId": sku["id"],       # 商详 skuList 中的 id 字段
                "skuId": sku["skuId"],           # 商详 skuList 中的 skuId 字段
                "entranceSource": "workBuddy",
                "activity": "",
                "distributionCard": "",
                "distributionType": "",
                "requestId": request_id,
                "addressId": address.get("id"),
                "goodsType": 1,
                "primageVo": None,
            }],
            "orderType": "order_shop",
            "scoreAmount": 0,
            "smoothScoreAmount": 0,
            "sourcePlat": 4,
            "shopOrderSubmit": {
                "type": 0,
                "sharedUserInfo": None,
                "inviterCardNo": "",
            },
            "threeTuanOrderSubmit": None,
            "orderUserCouponList": [],
            "useCoupon": False,
            "priExpr": 1,
        }

        result = self._request("POST", "/api/cart/wx/order/wb_cr", data=payload)
        data = result.get("data", {})
        return {
            "mainOrderNo": data.get("mainOrderNo", ""),
            "subOrderNo": data.get("subOrderNo", ""),
        }

    # =====================================================
    # Payment API
    # =====================================================

    @staticmethod
    def _generate_pay_qr_code(code_url: str, order_no: str = "") -> dict:
        """
        将支付 codeUrl 生成可直接用于 show_widget 的 HTML 二维码。

        使用 Canvas + 内联 JS 渲染，无需 Pillow，速度极快，尺寸固定 300px 确保可扫描。

        Args:
            code_url:  微信支付 native codeUrl，如 weixin://wxpay/bizpayurl?pr=xxx
            order_no:  订单号（用于文件命名）

        Returns:
            {
                "html": "<div>...<canvas>...</canvas><script>...</script></div>",
            }
        """
        import qrcode

        # 生成 QR 模块矩阵（box_size=1 控制矩阵大小，由版本号自动决定）
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=1,
            border=4,
        )
        qr.add_data(code_url)
        qr.make(fit=True)

        count = len(qr.modules)
        # 将模块矩阵编码为紧凑的 0/1 字符串
        module_str = "".join("1" if cell else "0" for row in qr.modules for cell in row)
        canvas_size = 300

        html = (
            f'<div style="text-align:center;padding:24px;font-family:system-ui,-apple-system,sans-serif;background:#fff;">'
            f'<h3 style="margin:0 0 20px 0;color:#333;font-size:18px;font-weight:600;">'
            f'微信支付二维码</h3>'
            f'<canvas id="payqr" width="{canvas_size}" height="{canvas_size}" '
            f'style="display:block;margin:0 auto;border:1px solid #e8e8e8;border-radius:8px;">'
            f'</canvas>'
            f'<p style="margin:16px 0 0 0;color:#666;font-size:14px;">请用微信扫描完成支付</p>'
            f'<script>'
            f'(function(){{'
            f'var m="{module_str}",c={count},s={canvas_size},u=s/c,'
            f'e=document.getElementById("payqr"),x=e.getContext("2d");'
            f'x.fillStyle="#fff";x.fillRect(0,0,s,s);x.fillStyle="#000";'
            f'for(var i=0;i<m.length;i++){{'
            f'if(m[i]==="1"){{var px=i%c,py=Math.floor(i/c);'
            f'x.fillRect(px*u,py*u,u,u);}}'
            f'}}'
            f'}})();'
            f'</script></div>'
        )

        return {"html": html}

    def pay_order(
        self,
        main_order_no: str,
        payment_type: str = "nativePay",
    ) -> dict:
        """
        调用支付接口，获取微信支付链接及 AI 支付码。

        接口：POST https://7.wawo.cc/api/transaction/wx/order/payment/agent
        认证：需 AccessToken

        Args:
            main_order_no: 主订单号（create_order 返回的 mainOrderNo）
            payment_type:  支付方式，默认 "nativePay"

        Returns:
            {
                "paymentCode": "PAYCODE_xxxxxxxxxxxxxxxx",   # WeixinPay AI支付码，对接 weixinpay_pay
            }

        Raises:
            RuntimeError: 接口返回异常或未包含有效 WeixinPay-Required
        """
        payload = {
            "mainOrderNo": main_order_no,
            "paymentType": payment_type,
        }
        result = self._request("POST", "/api/transaction/wx/order/payment/agent", data=payload)

        payment_code = result.get("WeixinPay-Required", "")

        if not payment_code:
            raise RuntimeError("支付接口未返回有效的 WeixinPay 支付码，请检查接口版本")

        return {
            "WeixinPay-Required": payment_code,
        }

    def poll_payment_result(
        self,
        main_order_no: str,
        timeout: int = 600,
        interval: int = 3,
    ) -> dict:
        """
        轮询支付结果，每 {interval} 秒查询一次，最长等待 {timeout} 秒。
        轮询期间接口异常会静默重试，不影响轮询继续。

        接口：POST /api/transaction/wx/order/wx_pay_result?mainOrderNo=xxx
        认证：需 AccessToken
        ⚠️ mainOrderNo 通过 query 参数传递，body 为 {}

        Args:
            main_order_no: 主订单号（create_order 返回的 mainOrderNo）
            timeout:       超时时间（秒），默认 600（10分钟）
            interval:      轮询间隔（秒），默认 3

        Returns:
            支付结果数据 dict，关键字段：
            - payStatus: 支付结果 0:未支付（继续轮询） 1:成功

        Raises:
            RuntimeError: 轮询超时，10分钟内未支付成功
        """
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                result = self._request(
                    "POST",
                    f"/api/transaction/wx/order/wx_pay_result?mainOrderNo={main_order_no}",
                    data={},
                )
                _check_api_result(result)
                data = result.get("data", {})
                pay_status = data.get("payStatus")
                if pay_status == 1:
                    return data
            except Exception:
                pass  # 轮询期间接口异常时静默继续，不中断轮询
            time.sleep(interval)
        raise RuntimeError(
            f"查询支付结果超时，后续请于小程序订单详情查看。"
        )

    def get_order(self, order_id: str) -> dict:
        """查询订单详情。TODO: 更新为真实接口路径。"""
        return self._request("GET", f"/api/orders/{order_id}")

    def list_orders(self, status: str = "", page: int = 1, limit: int = 20) -> dict:
        """查询订单列表。TODO: 更新为真实接口路径。"""
        params = urllib.parse.urlencode({"status": status, "page": page, "limit": limit})
        return self._request("GET", f"/api/orders?{params}")

    def cancel_order(self, order_id: str, reason: str = "") -> dict:
        """取消订单。TODO: 更新为真实接口路径。"""
        return self._request("POST", f"/api/orders/{order_id}/cancel", data={"reason": reason})

    # =====================================================
    # Miniprogram Link API（小程序端跳转链接）
    # =====================================================

    def get_miniprogram_link(self, launch_no: str) -> str:
        """
        获取小程序跳转链接（游客接口，无需登录）。

        接口：GET /api/tripartite/wx/scheme/generateUrlLink?path=...
        认证：无需 Token

        Args:
            launch_no: 商品 launchNo

        Returns:
            HTTPS 可点击链接，例如 "https://wxaurl.cn/8iSjEMA3MJn"

        Raises:
            RuntimeError: 接口返回异常
        """
        raw_path = f"shopping_pages/pages/goodsInfo/goodsInfo?c=workbuddy&launchNo={launch_no}"
        encoded_path = urllib.parse.quote(raw_path, safe="")
        api_path = f"/api/tripartite/wx/scheme/generateUrlLink?path={encoded_path}"

        result = self._request("GET", api_path, data=None, with_auth=False)

        if not result.get("success") or result.get("code") != "000":
            msg = result.get("message") or "未知错误"
            raise RuntimeError(f"获取小程序链接接口异常 (code={result.get('code')}): {msg}")

        link = result.get("data", "")
        if not link:
            raise RuntimeError("接口返回的小程序链接为空")
        return link

    # =====================================================
    # Sun Code API（Windows 端太阳码）
    # =====================================================

    def get_suncode(self, launch_no: str) -> str:
        """
        生成小程序太阳码（游客接口，无需登录）。

        用于 Windows 端和小程序端 WorkBuddy，引导用户微信扫码跳转小程序下单。

        接口：POST /api/tripartite/wx/QR?scene=$...&page=...
        认证：无需 Token

        Args:
            launch_no: 商品 launchNo（从搜索或商详获取）

        Returns:
            完整太阳码图片 URL，例如 "https://img.wawo.cc/wxqr/2026-06-12/xxx.jpg"

        Raises:
            RuntimeError: 接口返回异常或 data 为空
        """
        scene = f"workb${launch_no}"
        page = "shopping_pages/pages/goodsInfo/goodsInfo"
        params = urllib.parse.urlencode({"scene": scene, "page": page})
        api_path = f"/api/tripartite/wx/QR?{params}"

        # 此接口 code 可能为 null，不经过 _check_api_result，直接用 data 字段判断
        result = self._request("POST", api_path, data={}, with_auth=False)

        data = result.get("data", "")
        if not data:
            raise RuntimeError("太阳码接口返回的图片路径为空")

        # 拼上完整 URL 前缀
        if data.startswith("http"):
            return data
        return "https://img.wawo.cc" + data


# =====================================================
# CLI / 快速测试
# =====================================================
if __name__ == "__main__":
    import sys

    # 启动时打印当前环境
    print(f"[环境] {ENV_LABEL} — {BASE_URL}{API_PREFIX}")

    if len(sys.argv) >= 2:
        mode = sys.argv[1]

        if mode == "--get-qr":
            # 阶段 1：获取二维码图片
            try:
                get_qr_code()
            except RuntimeError as e:
                print(f"错误: {e}")
                sys.exit(1)

        elif mode == "--poll-login":
            # 阶段 2：轮询获取 token（需传 --pcKey）
            pc_key = None
            for i, arg in enumerate(sys.argv):
                if arg == "--pcKey" and i + 1 < len(sys.argv):
                    pc_key = sys.argv[i + 1]
                    break
            if not pc_key:
                print("错误: 需要 --pcKey 参数，例如: --poll-login --pcKey abc123")
                sys.exit(1)
            try:
                token = poll_for_token(pc_key)
                print(f"登录成功，token（前20位）: {token[:20]}...")
            except RuntimeError as e:
                print(f"错误: {e}")
                sys.exit(1)

        elif mode == "--check-client":
            # 检测当前客户端类型（pc / miniprogram）
            client_type = get_client_type()
            print(client_type)

        elif mode == "--check-os":
            # 检测当前操作系统（darwin / windows / linux）
            os_type = get_os()
            print(os_type)

        elif mode == "--get-suncode":
            # 生成小程序太阳码（需传 --launchNo <launchNo>）
            launch_no = None
            for i, arg in enumerate(sys.argv):
                if arg == "--launchNo" and i + 1 < len(sys.argv):
                    launch_no = sys.argv[i + 1]
                    break
            if not launch_no:
                print("错误: 需要 --launchNo 参数，例如: --get-suncode --launchNo 1700142193531")
                sys.exit(1)
            try:
                client = MiniAppClient()
                suncode_url = client.get_suncode(launch_no)
                print(suncode_url)
            except RuntimeError as e:
                print(f"错误: {e}")
                sys.exit(1)

        elif mode == "--get-mp-link":
            # 获取小程序跳转链接（需传 --launchNo <launchNo>）
            launch_no = None
            for i, arg in enumerate(sys.argv):
                if arg == "--launchNo" and i + 1 < len(sys.argv):
                    launch_no = sys.argv[i + 1]
                    break
            if not launch_no:
                print("错误: 需要 --launchNo 参数，例如: --get-mp-link --launchNo 1700145740437")
                sys.exit(1)
            try:
                client = MiniAppClient()
                link = client.get_miniprogram_link(launch_no)
                print(link)
            except RuntimeError as e:
                print(f"错误: {e}")
                sys.exit(1)

        elif mode == "--logout":
            # 退出登录：清除本地 token 缓存
            logout()

        elif mode == "--pay":
            # 调用支付接口（需传 --order <mainOrderNo>）
            order_no = None
            for i, arg in enumerate(sys.argv):
                if arg == "--order" and i + 1 < len(sys.argv):
                    order_no = sys.argv[i + 1]
                    break
            if not order_no:
                print("错误: 需要 --order 参数，例如: --pay --order 1020260608000000268612")
                sys.exit(1)
            try:
                client = MiniAppClient()
                pay_result = client.pay_order(order_no)
                print(f"支付链接: {pay_result['codeUrl']}")
                print(f"二维码 HTML 已生成（{len(pay_result['html'])} 字符）")
            except AuthRequiredError:
                print("需要微信扫码登录，请先执行 --get-qr 和 --poll-login")
                sys.exit(1)
            except RuntimeError as e:
                print(f"错误: {e}")
                sys.exit(1)

        else:
            print(f"未知模式: {mode}")
            print("用法:")
            print("  python api_client.py --check-client                        # 检测客户端类型 (pc/miniprogram)")
            print("  python api_client.py --check-os                            # 检测操作系统 (darwin/windows/linux)")
            print("  python api_client.py --get-suncode --launchNo <launchNo>   # 生成小程序太阳码（Windows 端）")
            print("  python api_client.py --get-mp-link --launchNo <launchNo>   # 获取小程序跳转链接")
            print("  python api_client.py --get-qr                             # 阶段1: 获取二维码")
            print("  python api_client.py --poll-login --pcKey <key>           # 阶段2: 轮询登录（最长5分钟）")
            print("  python api_client.py --logout                             # 退出登录")
            print("  python api_client.py --pay --order <orderNo>              # 调用支付接口")
            sys.exit(1)

    else:
        print("=== Mini App Order — 登录测试 ===")
        try:
            token = get_valid_token()
            if token:
                print(f"当前 token（前20位）: {token[:20]}...")
                client = MiniAppClient()
                products = client.search_products("测试")
                print(f"搜索到 {len(products)} 个商品")
        except RuntimeError as e:
            print(f"错误: {e}")
