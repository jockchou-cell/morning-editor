import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

# 1. 页面配置：简约主题
st.set_page_config(page_title="朝起拾要·专业版", layout="wide", page_icon="📝")

# 强制简约样式：无背景色、统一边框
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 4px; border: 1px solid #d1d1d1; background-color: #ffffff; color: #333; transition: all 0.3s; }
    .stButton>button:hover { border-color: #000; background-color: #f8f9fa; }
    div[data-testid="stExpander"] { border: none; box-shadow: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心缓存与状态 ---
@st.cache_data(ttl=600)
def fetch_news_api():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # 使用对海外服务器响应较好的镜像源
        resp = requests.get("https://api.oick.cn/api/baidu", headers=headers, timeout=5)
        if resp.status_code == 200:
            return [item['title'] for item in resp.json()[:10]]
    except: return []
    return []

if 'article_cache' not in st.session_state: st.session_state['article_cache'] = ""
if 'news_list' not in st.session_state: st.session_state['news_list'] = []
if 'input_text' not in st.session_state: st.session_state['input_text'] = ""

# --- 3. 侧边栏：配置与出图 ---
with st.sidebar:
    st.title("朝起拾要")
    ds_key = st.secrets.get("ds_key")
    if ds_key: st.caption("系统：API 已就绪")
    else: ds_key = st.text_input("配置 API Key", type="password")
    
    st.divider()
    st.subheader("图像生成")
    img_prompt = st.text_area("提示词 (英文)", placeholder="输入图像描述...", height=100)
    if st.button("生成图片"):
        if img_prompt:
            with st.spinner("处理中..."):
                clean_p = "".join(e for e in img_prompt if e.isalnum() or e == " ")
                encoded = urllib.parse.quote(clean_p.strip())
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&nologo=true&seed={random.randint(1,999)}"
                st.image(img_url)
        else: st.warning("内容为空")

# --- 4. 主界面：1:1 对称布局 ---
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.subheader("素材与灵感")
    
    # 热点刷新部分
    if st.button("同步实时热点"):
        st.session_state['news_list'] = fetch_news_api()
    
    if st.session_state['news_list']:
        # 简约平铺按钮
        for i, news in enumerate(st.session_state['news_list']):
            if st.button(f" {news}", key=f"news_{i}"):
                st.session_state['input_text'] = news
                st.rerun()
    else:
        st.caption("点击上方按钮同步，或访问下方站点摘取：")
        c1, c2, c3 = st.columns(3)
        c1.link_button("36氪", "https://36kr.com/technology")
        c2.link_button("IT之家", "https://www.ithome.com/")
        c3.link_button("微博", "https://s.weibo.com/top/summary")

    st.divider()
    
    # 核心编辑区
    user_input = st.text_area("内容编辑", value=st.session_state['input_text'], height=300, placeholder="在此输入素材...")
    
    if st.button("开始文章构思"):
        if not ds_key: st.error("未配置 Key")
        elif not user_input: st.warning("请输入素材")
        else:
            client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
            # 交互增强：状态指示器
            with st.status("才思泉涌中...", expanded=True) as status:
                try:
                    st.write("正在研读素材...")
                    st.write("正在提炼爆款标题...")
                    st.write("正在组织深度论点...")
                    
                    sys_msg = "你是一个专业科技主编。风格犀利简约，拒绝废话。结构：5个备选标题、引言、正文（多段落加粗）、点评。800字左右。"
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_input}]
                    )
                    st.session_state['article_cache'] = response.choices[0].message.content
                    status.update(label="构思完成", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"连接失败: {e}")

with col_right:
    st.subheader("生成定稿")
    if st.session_state['article_cache']:
        # 简约结果展示
        st.markdown(st.session_state['article_cache'])
        
        st.divider()
        c_copy, c_clear = st.columns(2)
        # 一键复制功能（Streamlit 内置）
        c_copy.copy_to_clipboard(st.session_state['article_cache'], before_text="复制全文")
        if c_clear.button("清空结果"):
            st.session_state['article_cache'] = ""
            st.rerun()
    else:
        st.info("待左侧构思完成后，此处将显示定稿。")