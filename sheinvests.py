import streamlit as st
from groq import Groq
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# --- Page Setup ---
st.set_page_config(page_title="SheInvests", page_icon="💰", layout="centered")

st.title("💰 SheInvests")
st.write("Your beginner friendly AI stock market guide!")
st.caption("Made by Twisha Jain")

# --- API Key ---
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.warning("GROQ_API_KEY is missing. Add it to .streamlit/secrets.toml.")
client = Groq(api_key=api_key) if api_key else None

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Stock Analyzer",
    "📚 Learn Terms",
    "💵 Investment Simulator",
    "🧠 Quiz"
])

# =====================
# TAB 1 - STOCK ANALYZER
# =====================
with tab1:
    st.header("📈 Analyze Any Stock")
    st.write("Type a stock symbol to get a beginner friendly analysis!")

    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("Stock Symbol",
                  placeholder="e.g. AAPL, RELIANCE.NS, TCS.NS")
    with col2:
        period = st.selectbox("Time Period", [
            "1mo", "3mo", "6mo", "1y"
        ], format_func=lambda x: {
            "1mo": "1 Month",
            "3mo": "3 Months",
            "6mo": "6 Months",
            "1y": "1 Year"
        }[x])

    if st.button("🔍 Analyze Stock", key="analyze"):
        if not ticker:
            st.warning("Please enter a stock symbol!")
        else:
            with st.spinner(f"Fetching data for {ticker.upper()}..."):
                try:
                    stock = yf.Ticker(ticker.upper())
                    hist = stock.history(period=period)
                    info = stock.info

                    if hist.empty:
                        st.error("Stock not found! Check the symbol and try again.")
                    else:
                        # --- Basic Info ---
                        name = info.get("longName", ticker.upper())
                        current_price = hist["Close"].iloc[-1]
                        start_price = hist["Close"].iloc[0]
                        change = ((current_price - start_price) / start_price) * 100
                        currency = info.get("currency", "USD")

                        st.markdown("---")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Company", name)
                        col2.metric("Current Price",
                                   f"{currency} {current_price:.2f}")
                        col3.metric("Change",
                                   f"{change:.2f}%",
                                   delta=f"{change:.2f}%")

                        # --- Chart ---
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=hist.index,
                            y=hist["Close"],
                            mode="lines",
                            name="Price",
                            line=dict(color="purple", width=2)
                        ))
                        fig.update_layout(
                            title=f"{name} Stock Price",
                            xaxis_title="Date",
                            yaxis_title=f"Price ({currency})",
                            template="plotly_white",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # --- AI Explanation ---
                        with st.spinner("AI is explaining this stock for you..."):
                            prompt = f"""
                            You are a friendly financial advisor explaining stocks 
                            to a woman who is completely new to investing.
                            Use simple everyday language, no jargon.
                            
                            STOCK: {name} ({ticker.upper()})
                            CURRENT PRICE: {currency} {current_price:.2f}
                            PRICE CHANGE OVER PERIOD: {change:.2f}%
                            PERIOD: {period}
                            
                            Please explain in this format:
                            
                            WHAT THIS COMPANY DOES:
                            [1-2 simple sentences]
                            
                            WHAT THESE NUMBERS MEAN:
                            [Explain the price and change in simple words]
                            
                            IS THIS STOCK:
                            [Choose one: 📈 Growing | 📉 Declining | ➡️ Stable]
                            
                            BEGINNER VERDICT:
                            [Simple honest advice for a beginner - 2 sentences]
                            
                            RISK LEVEL:
                            [Choose one: 🟢 Low Risk | 🟡 Medium Risk | 🔴 High Risk]
                            
                            ONE TIP FOR BEGINNERS:
                            [One practical tip related to this stock]
                            """

                            if client is None:
                                st.error("AI API key not configured. Please set GROQ_API_KEY in .streamlit/secrets.toml.")
                            else:
                                response = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=[{"role": "user", "content": prompt}]
                                )
                                st.markdown("### 🤖 AI Analysis")
                                st.markdown(response.choices[0].message.content)

                except Exception as e:
                    st.error(f"Something went wrong: {e}")

    st.markdown("---")
    st.info("💡 **Indian stocks:** Add .NS at the end (e.g. TCS.NS, RELIANCE.NS)\n\n💡 **US stocks:** Just the symbol (e.g. AAPL, GOOGL, TSLA)")

