import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

# 1. 页面配置
st.set_page_config(page_title="朝起拾要·专业版", layout="wide", page_icon="📝")

# 简约样式
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 4px; border: 1px solid #e0e0e0; background-color: #ffffff; color: #333; }
    .stButton>button:hover { border-color: #000; background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 状态初始化 ---
if 'article_cache' not in st.session_state: st.session_state['article_cache'] = ""
if 'news_list' not in st.session_state: st.session_state['news_list'] = []
if 'input_text' not in st.session_state: st.session_state['input_text'] = ""

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("朝起拾要")
    ds_key = st.secrets.get("ds_key")
    if ds_key: st.caption("✅ API 状态：就绪")
    else: ds_key = st.text_input("填入 API Key", type="password")
    
    st.divider()
    st.subheader("辅助出图")
    img_prompt = st.text_area("提示词 (英文)", placeholder="描述你想要的画面...", height=100)
    if st.button("生成图片"):
        if img_prompt:
            with st.spinner("处理中..."):
                encoded = urllib.parse.quote(img_prompt.strip())
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&nologo=true&seed={random.randint(1,999)}"
                st.image(img_url)

# --- 4. 主界面：1:1 对称布局 ---
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.subheader("灵感素材")
    
    # 6个可选新闻链接 (对称排列)
    st.caption("手动摘取信源：")
    link_cols = st.columns(3)
    link_cols[0].link_button("36氪科技", "https://36kr.com/technology")
    link_cols[1].link_button("汽车之家", "https://www.autohome.com.cn/")
    link_cols[2].link_button("IT之家", "https://www.ithome.com/")
    link_cols[0].link_button("虎扑热帖", "https://bbs.hupu.com/all-groot")
    link_cols[1].link_button("界面新闻", "https://www.jiemian.com/")
    link_cols[2].link_button("头条热点", "https://www.toutiao.com/")

    if st.button("同步实时热点"):
        try:
            resp = requests.get("https://api.oick.cn/api/baidu", timeout=5)
            if resp.status_code == 200:
                st.session_state['news_list'] = [item['title'] for item in resp.json()[:10]]
        except: st.error("网络波动，请点击上方链接手动摘取")
    
    if st.session_state['news_list']:
        for i, news in enumerate(st.session_state['news_list']):
            if st.button(f"📌 {news}", key=f"news_{i}"):
                st.session_state['input_text'] = news
                st.rerun()

    st.divider()
    user_input = st.text_area("素材编辑区", value=st.session_state['input_text'], height=250)
    
    if st.button("开始文章构思"):
        if not ds_key: st.error("缺少 API Key")
        elif not user_input: st.warning("素材为空")
        else:
            client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
            with st.status("才思泉涌中...", expanded=True) as status:
                try:
                    st.write("研读素材中...")
                    st.write("提炼标题中...")
                    sys_msg = "你是一个专业主编。风格犀利简约。结构：5个备选标题、引言、正文（多段落加粗关键句）、点评。800字左右。"
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_input}]
                    )
                    st.session_state['article_cache'] = response.choices[0].message.content
                    status.update(label="构思完成", state="complete", expanded=False)
                except Exception as e: st.error(f"失败: {e}")

with col_right:
    st.subheader("定稿展示")
    if st.session_state['article_cache']:
        # 使用 code 块包裹文章，方便用户一键点击右上角复制，且绝不报错
        st.code(st.session_state['article_cache'], language="markdown")
        
        # 正常预览
        st.markdown("---")
        st.markdown(st.session_state['article_cache'])
        
        if st.button("清空当前内容"):
            st.session_state['article_cache'] = ""
            st.rerun()
    else:
        st.info("构思完成后，定稿将在此处呈现。")