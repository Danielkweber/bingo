import streamlit as st
import matplotlib.pyplot as plt
import textwrap
import random
import json
import os
from openai import OpenAI


def parse_items_with_llm(text: str) -> list[str]:
    """Use OpenRouter to parse user text into bingo items."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )

    response = client.chat.completions.create(
        model="anthropic/claude-3-haiku",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant that extracts bingo card items from user input.
Extract individual items/goals from the user's text and return them as a JSON array of strings.
Keep each item concise (under 30 characters if possible).
Return ONLY the JSON array, no other text.""",
            },
            {"role": "user", "content": text},
        ],
    )

    result = response.choices[0].message.content.strip()
    # Handle potential markdown code blocks
    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]
        result = result.strip()

    return json.loads(result)


def generate_bingo_card(items: list[str], title: str = "BINGO GOALS") -> plt.Figure:
    """Generate a bingo card figure from items."""
    # Pad or trim to 24 items (25 squares minus center free space)
    if len(items) < 24:
        all_slots = items + [""] * (24 - len(items))
    else:
        all_slots = items[:24]

    random.shuffle(all_slots)

    # Insert the Free Square at the center (index 12)
    all_slots.insert(12, "FREE:\nAppreciate Life")

    # Create the Visual
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)

    for i in range(5):
        for j in range(5):
            # Calculate index (flipped j to fill from top-down)
            idx = (4 - j) * 5 + i
            label = all_slots[idx]

            # Wrap text for the squares
            wrapped_label = "\n".join(textwrap.wrap(label, width=15))

            # Styling: Center square is pink, others are white
            face_color = "#fff0f3" if idx == 12 else "white"

            rect = plt.Rectangle(
                (i, j), 1, 1, facecolor=face_color, edgecolor="#333333", lw=1.5
            )
            ax.add_patch(rect)

            ax.text(
                i + 0.5,
                j + 0.5,
                wrapped_label,
                ha="center",
                va="center",
                fontsize=10,
                fontweight="medium",
                family="sans-serif",
            )

    # Add B-I-N-G-O Headers
    headers = ["B", "I", "N", "G", "O"]
    for i, h in enumerate(headers):
        ax.text(
            i + 0.5,
            5.3,
            h,
            ha="center",
            va="center",
            fontsize=35,
            fontweight="bold",
            color="#1a1a1a",
        )

    ax.set_axis_off()
    ax.text(
        2.5,
        6.0,
        title,
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color="#1a1a1a",
    )
    ax.set_ylim(0, 6.5)
    plt.tight_layout()

    return fig


# Streamlit UI
st.set_page_config(page_title="Bingo Card Generator", page_icon="🎯", layout="centered")

st.title("Bingo Card Generator")
st.markdown("Enter your goals or items below and generate a custom bingo card!")

user_input = st.text_area(
    "Enter your bingo items:",
    height=200,
    placeholder="Enter items in any format:\n- Go skiing\n- Read 10 books\n- Learn a new language\n\nOr: skiing, reading, dancing, cooking...",
)

title = st.text_input("Card Title", value="2025 GOALS")

if st.button("Generate Bingo Card", type="primary"):
    if not user_input.strip():
        st.error("Please enter some items first!")
    elif not os.environ.get("OPENROUTER_API_KEY"):
        st.error("Please set OPENROUTER_API_KEY environment variable")
    else:
        with st.spinner("Parsing your items..."):
            try:
                items = parse_items_with_llm(user_input)
                st.success(f"Found {len(items)} items!")

                with st.expander("View parsed items"):
                    for i, item in enumerate(items, 1):
                        st.write(f"{i}. {item}")

            except Exception as e:
                st.error(f"Error parsing items: {e}")
                items = None

        if items:
            with st.spinner("Generating bingo card..."):
                fig = generate_bingo_card(items, title=title)
                st.pyplot(fig)
                plt.close(fig)
