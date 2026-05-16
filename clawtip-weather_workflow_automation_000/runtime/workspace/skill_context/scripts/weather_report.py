import sys
import json
import urllib.request
import urllib.error

GET_RESULT_URL = "https://ms.jr.jd.com/gw2/generic/hyqy/na/m/getWeatherResult"


def counseling(question: str, order_no: str, credential: str) -> str:
    print("weather reporting location is: " + question)
    if credential is None:
        return "Please enter your counseling credential"

    payload = json.dumps({
        "question": question,
        "orderNo": order_no,
        "credential": credential
    }).encode("utf-8")

    req = urllib.request.Request(
        GET_RESULT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8")).get("resultData")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Counseling request failed: {e}") from e

    if body.get("responseCode") != "200":
        raise RuntimeError(
            f"Counseling failed: {body.get('responseMessage', 'unknown error')}"
        )

    pay_status = body.get("payStatus")
    print(f"PAY_STATUS: {pay_status}")

    answer = body.get("answer")
    if not answer  and "ERROR" == pay_status:
        # 避免 key 不存在时报错
        raise RuntimeError(f'获取信息失败：原因：{body.get("errorInfo", "未知错误")}')
    return answer


import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get weather counseling report")
    parser.add_argument("question", help="Location for weather report")
    parser.add_argument("order_no", help="Order number")
    parser.add_argument("credential", help="Payment credential")
    args = parser.parse_args()

    try:
        result = counseling(args.question, args.order_no, args.credential)
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


