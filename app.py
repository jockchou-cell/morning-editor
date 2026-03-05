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
    
    # --- 智能 Key 检测逻辑 ---
    # 尝试从 Secrets 获取 ds_key
    ds_key = st.secrets.get("ds_key")
    
    if ds_key:
        st.success("✅ DeepSeek API 已自动配置")
    else:
        # 如果 Secret 没配置，则显示输入框
        ds_key = st.text_input("DeepSeek API Key", type="password", help="本地运行时请手动填入")
        st.warning("⚠️ 未检测到云端 Secret 配置")

    st.caption("文案由 DeepSeek 驱动 | 出图已接入全球加速通道")
    
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
                    # 彻底清洗提示词，防止特殊字符导致 URL 损坏
                    clean_prompt = "".join(e for e in user_prompt if e.isalnum() or e == " ")
                    encoded = urllib.parse.quote(clean_prompt.strip())
                    seed = random.randint(1, 100000)
                    # 采用高可用 Pollinations 接口
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&nologo=true&seed={seed}&enhance=true"
                    st.image(img_url, caption="AI 生成预览 (右键可保存图片)")
    else:
        st.info("💡 推荐图库直达：")
        st.link_button("Pixabay (全能图库)", "https://pixabay.com/")
        st.link_button("Pexels (高质量素材)", "https://www.pexels.com/zh-cn/")

# --- 3. 主界面：内容编辑 ---
st.header("内容编辑")

# 热点展示区
st.subheader("🔥 实时全网热搜")
if st.button("🔄 刷新实时热点"):
    with st.spinner("正在通过云端镜像同步数据..."):
        try:
            # 使用更稳健的浏览器伪装头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            }
            # 采用国内直连成功率最高的公共接口
            hot_url = "https://tenapi.cn/v2/webhot"
            resp = requests.get(hot_url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                if data:
                    st.session_state['news_cache'] = [item['name'] for item in data[:10]]
                    st.success("数据同步成功！")
                else:
                    st.error("接口返回数据为空，请手动摘取")
            else:
                st.error(f"接口限流 (状态码:{resp.status_code})，请尝试手动摘取。")
        except Exception as e:
            st.error("网络连接超时，请直接点击下方按钮前往主流媒体。")

# 渲染热点按钮
if st.session_state['news_cache']:
    cols = st.columns(2)
    for i, n in enumerate(st.session_state['news_cache']):
        # 点击按钮将内容存入缓存并强制刷新
        if cols[i % 2].button(f"📌 {n}", key=f"btn_{i}", use_container_width=True):
            st.session_state['input_cache'] = n
            st.rerun()
else:
    st.info("💡 实时同步受限，建议前往以下网站摘取（最稳定、最真实）：")
    c1, c2, c3, c4 = st.columns(4)
    c1.link_button("36氪科技", "https://36kr.com/technology")
    c2.link_button("IT之家", "https://www.ithome.com/")
    c3.link_button("汽车之家", "https://www.autohome.com.cn/news/")
    c4.link_button("微博热搜", "https://s.weibo.com/top/summary")

st.divider()

# 编辑区 (绑定缓存，确保刷新不出错)
raw_input = st.text_area("在此输入素材或编辑文章：", value=st.session_state['input_cache'], height=250)

if st.button("一键生成公众号爆款文 🔥"):
    if not ds_key:
        st.error("请先在左侧填入或配置 DeepSeek API Key")
    elif not raw_input:
        st.warning("素材内容为空，主编没法凭空捏造呀。")
    else:
        client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
        try:
            with st.spinner("主编正在构思爆款金句..."):
                sys_msg = """你是一个10万粉科技/汽车主编。
                要求：
                1. 风格：犀利、口语化、短句多。拒绝AI味。
                2. 结构：3个备选标题、[引言]、[正文](分段+标题)、[总结点评]。
                3. 长度：必须500字以上，内容详实。
                4. 文末提供IMAGE_PROMPT: [英文绘图描述词]。"""
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": raw_input}]
                )
                # 写入缓存锁，防止出图刷新消失
                st.session_state['article_cache'] = response.choices[0].message.content
                st.success("🎉 文章生成完毕！")
        except Exception as e:
            st.error(f"生成失败：{e}")

# --- 文章展示区 (始终从缓存中读取，不受侧边栏操作影响) ---
if st.session_state['article_cache']:
    st.markdown("---")
    st.subheader("📄 最终定稿 (可全选复制)")
    st.markdown(st.session_state['article_cache'])
    
    if st.button("🗑️ 清空当前定稿"):
        st.session_state['article_cache'] = ""
        st.rerun()