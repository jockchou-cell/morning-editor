import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

# 1. 页面配置
st.set_page_config(page_title="朝起拾要·全能工作室", layout="wide", page_icon="☀️")

# --- 初始化状态 ---
if 'article_cache' not in st.session_state:
    st.session_state['article_cache'] = ""
if 'news_cache' not in st.session_state:
    st.session_state['news_cache'] = []
if 'input_cache' not in st.session_state:
    st.session_state['input_cache'] = ""

# --- 2. 侧边栏 ---
with st.sidebar:
    st.title("☀️ 朝起拾要")
    st.divider()
    
    # 智能 Key 检测：修复 Secret 报错
    ds_key = st.secrets.get("ds_key") # 使用 .get 即使本地没有也不会崩溃
    if ds_key:
        st.success("✅ DeepSeek API 已自动配置")
    else:
        ds_key = st.text_input("DeepSeek API Key (本地运行专用)", type="password")
        st.info("💡 提示：云端部署建议在 Secrets 中配置 ds_key")

    st.caption("核心模型：DeepSeek-V3 | 绘图引擎：Pollinations Cloud")
    
    st.divider()
    st.subheader("🖼️ 视觉实验室")
    user_prompt = st.text_area("粘贴图片提示词 (英文)", placeholder="例如: Cyberpunk electric car...")
    if st.button("立即出图 🎨"):
        if not user_prompt:
            st.warning("请填入提示词")
        else:
            with st.spinner("AI 正在渲染..."):
                clean_p = "".join(e for e in user_prompt if e.isalnum() or e == " ")
                encoded = urllib.parse.quote(clean_p.strip())
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&seed={random.randint(1,1000000)}&nologo=true"
                st.markdown(f"![Generated Image]({img_url})")

# --- 3. 主界面 ---
st.header("内容编辑")

st.subheader("🔥 实时全网热点")
# 刷新按钮
if st.button("🔄 刷新实时热搜"):
    with st.spinner("正在同步全球热搜..."):
        headers = {'User-Agent': 'Mozilla/5.0'}
        urls = ["https://api.oick.cn/api/baidu", "https://tenapi.cn/v2/webhot"]
        success = False
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    # 统一提取逻辑
                    st.session_state['news_cache'] = [item.get('title') or item.get('name') for item in (data if isinstance(data, list) else data.get('data', []))[:10]]
                    st.success("热点同步成功！")
                    success = True
                    break
            except: continue
        if not success:
            st.error("云端同步受限，请尝试手动摘取。")

st.divider()

# --- 核心改进：二选一展示逻辑 ---
if st.session_state['news_cache']:
    # 情况 A：同步成功，只展示热点按钮
    st.caption("已同步最新热点，点击即可作为素材：")
    cols = st.columns(2)
    for i, n in enumerate(st.session_state['news_cache']):
        if cols[i % 2].button(f"📌 {n}", key=f"btn_{i}", use_container_width=True):
            st.session_state['input_cache'] = n
            st.rerun()
    if st.button("清除热点列表"):
        st.session_state['news_cache'] = []
        st.rerun()
else:
    # 情况 B：未同步或失败，展示 6 个媒体链接
    st.info("💡 当前未同步热搜，建议前往以下信源摘取素材：")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    c1.link_button("36氪科技", "https://36kr.com/technology")
    c2.link_button("IT之家", "https://www.ithome.com/")
    c3.link_button("汽车之家", "https://www.autohome.com.cn/")
    c4.link_button("虎扑热榜", "https://bbs.hupu.com/all-groot")
    c5.link_button("界面新闻", "https://www.jiemian.com/")
    c6.link_button("今日头条", "https://www.toutiao.com/")

st.divider()

# 编辑区
raw_input = st.text_area("在此粘贴素材或编辑：", value=st.session_state['input_cache'], height=200)

if st.button("开始文章构思 🔥"):
    if not ds_key:
        st.error("请配置 API Key")
    elif not raw_input:
        st.warning("素材内容为空。")
    else:
        client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
        try:
            with st.spinner("才思泉涌中..."):
                sys_msg = "你是一个顶级主编。结构：5个标题、引言、正文（加粗）、总结。文末必须附带英文绘图词 [IMG_PROMPT]: 内容"
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": raw_input}]
                )
                st.session_state['article_cache'] = response.choices[0].message.content
        except Exception as e: st.error(f"生成失败：{e}")

# 结果展示：使用 st.code 实现安全一键复制
if st.session_state['article_cache']:
    st.markdown("---")
    st.caption("点击右上角图标即可复制全文：")
    st.code(st.session_state['article_cache'], language="markdown")
    st.markdown("### 内容预览")
    st.markdown(st.session_state['article_cache'])