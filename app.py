import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

st.set_page_config(page_title="朝起拾要·全能工作室", layout="wide", page_icon="☀️")


# =========================
# 1 缓存 AI 客户端（关键优化）
# =========================

@st.cache_resource
def get_client(api_key):
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


# =========================
# 2 缓存热点数据（减少网络请求）
# =========================

@st.cache_data(ttl=600)
def get_hot_news():

    headers = {'User-Agent': 'Mozilla/5.0'}

    urls = [
        "https://api.oick.cn/api/baidu",
        "https://tenapi.cn/v2/webhot"
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=5)

            if resp.status_code == 200:

                data = resp.json()

                if "oick" in url:
                    return [item['title'] for item in data[:10]]
                else:
                    return [item['name'] for item in data['data'][:10]]

        except:
            continue

    return []


# =========================
# 初始化缓存
# =========================

if 'article_cache' not in st.session_state:
    st.session_state['article_cache'] = ""

if 'input_cache' not in st.session_state:
    st.session_state['input_cache'] = ""


# =========================
# 侧边栏
# =========================

with st.sidebar:

    st.title("☀️ 朝起拾要")

    st.divider()

    ds_key = st.secrets.get("ds_key")

    if ds_key:
        st.success("✅ DeepSeek API 已自动配置")
    else:
        ds_key = st.text_input("DeepSeek API Key", type="password")

    st.caption("核心模型：DeepSeek-V3")

    st.divider()

    st.subheader("🖼️ 视觉实验室")

    user_prompt = st.text_area("粘贴图片提示词 (英文)")

    if st.button("立即出图 🎨"):

        if user_prompt:

            with st.spinner("AI 正在渲染..."):

                clean_p = "".join(e for e in user_prompt if e.isalnum() or e == " ")

                encoded = urllib.parse.quote(clean_p.strip())

                seed = random.randint(1, 1000000)

                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&seed={seed}&nologo=true"

                st.image(img_url)


# =========================
# 主界面
# =========================

st.header("内容编辑")


# 热点区

st.subheader("🔥 实时全网热点")

if st.button("🔄 刷新热点"):

    with st.spinner("同步热点中..."):

        news = get_hot_news()

        if news:

            st.session_state['news_cache'] = news

        else:

            st.error("热点获取失败")


if 'news_cache' in st.session_state:

    cols = st.columns(2)

    for i, n in enumerate(st.session_state['news_cache']):

        if cols[i % 2].button(n):

            st.session_state['input_cache'] = n

            st.rerun()


st.divider()


# 输入区

raw_input = st.text_area(

    "在此粘贴素材或编辑：",

    value=st.session_state['input_cache'],

    height=200

)


# =========================
# AI生成
# =========================

if st.button("一键生成爆款文 🔥"):

    if not ds_key:

        st.error("请配置 API Key")

    elif not raw_input:

        st.warning("素材为空")

    else:

        client = get_client(ds_key)

        with st.spinner("主编写作中..."):

            try:

                sys_msg = "你是一个10万粉科技主编。风格犀利口语化。结构：3个标题、引言、正文、点评。500字以上。"

                response = client.chat.completions.create(

                    model="deepseek-chat",

                    messages=[

                        {"role": "system", "content": sys_msg},

                        {"role": "user", "content": raw_input}

                    ]

                )

                result = response.choices[0].message.content

                st.session_state['article_cache'] = result

            except Exception as e:

                st.error(f"生成失败：{e}")


# =========================
# 输出区
# =========================

if st.session_state['article_cache']:

    st.divider()

    st.subheader("✍️ AI生成结果")

    st.markdown(st.session_state['article_cache'])