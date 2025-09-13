import streamlit as st
from agno.agent import Agent
from agno.models.google import Gemini

st.set_page_config(
    page_title="AI 健康与健身规划器",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
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
""", unsafe_allow_html=True)

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
            considerations = plan_content.get("important_considerations", "").split('\n')
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
            tips = plan_content.get("tips", "").split('\n')
            for tip in tips:
                if tip.strip():
                    st.info(tip)

def main():
    if 'dietary_plan' not in st.session_state:
        st.session_state.dietary_plan = {}
        st.session_state.fitness_plan = {}
        st.session_state.qa_pairs = []
        st.session_state.plans_generated = False

    st.title("🏋️‍♂️ AI 健康与健身规划器")
    st.markdown("""
        <div style='background-color: #00008B; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem;'>
        获取根据您的目标和偏好量身定制的个性化饮食和健身计划。
        我们由人工智能驱动的系统会考虑您的独特情况，为您创建完美的计划。
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("🔑 API 配置")
        gemini_api_key = st.text_input(
            "Gemini API 密钥",
            type="password",
            help="输入您的 Gemini API 密钥以访问服务"
        )
        
        if not gemini_api_key:
            st.warning("⚠️ 请输入您的 Gemini API 密钥以继续")
            st.markdown("[在此处获取您的 API 密钥](https://aistudio.google.com/apikey)")
            return
        
        st.success("API 密钥已接受！")

    if gemini_api_key:
        try:
            gemini_model = Gemini(id="gemini-1.5-flash-preview-0514", api_key=gemini_api_key)
        except Exception as e:
            st.error(f"❌ 初始化 Gemini 模型时出错: {e}")
            return

        st.header("👤 您的个人资料")
        
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("年龄", min_value=10, max_value=100, step=1, help="输入您的年龄")
            height = st.number_input("身高 (cm)", min_value=100.0, max_value=250.0, step=0.1)
            activity_level = st.selectbox(
                "活动水平",
                options=["久坐", "轻度活跃", "中度活跃", "非常活跃", "极度活跃"],
                help="选择您通常的活动水平"
            )
            dietary_preferences = st.selectbox(
                "饮食偏好",
                options=["素食", "生酮", "无麸质", "低碳水", "无乳制品"],
                help="选择您的饮食偏好"
            )

        with col2:
            weight = st.number_input("体重 (kg)", min_value=20.0, max_value=300.0, step=0.1)
            sex = st.selectbox("性别", options=["男性", "女性", "其他"])
            fitness_goals = st.selectbox(
                "健身目标",
                options=["减肥", "增肌", "耐力", "保持健康", "力量训练"],
                help="您想实现什么目标？"
            )

        if st.button("🎯 生成我的个性化计划", use_container_width=True):
            with st.spinner("正在为您创建完美的健康和健身日程..."):
                try:
                    dietary_agent = Agent(
                        name="饮食专家",
                        role="提供个性化饮食建议",
                        model=gemini_model,
                        instructions=[
                            "考虑用户的输入，包括饮食限制和偏好。",
                            "建议一天的详细膳食计划，包括早餐、午餐、晚餐和零食。",
                            "简要解释为什么该计划适合用户的目标。",
                            "注重建议的清晰性、连贯性和质量。",
                        ]
                    )

                    fitness_agent = Agent(
                        name="健身专家",
                        role="提供个性化健身建议",
                        model=gemini_model,
                        instructions=[
                            "提供根据用户目标量身定制的锻炼。",
                            "包括热身、主要锻炼和冷却运动。",
                            "解释每项推荐锻炼的好处。",
                            "确保计划具有可操作性和详细性。",
                        ]
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

                    dietary_plan_response = dietary_agent.run(user_profile)
                    dietary_plan = {
                        "why_this_plan_works": "高蛋白、健康脂肪、适量碳水化合物和热量平衡",
                        "meal_plan": dietary_plan_response.content,
                        "important_considerations": """
                        - 补水：全天多喝水
                        - 电解质：监测钠、钾和镁的水平
                        - 纤维：通过蔬菜和水果确保摄入足量
                        - 倾听身体的声音：根据需要调整份量
                        """
                    }

                    fitness_plan_response = fitness_agent.run(user_profile)
                    fitness_plan = {
                        "goals": "增强力量、提高耐力并保持整体健康",
                        "routine": fitness_plan_response.content,
                        "tips": """
                        - 定期跟踪您的进展
                        - 锻炼之间保证适当的休息
                        - 注重正确的姿势
                        - 坚持您的日常锻炼
                        """
                    }

                    st.session_state.dietary_plan = dietary_plan
                    st.session_state.fitness_plan = fitness_plan
                    st.session_state.plans_generated = True
                    st.session_state.qa_pairs = []

                    display_dietary_plan(dietary_plan)
                    display_fitness_plan(fitness_plan)

                except Exception as e:
                    st.error(f"❌ 发生错误: {e}")

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
                            agent = Agent(model=gemini_model, show_tool_calls=True, markdown=True)
                            run_response = agent.run(full_context)

                            if hasattr(run_response, 'content'):
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