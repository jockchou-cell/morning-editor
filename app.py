import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

# 1. 页面配置：保持你喜欢的经典布局
st.set_page_config(page_title="朝起拾要·全能工作室", layout="wide", page_icon="☀️")

# --- 2. 初始化保险箱 (Session State) ---
if 'article_cache' not in st.session_state:
    st.session_state['article_cache'] = ""
if 'news_cache' not in st.session_state:
    st.session_state['news_cache'] = []
if 'input_cache' not in st.session_state:
    st.session_state['input_cache'] = ""

# --- 3. 侧边栏：朝起拾要 ---
with st.sidebar:
    st.title("☀️ 朝起拾要")
    st.divider()
    
    # 兼容性 Key 获取：优先从云端 Secrets 获取，本地失败则不报错
    try:
        ds_key = st.secrets["ds_key"]
        st.success("✅ DeepSeek API 已就绪")
    except:
        ds_key = st.text_input("DeepSeek API Key (本地运行请手动填入)", type="password")

    st.caption("核心模型：DeepSeek-V3 | 绘图引擎：Pollinations Cloud")
    
    st.divider()
    st.subheader("🖼️ 视觉实验室")
    
    # 极简出图逻辑
    user_prompt = st.text_area("粘贴图片提示词 (英文)", placeholder="例如: Cyberpunk electric car...")
    if st.button("立即出图 🎨"):
        if not user_prompt:
            st.warning("请填入提示词")
        else:
            with st.spinner("AI 正在云端渲染..."):
                clean_p = "".join(e for e in user_prompt if e.isalnum() or e == " ")
                encoded = urllib.parse.quote(clean_p.strip())
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&seed={random.randint(1,1000000)}&nologo=true"
                st.markdown(f"![Generated Image]({img_url})")
                st.caption("✨ 生成成功，长按或右键图片另存为。")

# --- 4. 主界面：内容编辑 ---
st.header("内容编辑")

# 热点展示区
st.subheader("🔥 实时全网热点")
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
                    st.session_state['news_cache'] = [item.get('title') or item.get('name') for item in (data if isinstance(data, list) else data.get('data', []))[:10]]
                    st.success("同步成功！")
                    success = True
                    break
            except: continue
        if not success: st.error("同步受限，请使用下方链接手动摘取。")

# 渲染热点按钮
if st.session_state['news_cache']:
    cols = st.columns(2)
    for i, n in enumerate(st.session_state['news_cache']):
        if cols[i % 2].button(f"📌 {n}", key=f"btn_{i}", use_container_width=True):
            st.session_state['input_cache'] = n
            st.rerun()
else:
    st.info("💡 建议前往信源摘取：")
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

if st.button("一键生成爆款文 🔥"):
    if not ds_key:
        st.error("请配置 API Key")
    elif not raw_input:
        st.warning("内容为空。")
    else:
        client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
        try:
            with st.spinner("才思泉涌中..."):
                sys_msg = """你是一个10万粉科技主编。风格犀利口语化。
                要求：5个爆款标题、引言、正文（多段落加粗）、总结。
                文末必须提供一个英文绘图提示词，格式如：[IMG_PROMPT]: 内容"""
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": raw_input}]
                )
                st.session_state['article_cache'] = response.choices[0].message.content
        except Exception as e: st.error(f"生成失败：{e}")

# --- 5. 展示结果：稳健的一键复制方案 ---
if st.session_state['article_cache']:
    st.markdown("---")
    st.subheader("📄 生成结果 (点击右上角复制)")
    
    # 【核心修正】使用 st.code 替代崩溃的 copy_to_clipboard
    # st.code 自带官方原生的复制按钮，绝对不会报错
    st.code(st.session_state['article_cache'], language="markdown")
    
    # 底部内容展示
    st.markdown(st.session_state['article_cache'])
    
    if st.button("🗑️ 清空结果"):
        st.session_state['article_cache'] = ""
        st.rerun()