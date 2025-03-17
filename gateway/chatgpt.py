import json
import logging
import os
import time

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from starlette.responses import RedirectResponse

import gateway.share
from app import app, templates
from entity.share import Share
from gateway import common_utils
from gateway.login import login_html
from utils.configs import redis_utils
from utils.kv_utils import set_value_for_key_list
from utils.token_util import access_to_share, generate_short_token

with open("templates/chatgpt_context_1.json", "r", encoding="utf-8") as f:
    chatgpt_context_1 = json.load(f)
with open("templates/chatgpt_context_2.json", "r", encoding="utf-8") as f:
    chatgpt_context_2 = json.load(f)



@app.get("/", response_class=HTMLResponse)
async def chatgpt_html(request: Request):
    share_token = request.query_params.get("share_token")
    if not share_token:
        share_token = request.cookies.get("share_token")
    if not share_token:
        response = templates.TemplateResponse("login.html", {"request": request})
        return response

    use_at = False

    user_chatgpt_context_1 = chatgpt_context_1.copy()
    user_chatgpt_context_2 = chatgpt_context_2.copy()


    if request.cookies.get("oai-locale"):
        set_value_for_key_list(user_chatgpt_context_1, "locale", request.cookies.get("oai-locale"))

    user_chatgpt_context_1 = json.dumps(user_chatgpt_context_1, separators=(',', ':'), ensure_ascii=False)
    user_chatgpt_context_2 = json.dumps(user_chatgpt_context_2, separators=(',', ':'), ensure_ascii=False)

    escaped_context_1 = user_chatgpt_context_1.replace("\\", "\\\\")
    escaped_context_2 = user_chatgpt_context_2.replace("\\", "\\\\")

    escaped_context_1 = escaped_context_1.replace('"', '\\"')
    escaped_context_2 = escaped_context_2.replace('"', '\\"')
    # share token
    if share_token.startswith("fk-"):
        access_token = common_utils.get_access_token(share_token)
        set_value_for_key_list(user_chatgpt_context_1, "accessToken", access_token)
    # access token
    elif share_token.startswith("eyJhbGciOi"):
        use_at = True
        access_token = share_token
        share_token = generate_short_token(access_token, "user-chatgpt")
        set_value_for_key_list(user_chatgpt_context_1, "accessToken", access_token)

        # 检查原有用户信息,如果存在需要删除
        former_share_token = redis_utils.get_value('user_info:' + share_token)
        if former_share_token is not None:
            redis_utils.delete_keys("share_token_info:" + former_share_token)
        # 将share_token存入redis
        share = Share()
        share.access_token = access_token
        share.user_name = share_token
        share.isolated_session = 0
        redis_utils.hash_set("share_token_info:" + share_token, share.__dict__, 86400 * 10)
        # 将用户对应share_token存入redis
        redis_utils.set_value("user_info:" + share_token, share_token, 86400 * 10)
    # 其他情况暂时不处理
    else:
        raise HTTPException(status_code=401, detail="Error RefreshToken")

    # at为空，返回
    if access_token is None:
        raise HTTPException(status_code=401, detail="Error RefreshToken")
    else:
        info = gateway.share.chatgpt_account_check(access_token)
        if info is None or info == {}:
            raise HTTPException(status_code=401, detail="AccessToken Expired")

        response = templates.TemplateResponse("chatgpt.html", {
            "request": request,
            "react_chatgpt_context_1": escaped_context_1,
            "react_chatgpt_context_2": escaped_context_2
        })
        if not use_at:
            response.set_cookie("share_token", value=share_token, expires="tomorrow 08:00:00 GMT")
        else:
            # 10天过期
            response.set_cookie("share_token", value=share_token, expires="10d")


        return response


@app.get('/api/not-login', response_class=HTMLResponse)
def api_free_login(request: Request):
    share_token = request.query_params.get('user_gateway_token')

    # 不为空，获取at并校验
    if share_token is not None:
        access_token = common_utils.get_share_token(share_token)
        # at为空，返回
        if access_token is None:
            raise HTTPException(status_code=401, detail="Error RefreshToken")
        else:
            info = gateway.share.chatgpt_account_check(access_token)
            if info is None or info == {}:
                raise HTTPException(status_code=401, detail="AccessToken Expired")

            response = RedirectResponse(url="/", status_code=302)
            response.set_cookie("share_token", value=share_token, expires="tomorrow 08:00:00 GMT")
            return response
    else:
        raise HTTPException(status_code=401, detail="Error RefreshToken")


@app.post('/api/login', response_class=HTMLResponse)
async def api_share(request: Request):
    # 获取body并转json
    share_info = await request.json()
    isolated_session = share_info.pop('isolated_session', None)
    # 转换为实体类
    share = Share(**share_info)
    share.conversation_isolation = 1 if isolated_session is not None and isolated_session == 1 else 0
    share_info['conversation_isolation'] = 1 if isolated_session is True else 0
    # 获取当前时间戳
    current = int(time.time())
    # 获取过期时间
    expire = share.expire_at - current
    info = gateway.share.chatgpt_account_check(share.access_token)
    if info is None or info == {}:
        response = {'status': False, 'message': '无效的 access token', 'data': None}
        return response

    # 生成share_token
    share_token = access_to_share(share)

    # 检查原有用户信息,如果存在需要删除
    former_share_token = redis_utils.get_value('user_info:' + share.user_name)
    if former_share_token is not None:
        redis_utils.delete_keys("share_token_info:" + former_share_token)
    # 将share_token存入redis
    # share_info['isolated_session'] = None
    result = redis_utils.hash_set("share_token_info:" + share_token, share_info, expire if expire > 0 else None)
    # 将用户对应share_token存入redis
    redis_utils.set_value("user_info:" + share.user_name, share_token, expire if expire > 0 else None)

    # 返回share_token
    response = {'status': True, 'message': 'Success', 'user-gateway-token': share_token}
    print("生成的share_token: ", share_token)
    # 返回http response
    return Response(
        content=json.dumps(response),
        media_type="application/json",
        status_code=200
    )
