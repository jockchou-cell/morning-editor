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
    
    # 智能 Key 检测逻辑
    ds_key = st.secrets.get("ds_key")
    if ds_key:
        st.success("✅ DeepSeek API 已就绪")
    else:
        ds_key = st.text_input("DeepSeek API Key", type="password")
        st.warning("⚠️ 请在云端 Secrets 配置 ds_key")

    st.caption("AI 驱动：DeepSeek-V3 | 绘图引擎：Pollinations AI")
    
    st.divider()
    st.subheader("🖼️ 视觉实验室")
    img_mode = st.radio("获取方式", ["AI 快速出图", "搜索无版权图片"])
    
    if img_mode == "AI 快速出图":
        user_prompt = st.text_area("粘贴图片提示词 (英文)", placeholder="例如: Cyberpunk style car, future city...")
        if st.button("立即出图 🎨"):
            if not user_prompt:
                st.warning("请填入提示词")
            else:
                with st.spinner("AI 正在云端绘图，请稍候..."):
                    # 彻底清洗提示词
                    clean_prompt = "".join(e for e in user_prompt if e.isalnum() or e == " ")
                    encoded = urllib.parse.quote(clean_prompt.strip())
                    # 关键修复：加入更强的随机随机种子防止缓存 404
                    seed = random.randint(1, 999999)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&seed={seed}&nologo=true&enhance=true"
                    # 使用 markdown 方式渲染图片，提高在部分浏览器下的兼容性
                    st.image(img_url, caption=f"生成成功 (Seed: {seed})", use_container_width=True)
    else:
        st.link_button("Pixabay (全能图库)", "https://pixabay.com/")
        st.link_button("Pexels (高质量素材)", "https://www.pexels.com/zh-cn/")

# --- 3. 主界面：内容编辑 ---
st.header("内容编辑")

# 热点展示区
st.subheader("🔥 实时全网热搜")
if st.button("🔄 刷新实时热点"):
    with st.spinner("正在通过备用节点同步..."):
        # 接口轮询逻辑
        api_endpoints = [
            "https://tenapi.cn/v2/webhot",
            "https://api.oioweb.cn/api/common/fetch_hot_v1"
        ]
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        success = False
        
        for url in api_endpoints:
            try:
                resp = requests.get(url, headers=headers, timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    if "tenapi" in url:
                        st.session_state['news_cache'] = [item['name'] for item in data['data'][:10]]
                    else:
                        st.session_state['news_cache'] = [item['title'] for item in data['result']['items'][:10]]
                    st.success(f"同步成功 (源: {url.split('/')[2]})")
                    success = True
                    break
            except:
                continue
        
        if not success:
            st.error("云端服务器访问受阻，请直接点击下方链接手动摘取。")

# 渲染按钮
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

# 编辑区
raw_input = st.text_area("在此输入素材或编辑文章：", value=st.session_state['input_cache'], height=250)

if st.button("一键生成公众号爆款文 🔥"):
    if not ds_key:
        st.error("请先在左侧配置 API Key")
    elif not raw_input:
        st.warning("素材内容为空。")
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
                st.success("🎉 生成完毕！")
        except Exception as e:
            st.error(f"生成失败：{e}")

# 显示文章
if st.session_state['article_cache']:
    st.markdown("---")
    st.subheader("📄 最终定稿 (可直接全选复制)")
    st.markdown(st.session_state['article_cache'])