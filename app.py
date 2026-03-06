import streamlit as st
import requests
import urllib.parse
import random
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="朝起拾要·全能工作室", layout="wide", page_icon="☀️")

# --- 初始化状态 (防止刷新消失) ---
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
    
    # 智能 Key 检测 (修复本地 Secret 报错)
    ds_key = st.secrets.get("ds_key") 
    if ds_key:
        st.success("✅ API 已自动配置")
    else:
        ds_key = st.text_input("DeepSeek API Key (本地运行请填入)", type="password")

    st.divider()
    st.subheader("🖼️ 视觉实验室")
    user_prompt = st.text_area("粘贴图片提示词 (英文)", placeholder="例如: Cyberpunk car...")
    if st.button("立即出图 🎨"):
        if user_prompt:
            with st.spinner("AI 渲染中..."):
                clean_p = "".join(e for e in user_prompt if e.isalnum() or e == " ")
                encoded = urllib.parse.quote(clean_p.strip())
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&seed={random.randint(1,99999)}&nologo=true"
                st.markdown(f"![Generated Image]({img_url})")
        else:
            st.warning("提示词为空")

# --- 3. 主界面：内容编辑 ---
st.header("内容编辑")

st.subheader("🔥 实时全网热点")
if st.button("🔄 刷新实时热搜"):
    with st.spinner("同步数据中..."):
        headers = {'User-Agent': 'Mozilla/5.0'}
        # 尝试两个镜像接口以确保云端成功率
        urls = ["https://api.oick.cn/api/baidu", "https://tenapi.cn/v2/webhot"]
        success = False
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    # 统一存储数据 (包含标题和链接)
                    if "oick" in url:
                        st.session_state['news_cache'] = data[:10]
                    else:
                        st.session_state['news_cache'] = data['data'][:10]
                    success = True
                    break
            except: continue
        if success:
            st.toast("热点同步完成！", icon="✅")
        else:
            st.error("同步失败，请使用下方链接。")

st.divider()

# --- 核心：二选一展示逻辑 ---
if st.session_state['news_cache']:
    # 【情况 A】同步成功：展示热点按钮 + 原文链接
    st.caption("✅ 点击标题导入素材，点击 [原文] 跳转网页")
    for i, item in enumerate(st.session_state['news_cache']):
        title = item.get('title') or item.get('name')
        # 自动补全链接
        link = item.get('url') or f"https://www.baidu.com/s?wd={urllib.parse.quote(title)}"
        
        c_btn, c_link = st.columns([0.85, 0.15])
        if c_btn.button(f"📌 {title}", key=f"nb_{i}", use_container_width=True):
            st.session_state['input_cache'] = title
            st.rerun()
        c_link.link_button("原文 🔗", link)
    
    if st.button("🗑️ 清除热搜，回退到导航"):
        st.session_state['news_cache'] = []
        st.rerun()
else:
    # 【情况 B】未同步/同步失败：展示 6 个媒体导航
    st.info("💡 当前未同步热搜，建议前往以下信源：")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    c1.link_button("36氪科技", "https://36kr.com/technology")
    c2.link_button("IT之家", "https://www.ithome.com/")
    c3.link_button("汽车之家", "https://www.autohome.com.cn/")
    c4.link_button("虎扑热榜", "https://bbs.hupu.com/all-groot")
    c5.link_button("界面新闻", "https://www.jiemian.com/")
    c6.link_button("今日头条", "https://www.toutiao.com/")

st.divider()

# 编辑与生成区
raw_input = st.text_area("在此粘贴素材或编辑：", value=st.session_state['input_cache'], height=200)

if st.button("开始文章构思 🔥"):
    if not ds_key:
        st.error("请配置 API Key")
    elif not raw_input:
        st.warning("内容为空")
    else:
        client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
        try:
            with st.spinner("才思泉涌中..."):
                sys_msg = "你是一个顶级主编。风格犀利。结构：5个标题、引言、正文（加粗核心句）、总结。末