import streamlit as st
import logging
import traceback
from datetime import datetime
from phi.agent import Agent
from phi.model.google import Gemini
from phi.model.openai import OpenAIChat

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
st.set_page_config(
    page_title="AI 健康与健身规划器",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0fff4;
        border: 1px solid #9ae6b4;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fffaf0;
        border: 1px solid #fbd38d;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def display_dietary_plan(plan_content):
    with st.expander("📋 您的个性化饮食计划", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 🎯 为什么这个计划有效")
            st.info(plan_content.get("why_this_plan_works", "信息不可用"))
            st.markdown("### 🍽️ 膳食计划")
            st.write(plan_content.get("meal_plan", "计划不可用"))

        with col2:
            st.markdown("### ⚠️ 重要注意事项")
            considerations = plan_content.get("important_considerations", "").split(
                "\n"
            )
            for consideration in considerations:
                if consideration.strip():
                    st.warning(consideration)


def display_fitness_plan(plan_content):
    with st.expander("💪 您的个性化健身计划", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 🎯 目标")
            st.success(plan_content.get("goals", "未指定目标"))
            st.markdown("### 🏋️‍♂️ 锻炼日程")
            st.write(plan_content.get("routine", "日程不可用"))

        with col2:
            st.markdown("### 💡 专业提示")
            tips = plan_content.get("tips", "").split("\n")
            for tip in tips:
                if tip.strip():
                    st.info(tip)


def main():
    # 应用启动日志
    startup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"AI 健康与健身规划器启动 - 时间: {startup_time}")

    if "dietary_plan" not in st.session_state:
        st.session_state.dietary_plan = {}
        st.session_state.fitness_plan = {}
        st.session_state.qa_pairs = []
        st.session_state.plans_generated = False
        logging.info("会话状态初始化完成")

    st.title("🏋️‍♂️ AI 健康与健身规划器")
    st.markdown(
        """
        <div style='background-color: #00008B; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem;'>
        获取根据您的目标和偏好量身定制的个性化饮食和健身计划。
        我们由人工智能驱动的系统会考虑您的独特情况，为您创建完美的计划。
        </div>
    """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("🔑 模型配置")

        # 模型提供商选择
        model_provider = st.selectbox(
            "选择模型提供商",
            options=["Gemini", "OpenAI"],
            help="选择您要使用的 AI 模型提供商",
        )

        if model_provider == "Gemini":
            st.subheader("🤖 Gemini 配置")
            gemini_api_key = st.text_input(
                "Gemini API 密钥", type="password", help="输入您的 Gemini API 密钥"
            )
            gemini_model_name = st.selectbox(
                "Gemini 模型",
                options=[
                    "gemini-2.5-flash-preview-05-20",
                    "gemini-1.5-pro",
                    "gemini-1.5-flash",
                    "gemini-pro",
                ],
                help="选择要使用的 Gemini 模型",
            )

            if not gemini_api_key:
                st.warning("⚠️ 请输入您的 Gemini API 密钥以继续")
                st.markdown(
                    "[在此处获取您的 API 密钥](https://aistudio.google.com/apikey)"
                )
                return

        elif model_provider == "OpenAI":
            st.subheader("🤖 OpenAI 配置")
            openai_api_key = st.text_input(
                "OpenAI API 密钥", type="password", help="输入您的 OpenAI API 密钥"
            )
            openai_base_url = st.text_input(
                "API Base URL", value="https://api.openai.com/v1", help="API URL"
            )
            openai_model_name = st.selectbox(
                "OpenAI 模型",
                options=[
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo",
                    "deepseek-v3",
                    "glm",
                ],
                help="选择要使用的 OpenAI 模型",
            )
            if openai_model_name == "deepseek-v3":
                openai_model_name = "deepseek-v3-241226-volces"
            elif openai_model_name == "glm":
                openai_model_name = "glm-4-flash"

            if not openai_api_key:
                st.warning("⚠️ 请输入您的 OpenAI API 密钥以继续")
                st.markdown(
                    "[在此处获取您的 API 密钥](https://platform.openai.com/api-keys)"
                )
                return

        st.success(f"✅ {model_provider} 配置完成！")

    # 初始化选定的模型
    model = None
    try:
        if model_provider == "Gemini":
            logging.info(f"开始初始化 Gemini 模型: {gemini_model_name}")
            st.info(f"正在初始化 Gemini 模型: {gemini_model_name}")
            model = Gemini(id=gemini_model_name, api_key=gemini_api_key)
            logging.info("Gemini 模型初始化成功")
        elif model_provider == "OpenAI":
            logging.info(f"开始初始化 OpenAI 兼容模型")
            logging.info(f"模型名称: {openai_model_name}")
            logging.info(f"Base URL: {openai_base_url}")
            logging.info(f"API Key 前缀: {openai_api_key[:10]}...")

            st.info(f"正在初始化 OpenAI 兼容模型: {openai_model_name}")
            st.info(f"使用 Base URL: {openai_base_url}")

            # 清理 base_url（移除 @ 符号）
            clean_base_url = openai_base_url.strip().replace("@", "")
            if not clean_base_url.endswith("/"):
                clean_base_url += "/"

            # 使用标准 OpenAIChat（兼容性修复已通过 deepseek_fix 模块自动应用）
            model = OpenAIChat(
                id=openai_model_name,
                api_key=openai_api_key,
                base_url=clean_base_url,
                max_tokens=2000,
                temperature=0.7,
            )
            logging.info("OpenAI 兼容模型初始化成功")

            # 添加 API 测试按钮
            if st.button("🧪 测试 API 连接", key="test_api"):
                with st.spinner("正在测试 API 连接..."):
                    try:
                        # 创建一个简单的测试 agent
                        test_agent = Agent(
                            name="测试助手",
                            model=model,
                            instructions=["简短回复测试消息"],
                        )
                        test_response = test_agent.run("Hello, this is a test.")

                        if test_response and hasattr(test_response, "content"):
                            st.success("✅ API 连接测试成功!")
                            st.info(f"测试响应: {test_response.content[:100]}...")
                        else:
                            st.error("❌ API 连接测试失败：响应为空")
                    except Exception as test_e:
                        st.error(f"❌ API 连接测试失败: {test_e}")

            st.info("正在验证模型配置...")

    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()

        # 详细日志记录
        logging.error(f"模型初始化失败 - 提供商: {model_provider}")
        logging.error(f"错误信息: {error_msg}")
        logging.error(f"完整堆栈跟踪:\n{error_traceback}")

        st.error(f"❌ 初始化 {model_provider} 模型时出错:")
        st.error(f"错误详情: {error_msg}")

        # 在界面上显示详细错误信息
        with st.expander("🔍 详细错误信息（用于调试）", expanded=False):
            st.code(error_traceback)

        # 提供针对性的解决建议
        if "400" in error_msg or "InvalidRequest" in error_msg:
            st.warning("**可能的解决方案:**")
            st.markdown(
                """
            - ✅ 检查 API Key 格式是否正确
            - ✅ 确认 Base URL 格式正确（不要包含 @ 符号）
            - ✅ 验证模型名称是否被 API 提供商支持
            - ✅ 确保 API Key 有足够的权限和余额
            """
            )
        elif "ModuleNotFoundError" in error_msg:
            st.warning("**依赖包缺失:**")
            st.markdown("请安装缺失的依赖包：`pip install -r requirements.txt`")
        return

    if not model:
        print(f"error model: {model}")
        st.error(f"❌ 无法初始化 {model_provider} 模型")
        return

    st.header("👤 您的个人资料")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input(
            "年龄", min_value=10, max_value=100, step=1, help="输入您的年龄"
        )
        height = st.number_input(
            "身高 (cm)", min_value=100.0, max_value=250.0, step=0.1
        )
        activity_level = st.selectbox(
            "活动水平",
            options=["久坐", "轻度活跃", "中度活跃", "非常活跃", "极度活跃"],
            help="选择您通常的活动水平",
        )
        dietary_preferences = st.selectbox(
            "饮食偏好",
            options=["素食", "生酮", "无麸质", "低碳水", "无乳制品"],
            help="选择您的饮食偏好",
        )

    with col2:
        weight = st.number_input("体重 (kg)", min_value=20.0, max_value=300.0, step=0.1)
        sex = st.selectbox("性别", options=["男性", "女性", "其他"])
        fitness_goals = st.selectbox(
            "健身目标",
            options=["减肥", "增肌", "耐力", "保持健康", "力量训练"],
            help="您想实现什么目标？",
        )

    if st.button("🎯 生成我的个性化计划", use_container_width=True):
        with st.spinner("正在为您创建完美的健康和健身日程..."):
            try:
                dietary_agent = Agent(
                    name="饮食专家",
                    model=model,
                    # 使用 system_prompt 而不是 instructions 和 role
                    system_prompt="""你是一位专业的饮食专家。请根据用户的个人信息提供个性化饮食建议：
                    - 考虑用户的输入，包括饮食限制和偏好
                    - 建议一天的详细膳食计划，包括早餐、午餐、晚餐和零食
                    - 简要解释为什么该计划适合用户的目标
                    - 注重建议的清晰性、连贯性和质量
                    请用中文回复。""",
                )

                fitness_agent = Agent(
                    name="健身专家",
                    model=model,
                    # 使用 system_prompt 而不是 instructions 和 role
                    system_prompt="""你是一位专业的健身专家。请根据用户的个人信息提供个性化健身建议：
                    - 提供根据用户目标量身定制的锻炼计划
                    - 包括热身、主要锻炼和冷却运动
                    - 解释每项推荐锻炼的好处
                    - 确保计划具有可操作性和详细性
                    请用中文回复。""",
                )

                user_profile = f"""
                年龄: {age}
                体重: {weight}kg
                身高: {height}cm
                性别: {sex}
                活动水平: {activity_level}
                饮食偏好: {dietary_preferences}
                健身目标: {fitness_goals}
                """

                # 生成饮食计划
                st.info("🍽️ 正在生成个性化饮食计划...")
                dietary_plan_response = dietary_agent.run(user_profile)

                if not dietary_plan_response or not hasattr(
                    dietary_plan_response, "content"
                ):
                    raise Exception("饮食计划生成失败，API 响应为空")

                dietary_plan = {
                    "why_this_plan_works": "高蛋白、健康脂肪、适量碳水化合物和热量平衡",
                    "meal_plan": dietary_plan_response.content,
                    "important_considerations": """
                    - 补水：全天多喝水
                    - 电解质：监测钠、钾和镁的水平
                    - 纤维：通过蔬菜和水果确保摄入足量
                    - 倾听身体的声音：根据需要调整份量
                    """,
                }

                # 生成健身计划
                st.info("💪 正在生成个性化健身计划...")
                fitness_plan_response = fitness_agent.run(user_profile)

                if not fitness_plan_response or not hasattr(
                    fitness_plan_response, "content"
                ):
                    raise Exception("健身计划生成失败，API 响应为空")

                fitness_plan = {
                    "goals": "增强力量、提高耐力并保持整体健康",
                    "routine": fitness_plan_response.content,
                    "tips": """
                    - 定期跟踪您的进展
                    - 锻炼之间保证适当的休息
                    - 注重正确的姿势
                    - 坚持您的日常锻炼
                    """,
                }

                st.session_state.dietary_plan = dietary_plan
                st.session_state.fitness_plan = fitness_plan
                st.session_state.plans_generated = True
                st.session_state.qa_pairs = []

                display_dietary_plan(dietary_plan)
                display_fitness_plan(fitness_plan)

            except Exception as e:
                error_msg = str(e)
                error_traceback = traceback.format_exc()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 详细日志记录
                logging.error(f"计划生成失败 - 时间: {timestamp}")
                logging.error(
                    f"用户配置: 年龄={age}, 体重={weight}, 身高={height}, 性别={sex}"
                )
                logging.error(f"错误信息: {error_msg}")
                logging.error(f"完整堆栈跟踪:\n{error_traceback}")

                st.error(f"❌ 生成计划时发生错误:")
                st.error(f"错误详情: {error_msg}")

                # 在界面上显示详细错误信息
                with st.expander("🔍 详细错误信息（用于调试）", expanded=False):
                    st.code(error_traceback)
                    st.markdown(f"**时间戳:** {timestamp}")
                    st.markdown(
                        f"**用户配置:** 年龄={age}, 体重={weight}, 身高={height}, 性别={sex}"
                    )

                # 根据错误类型提供具体的解决建议
                if "400" in error_msg or "InvalidRequest" in error_msg:
                    st.warning("**API 请求错误 - 可能的解决方案:**")
                    st.markdown(
                        """
                    1. **检查 API 配置:**
                       - API Key 格式: `sk-IGCVhvUquxeZLQWHCuot6s6LLxyZ`
                       - Base URL: `https://model.in.zhihu.com/v1` (不要包含 @ 符号)
                       - 模型名称: `deepseek-v3-241226-volces`
                    
                    2. **验证 API 服务:**
                       - 确认 API 服务可用
                       - 检查 API Key 是否有效且有足够余额
                       - 验证模型名称是否正确
                    
                    3. **网络连接:**
                       - 检查网络连接是否正常
                       - 确认防火墙没有阻止请求
                    """
                    )
                elif (
                    "timeout" in error_msg.lower() or "connection" in error_msg.lower()
                ):
                    st.warning("**网络连接问题 - 解决方案:**")
                    st.markdown(
                        "- 检查网络连接\n- 尝试重新运行\n- 确认 API 服务地址正确"
                    )
                else:
                    st.warning("**通用解决方案:**")
                    st.markdown(
                        "- 检查所有配置参数\n- 重新启动应用\n- 联系 API 提供商确认服务状态"
                    )

                # 记录详细错误到日志文件
                try:
                    with open("logs", "a", encoding="utf-8") as f:
                        f.write(f"\n[{timestamp}] 计划生成错误: {error_msg}\n")
                        f.write(f"堆栈跟踪: {error_traceback}\n")
                        f.write("-" * 50 + "\n")
                except Exception as log_error:
                    logging.error(f"写入日志文件失败: {log_error}")

    if st.session_state.plans_generated:
        st.header("❓ 对您的计划有疑问吗？")
        question_input = st.text_input("您想知道什么？")

        if st.button("获取答案"):
            if question_input:
                with st.spinner("正在为您寻找最佳答案..."):
                    dietary_plan = st.session_state.dietary_plan
                    fitness_plan = st.session_state.fitness_plan

                    context = f"饮食计划: {dietary_plan.get('meal_plan', '')}\n\n健身计划: {fitness_plan.get('routine', '')}"
                    full_context = f"{context}\n用户问题: {question_input}"

                    try:
                        agent = Agent(
                            model=model,
                            system_prompt="你是一位健康和健身专家。请根据提供的饮食和健身计划回答用户的问题。用中文回复。",
                        )
                        run_response = agent.run(full_context)

                        if hasattr(run_response, "content"):
                            answer = run_response.content
                        else:
                            answer = "抱歉，目前无法生成回应。"

                        st.session_state.qa_pairs.append((question_input, answer))
                    except Exception as e:
                        st.error(f"❌ 获取答案时发生错误: {e}")

        if st.session_state.qa_pairs:
            st.header("💬 问答历史")
            for question, answer in st.session_state.qa_pairs:
                st.markdown(f"**问:** {question}")
                st.markdown(f"**答:** {answer}")


if __name__ == "__main__":
    main()
