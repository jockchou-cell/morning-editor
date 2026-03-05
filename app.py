import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

# 页面配置
st.set_page_config(page_title="朝起拾要·全能工作室", layout="wide", page_icon="☀️")

# --- 1. 初始化保险箱 ---
if 'article_cache' not in st.session_state:
    st.session_state['article_cache'] = ""
if 'news_cache' not in st.session_state:
    st.session_state['news_cache'] = []
if 'input_cache' not in st.session_state:
    st.session_state['input_cache'] = ""

# --- 2. 侧边栏：朝起拾要 ---
with st.sidebar:
    st.title("☀️ 朝起拾要")
    st.divider()
    
    ds_key = st.text_input("DeepSeek API Key", type="password")
    st.caption("提示：文案由 DeepSeek 驱动，出图已切换至加速通道。")
    
    st.divider()
    st.subheader("🖼️ 视觉实验室")
    img_mode = st.radio("获取方式", ["AI 快速出图", "搜索无版权图片"])
    
    if img_mode == "AI 快速出图":
        user_prompt = st.text_area("粘贴图片提示词 (英文)", placeholder="例如: Futuristic electric car, cyber style...")
        if st.button("立即出图 🎨"):
            if not user_prompt:
                st.warning("请先填入提示词")
            else:
                with st.spinner("AI 正在绘图..."):
                    # 使用加密和随机因子确保 100% 触发新图生成
                    clean_prompt = "".join(e for e in user_prompt if e.isalnum() or e == " ")
                    encoded = urllib.parse.quote(clean_prompt.strip())
                    seed = random.randint(1, 100000)
                    # 采用无需 Token 的高稳定性接口
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&nologo=true&seed={seed}&enhance=true"
                    st.image(img_url, caption="生成成功！右键可保存图片")
    else:
        st.info("💡 推荐图库直达：")
        st.link_button("Pixabay (全能)", "https://pixabay.com/")
        st.link_button("Pexels (高质)", "https://www.pexels.com/zh-cn/")

# --- 3. 主界面：内容编辑 ---
st.header("内容编辑")

# 热点展示区
st.subheader("🔥 实时热点速递")
if st.button("🔄 刷新实时热点"):
    with st.spinner("正在链接热搜数据源..."):
        try:
            # 伪装 Header 绕过部分接口拦截
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            # 尝试两个主流接口
            hot_url = "https://tenapi.cn/v2/webhot"
            resp = requests.get(hot_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                st.session_state['news_cache'] = [item['name'] for item in resp.json()['data'][:10]]
                st.success("同步成功！")
            else:
                st.session_state['news_cache'] = []
                st.error("接口繁忙，建议使用下方链接。")
        except:
            st.error("网络连接超时，请点击下方快捷链接手动获取。")

# 渲染热点按钮
if st.session_state['news_cache']:
    cols = st.columns(2)
    for i, n in enumerate(st.session_state['news_cache']):
        if cols[i % 2].button(f"📌 {n}", key=f"btn_{i}", use_container_width=True):
            st.session_state['input_cache'] = n
            st.rerun()
else:
    st.info("💡 建议前往以下网站摘取（最稳定、最真实）：")
    c1, c2, c3, c4 = st.columns(4)
    c1.link_button("36氪科技", "https://36kr.com/technology")
    c2.link_button("IT之家", "https://www.ithome.com/")
    c3.link_button("汽车之家", "https://www.autohome.com.cn/news/")
    c4.link_button("微博热搜", "https://s.weibo.com/top/summary")

st.divider()

# 编辑区 (绑定缓存)
raw_input = st.text_area("素材编辑：", value=st.session_state['input_cache'], height=200)

if st.button("一键生成公众号爆款文 🔥"):
    if not ds_key:
        st.error("请先在左侧填入 DeepSeek API Key")
    elif not raw_input:
        st.warning("内容为空，请输入素材。")
    else:
        client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
        try:
            with st.spinner("主编正在疯狂写作中..."):
                sys_msg = "你是一个10万粉科技主编。风格犀利口语化。结构：3个标题、引言、正文(分段+标题)、点评。500字以上。文末提供英文绘图词，格式：[IMG] 内容"
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": raw_input}]
                )
                st.session_state['article_cache'] = response.choices[0].message.content
        except Exception as e:
            st.error(f"生成失败：{e}")

# 显示文章
if st.session_state['article_cache']:
    st.markdown("---")
    st.subheader("📄 生成结果 (可直接全选复制)")
    st.markdown(st.session_state['article_cache'])