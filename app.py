import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

# 1. 页面配置 & 样式优化
st.set_page_config(page_title="朝起拾要·爆文工作室", layout="wide", page_icon="🚀")

# 自定义 CSS 提升产品感
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #FF4B4B; color: white; }
    .stTextArea>div>div>textarea { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 缓存机制 (优化加载速度) ---
@st.cache_data(ttl=600) # 缓存10分钟
def get_hot_news_cached():
    headers = {'User-Agent': 'Mozilla/5.0'}
    urls = ["https://api.oick.cn/api/baidu", "https://tenapi.cn/v2/webhot"]
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [item.get('title') or item.get('name') for item in (data if isinstance(data, list) else data.get('data', []))[:10]]
        except: continue
    return []

# --- 3. 初始化保险箱 ---
for key in ['article_cache', 'news_cache', 'input_cache', 'titles_cache']:
    if key not in st.session_state: st.session_state[key] = "" if 'cache' in key else []

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("☀️ 朝起拾要 v4.0")
    ds_key = st.secrets.get("ds_key")
    if ds_key: st.success("✅ 云端引擎已就绪")
    else: ds_key = st.text_input("填入 API Key", type="password")
    
    st.divider()
    st.subheader("🖼️ AI 配图专家")
    user_prompt = st.text_area("图片描述 (自动优化)", placeholder="输入关键词...")
    if st.button("生成高清配图 🎨"):
        if user_prompt:
            seed = random.randint(1, 999999)
            img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(user_prompt)}?width=1024&height=512&seed={seed}&nologo=true"
            st.image(img_url)
            st.toast("图片已生成！", icon="🖼️")

# --- 5. 主界面布局 ---
col_l, col_r = st.columns([1, 1.5])

with col_l:
    st.subheader("🔥 灵感源泉")
    if st.button("🔄 刷新全网热点"):
        # 清除缓存强制刷新
        get_hot_news_cached.clear()
        st.session_state['news_cache'] = get_hot_news_cached()
    
    if not st.session_state['news_cache']:
        st.session_state['news_cache'] = get_hot_news_cached()

    for i, n in enumerate(st.session_state['news_cache']):
        if st.button(f"📌 {n}", key=f"n_{i}"):
            st.session_state['input_cache'] = n
            st.rerun()

with col_r:
    st.subheader("✍️ 创作空间")
    raw_input = st.text_area("输入素材或热点关键词：", value=st.session_state['input_cache'], height=150)
    
    if st.button("开始炼丹 (生成爆文) 🔥"):
        if not ds_key: st.error("请先配置 Key")
        elif not raw_input: st.warning("素材呢？")
        else:
            client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
            with st.status("正在进行深度创作...", expanded=True) as status:
                try:
                    st.write("🔍 正在分析热点背景...")
                    time.sleep(1)
                    st.write("🧠 正在构建爆款逻辑...")
                    
                    sys_msg = """你是一个顶级自媒体主编。
                    输出要求：
                    1. 给出5个极具点击欲望的[爆款标题]，包含Emoji。
                    2. 正文要求：[引言]、[深度分析](分段并加粗关键词)、[文末总结]。
                    3. 风格：犀利口语化，多用Emoji，适合手机阅读。
                    4. 长度：800字左右。"""
                    
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": raw_input}]
                    )
                    st.session_state['article_cache'] = res.choices[0].message.content
                    status.update(label="✅ 生成成功！", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"失败了：{e}")

    # 结果展示
    if st.session_state['article_cache']:
        st.divider()
        # 增加一键复制按钮
        st.copy_to_clipboard(st.session_state['article_cache'])
        st.info("👆 文章已自动进入剪贴板，可直接粘贴到公众号")
        
        st.markdown(st.session_state['article_cache'])
        
        if st.button("🗑️ 清空内容"):
            st.session_state['article_cache'] = ""
            st.rerun()