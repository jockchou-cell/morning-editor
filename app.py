import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

# 1. 页面配置
st.set_page_config(page_title="朝起拾要·专业版", layout="wide", page_icon="📝")

# 简约 CSS：保持对称美感与纯净界面
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 4px; border: 1px solid #e0e0e0; background-color: #ffffff; color: #333; height: 45px; }
    .stButton>button:hover { border-color: #000; background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 初始化缓存 ---
if 'article_cache' not in st.session_state: st.session_state['article_cache'] = ""
if 'news_list' not in st.session_state: st.session_state['news_list'] = []
if 'input_text' not in st.session_state: st.session_state['input_text'] = ""

# --- 3. 侧边栏：极简出图 ---
with st.sidebar:
    st.title("朝起拾要")
    ds_key = st.secrets.get("ds_key")
    if ds_key: st.success("✅ 云端引擎已连接")
    else: ds_key = st.text_input("配置 Key", type="password")
    
    st.divider()
    st.subheader("图像实验室")
    img_prompt_input = st.text_area("粘贴下方生成的提示词", placeholder="Prompt goes here...", height=100)
    if st.button("立即出图 🖼️"):
        if img_prompt_input:
            with st.spinner("正在绘制..."):
                clean_p = "".join(e for e in img_prompt_input if e.isalnum() or e == " ")
                encoded = urllib.parse.quote(clean_p.strip())
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&nologo=true&seed={random.randint(1,9999)}"
                st.image(img_url, caption="生成完毕，右键另存为")
        else: st.warning("请填入提示词")

# --- 4. 主界面：1:1 对称布局 ---
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.subheader("素材灵感")
    
    # 对称分布的 6 个信源链接
    st.caption("全网热点直达：")
    l_c1, l_c2, l_c3 = st.columns(3)
    l_c1.link_button("36氪科技", "https://36kr.com/technology")
    l_c2.link_button("汽车之家", "https://www.autohome.com.cn/")
    l_c3.link_button("IT之家", "https://www.ithome.com/")
    l_c1.link_button("虎扑热点", "https://bbs.hupu.com/all-groot")
    l_c2.link_button("界面新闻", "https://www.jiemian.com/")
    l_c3.link_button("头条热搜", "https://www.toutiao.com/")

    if st.button("🔄 同步实时热榜"):
        try:
            resp = requests.get("https://api.oick.cn/api/baidu", timeout=5)
            if resp.status_code == 200:
                st.session_state['news_list'] = [item['title'] for item in resp.json()[:10]]
        except: st.error("接口繁忙，请直接点击上方链接手动摘取")
    
    if st.session_state['news_list']:
        for i, news in enumerate(st.session_state['news_list']):
            if st.button(f"📌 {news}", key=f"news_{i}"):
                st.session_state['input_text'] = news
                st.rerun()

    st.divider()
    # 编辑区
    user_input = st.text_area("内容编辑", value=st.session_state['input_text'], height=250)
    
    if st.button("开始文章构思 🔥"):
        if not ds_key: st.error("请配置 Key")
        elif not user_input: st.warning("素材内容为空")
        else:
            client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
            with st.status("才思泉涌中...", expanded=True) as status:
                try:
                    st.write("正在研读素材...")
                    # 调优后的 Prompt：强制输出图片提示词
                    sys_msg = """你是一个顶级科技主编。风格犀利、多用加粗和短句。
                    结构：5个爆款标题、引言、正文（多段落分明并加粗核心句）、总结。
                    最后必须单独输出一行：[IMG_PROMPT]: 对应的英文绘图词"""
                    
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_input}]
                    )
                    st.session_state['article_cache'] = response.choices[0].message.content
                    status.update(label="构思完成", state="complete", expanded=False)
                except Exception as e: st.error(f"生成中断: {e}")

with col_right:
    st.subheader("定稿预览")
    if st.session_state['article_cache']:
        # 结果容器：使用 textarea 模拟“一键复制”体验，不仅稳定且点击即选中
        st.text_area("以下内容可直接全选复制：", 
                     value=st.session_state['article_cache'], 
                     height=450, 
                     help="点击框内按 Ctrl+A 全选，Ctrl+C 复制")
        
        st.divider()
        if st.button("🗑️ 清空当前内容"):
            st.session_state['article_cache'] = ""
            st.rerun()
        
        # 底部 Markdown 实时渲染，方便检查格式
        st.markdown(st.session_state['article_cache'])
    else:
        st.info("待左侧构思完成后，文章与绘图词将在此呈现。")