# =====================
# TAB 2 - LEARN TERMS
# =====================
with tab2:
    st.header("📚 Learn Stock Market Terms")
    st.write("Type any confusing term and AI will explain it simply!")

    term = st.text_input("Enter any stock market term",
              placeholder="e.g. dividend, P/E ratio, bull market, portfolio...")

    if st.button("💡 Explain This Term", key="explain"):
        if not term:
            st.warning("Please enter a term!")
        else:
            with st.spinner("Explaining in simple words..."):
                prompt = f"""
                Explain the stock market term "{term}" to a complete beginner woman
                who has never invested before.
                
                Use this format:
                
                SIMPLE DEFINITION:
                [One sentence explanation like you're talking to a friend]
                
                REAL LIFE EXAMPLE:
                [Relate it to everyday life]
                
                WHY IT MATTERS:
                [Why should a beginner care about this]
                
                REMEMBER:
                [One key takeaway]
                """

                if client is None:
                    st.error("AI API key not configured. Please set GROQ_API_KEY in .streamlit/secrets.toml.")
                else:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.markdown(response.choices[0].message.content)

    # --- Common Terms ---
    st.markdown("---")
    st.markdown("### 🔤 Common Terms to Start With")
    common_terms = [
        "Stock", "Dividend", "Portfolio", "Bull Market",
        "Bear Market", "P/E Ratio", "Market Cap", "IPO"
    ]
    cols = st.columns(4)
    for i, t in enumerate(common_terms):
        with cols[i % 4]:
            st.button(t, key=f"term_{t}")

# =====================
# TAB 3 - SIMULATOR
# =====================
with tab3:
    st.header("💵 Investment Growth Simulator")
    st.write("See how small investments can grow over time!")

    col1, col2 = st.columns(2)
    with col1:
        monthly = st.number_input("Monthly Investment (₹)",
                    min_value=100, max_value=100000,
                    value=500, step=100)
    with col2:
        years = st.slider("Number of Years", 1, 30, 10)

    rate = st.slider("Expected Annual Return (%)", 5, 20, 12)

    if st.button("📊 Calculate Growth", key="simulate"):
        total_invested = monthly * 12 * years
        monthly_rate = rate / 100 / 12
        months = years * 12

        future_value = monthly * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        ) * (1 + monthly_rate)

        profit = future_value - total_invested

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invested", f"₹{total_invested:,.0f}")
        col2.metric("Future Value", f"₹{future_value:,.0f}")
        col3.metric("Total Profit", f"₹{profit:,.0f}")

        # Growth Chart
        values = []
        invested = []
        for m in range(1, months + 1):
            fv = monthly * (
                ((1 + monthly_rate) ** m - 1) / monthly_rate
            ) * (1 + monthly_rate)
            values.append(fv)
            invested.append(monthly * m)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=values,
            name="Portfolio Value",
            line=dict(color="purple", width=2),
            fill="tozeroy"
        ))
        fig.add_trace(go.Scatter(
            y=invested,
            name="Amount Invested",
            line=dict(color="pink", width=2),
            fill="tozeroy"
        ))
        fig.update_layout(
            title="Your Investment Growth Over Time",
            xaxis_title="Months",
            yaxis_title="Value (₹)",
            template="plotly_white",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.success(f"🎉 By investing just ₹{monthly}/month for {years} years you could grow your money to ₹{future_value:,.0f}!")

# =====================
# TAB 4 - QUIZ
# =====================
with tab4:
    st.header("🧠 Test Your Knowledge")
    st.write("Answer these beginner questions!")

    questions = [
        {
            "q": "What is a stock?",
            "options": [
                "A loan from the bank",
                "A small ownership in a company",
                "A type of savings account",
                "A government bond"
            ],
            "answer": "A small ownership in a company"
        },
        {
            "q": "What does 'bull market' mean?",
            "options": [
                "Market is falling",
                "Market is stable",
                "Market is rising",
                "Market is closed"
            ],
            "answer": "Market is rising"
        },
        {
            "q": "What is a dividend?",
            "options": [
                "A fee you pay to buy stocks",
                "A profit shared by company with shareholders",
                "A type of stock chart",
                "A market index"
            ],
            "answer": "A profit shared by company with shareholders"
        },
        {
            "q": "Which is safer for beginners?",
            "options": [
                "Putting all money in one stock",
                "Diversifying across multiple stocks",
                "Only buying expensive stocks",
                "Selling stocks every day"
            ],
            "answer": "Diversifying across multiple stocks"
        }
    ]

    score = 0
    answers = []

    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}: {q['q']}**")
        answer = st.radio("", q["options"], key=f"q{i}", index=None)
        answers.append(answer)
        st.markdown("")

    if st.button("📝 Submit Quiz", key="quiz"):
        score = sum(1 for i, q in enumerate(questions)
                   if answers[i] == q["answer"])
        st.markdown("---")
        if score == 4:
            st.success(f"🏆 Perfect Score! {score}/4 — You're ready to start investing!")
        elif score >= 2:
            st.warning(f"👍 Good job! {score}/4 — Keep learning!")
        else:
            st.error(f"📚 {score}/4 — Go through the Learn Terms tab and try again!")

        for i, q in enumerate(questions):
            if answers[i] == q["answer"]:
                st.markdown(f"✅ Q{i+1}: Correct!")
            else:
                st.markdown(f"❌ Q{i+1}: Wrong — Answer was: **{q['answer']}**")

st.markdown("---")
st.markdown("<center>Made with ❤️ by Twisha Jain | SheInvests — Empowering Women to Invest</center>", unsafe_allow_html=True)
