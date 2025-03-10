import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from PIL import Image

# Load Data 
datasets = {
    "Dongsi": pd.read_csv("https://raw.githubusercontent.com/rakhapta/Beijing_AQI/refs/heads/main/dashboard/dongsi.csv"),
    "Huairou": pd.read_csv("https://raw.githubusercontent.com/rakhapta/Beijing_AQI/refs/heads/main/dashboard/huairou.csv"),
    "Tiantian": pd.read_csv("https://raw.githubusercontent.com/rakhapta/Beijing_AQI/refs/heads/main/dashboard/tiantan.csv"),

}

# Konversi waktu pada setiap dataset
for df in datasets.values():
    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]], errors="coerce")

# Load Images
district_images = {
    "Dongsi": "https://raw.githubusercontent.com/rakhapta/Beijing_AQI/main/dashboard/dongsi.jpg",
    "Huairou": "https://raw.githubusercontent.com/rakhapta/Beijing_AQI/main/dashboard/huairou.jpg",
    "Tiantan": "https://raw.githubusercontent.com/rakhapta/Beijing_AQI/main/dashboard/tiantan.jpg"
}
def pm25_to_aqi_category(pm25):
    if pm25 <= 12:
        return "Good"
    elif pm25 <= 35.4:
        return "Moderate"
    elif pm25 <= 55.4:
        return "Unhealthy for Sensitive Groups"
    elif pm25 <= 150.4:
        return "Unhealthy"
    elif pm25 <= 250.4:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def pm25_to_aqi_color(pm25):
    if pm25 <= 12:
        return '#00E400'  # Green (Good)
    elif pm25 <= 35.4:
        return '#FFFF00'  # Yellow (Moderate)
    elif pm25 <= 55.4:
        return '#FF7E00'  # Orange (Unhealthy for Sensitive Groups)
    elif pm25 <= 150.4:
        return '#FF0000'  # Red (Unhealthy)
    elif pm25 <= 250.4:
        return '#8F3F97'  # Purple (Very Unhealthy)
    else:
        return '#7E0023'  # Maroon (Hazardous)
# Navigasi Sidebar
if "page" not in st.session_state:
    st.session_state["page"] = "🏠 Homepage"
if "selected_district" not in st.session_state:
    st.session_state["selected_district"] = "Dongsi"

# Define pages with emojis
pages = ["🏠 Homepage", "📊 District Dashboard"]

st.sidebar.markdown("### Select Pages")  # Default header, bigger than in radio (kecil kurang suka)

# Create a radio button to select pages
page = st.sidebar.radio(" ", pages, index=pages.index(f"{st.session_state['page']}"))

st.session_state["page"] = page

if page == "🏠 Homepage":
    st.title("🌆 Air Pollution Dashboard - Beijing Districts")
    st.subheader("📌 PM2.5 Comparison Between Districts")
    
    fig, ax = plt.subplots()
    sns.barplot(
        x=list(datasets.keys()), 
        y=[df["PM2.5"].mean() for df in datasets.values()], 
        palette="coolwarm", 
        ax=ax
    )

    # Add labels for the bars (actual PM2.5 mean values)
    for i, df in enumerate(datasets.values()):
        mean_pm25 = df["PM2.5"].mean()
        ax.text(i, mean_pm25 + 1, f"{mean_pm25:.2f}", ha='center', va='bottom', fontsize=10)

    # Highlight the district with the highest PM2.5
    max_index = [df["PM2.5"].mean() for df in datasets.values()].index(max([df["PM2.5"].mean() for df in datasets.values()]))
    ax.patches[max_index].set_edgecolor('black')
    ax.patches[max_index].set_linewidth(2)

    # Improve axis labels and title
    plt.xlabel("District", fontsize=12)
    plt.ylabel("Average PM2.5 Level (µg/m³)", fontsize=12)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    # Display the updated plot
    st.pyplot(fig)

    st.subheader("📌 Correlation Between PM2.5 and Meteorological Factors Across All Districts")

    # Combine data and calculate correlation
    combined_data = pd.concat([df.assign(District=district) for district, df in datasets.items()])
    corr = combined_data[["PM2.5", "TEMP", "PRES", "WSPM", "DEWP", "RAIN"]].corr()

    # Create a heatmap with explanations
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        corr,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"shrink": 0.8, "label": "Correlation Coefficient"}
    )

    # Title and labels
    plt.title("Correlation Between PM2.5 and Meteorological Factors", fontsize=14, pad=15)
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.yticks(fontsize=10)

    # Display heatmap
    st.pyplot(fig)

    # Add explanation
    st.markdown("""
    ### How to Interpret This Heatmap:
    - **What is Correlation?**: Correlation measures the strength and direction of the relationship between two variables.
    - **Positive Correlation (Red)**: As one variable increases, the other tends to increase.
    - **Negative Correlation (Blue)**: As one variable increases, the other tends to decrease.
    - **Closer to 0**: Weak or no correlation between variables.
    - **Highlights**:
    - Wind Speed (WSPM) has a weak negative correlation with PM2.5 (-0.28), indicating it may help disperse air pollutants.
    - Dew Point (DEWP) shows a slight positive correlation with PM2.5 (0.15), suggesting more humid conditions might retain pollutants.

    #### Want More Details?
    You can explore individual district dashboards to better understand the localized relationships between meteorological factors and PM2.5 levels.
    """)


    st.subheader("📌 PM2.5 Levels by Hour of the Day Across Districts")

    # Add a column to each dataset to identify the district
    for district_name, df in datasets.items():
        df["District"] = district_name  # Add a 'District' column
        df["hour"] = pd.to_datetime(df["datetime"]).dt.hour  # Extract the hour from the 'datetime' column

    # Combine all datasets into a single DataFrame
    combined_data = pd.concat(datasets.values(), ignore_index=True)

    # Group by District and hour, then calculate the average PM2.5 levels
    hourly_avg = combined_data.groupby(["District", "hour"])["PM2.5"].mean().reset_index()

    # Create the plot
    fig, ax = plt.subplots()
    for district in hourly_avg["District"].unique():
        district_data = hourly_avg[hourly_avg["District"] == district]
        plt.plot(
            district_data["hour"], 
            district_data["PM2.5"], 
            marker="o", 
            linestyle="-", 
            label=district
        )

    # Add a horizontal line for unhealthy threshold
    plt.axhline(y=75, color='r', linestyle='--', label="Unhealthy Level")

    # Add title, labels, and legend
    plt.xlabel("Hour of the Day", fontsize=12)
    plt.ylabel("Average PM2.5 Level (µg/m³)", fontsize=12)
    plt.legend(title="District", fontsize=10)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    # Display the plot
    st.pyplot(fig)

    st.subheader("📷 Select a District to View Details")
    col1, col2, col3 = st.columns(3)
    
    for i, (district, image_path) in enumerate(district_images.items()):
        img = Image.open(image_path)
        with [col1, col2, col3][i]:
            st.image(img, caption=district, use_container_width=True)
            if st.button(f"Select {district}"):
                st.session_state["selected_district"] = district
                st.session_state["page"] = "📊 District Dashboard"
                st.rerun()
    
    st.subheader("🌍 Map of Air Pollution Levels in Beijing")
    district_locations = {
        "Dongsi": {"lat": 39.929, "lon": 116.417},
        "Huairou": {"lat": 40.317, "lon": 116.637},
        "Tiantan": {"lat": 39.886, "lon": 116.412}
    }
    avg_pm25_by_district = {name: df["PM2.5"].mean() for name, df in datasets.items()}
    m = folium.Map(location=[40, 116.7], zoom_start=9)
    
    for district, pm25 in avg_pm25_by_district.items():
        if district in district_locations:
            lat, lon = district_locations[district]["lat"], district_locations[district]["lon"]
            color = pm25_to_aqi_color(pm25)
            folium.CircleMarker(
                location=[lat, lon],
                radius=10,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup = f"<b>{district}</b>: {pm25:.2f} µg/m³<br>Category: {pm25_to_aqi_category(pm25)}<br>"
            ).add_to(m)
    
    folium_static(m)
else:
    selected_district = st.sidebar.selectbox("Select a district", list(datasets.keys()), index=list(datasets.keys()).index(st.session_state["selected_district"]))
    st.session_state["selected_district"] = selected_district
    df = datasets[selected_district]
    avg_pm25 = df["PM2.5"].mean()

    aqi_color = pm25_to_aqi_color(avg_pm25)

    st.title(f"📊 Air Pollution Dashboard - {selected_district}")
    st.subheader("📌 Average PM2.5 Levels by District")
    fig, ax = plt.subplots()
    sns.barplot(x=list(datasets.keys()), 
                y=[df["PM2.5"].mean() for df in datasets.values()], 
                palette=["red" if d == selected_district else "blue" for d in datasets.keys()])
    plt.xlabel("District")
    plt.ylabel("PM2.5 Level")
    st.pyplot(fig)
    
    st.subheader("📌 Correlation Between PM2.5 and Meteorological Factors")

    # Compute the correlation matrix
    corr = df[["PM2.5", "TEMP", "PRES", "WSPM", "DEWP", "RAIN"]].corr()

    # Create a heatmap with added explanations
    fig, ax = plt.subplots(figsize=(8, 6))  # Slightly larger for better readability
    sns.heatmap(
        corr,
        annot=True,
        cmap="coolwarm",
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"shrink": 0.8, "label": "Correlation Coefficient"}
    )

    # Add a title and explanation for correlation metrics
    plt.title("Correlation Between PM2.5 and Meteorological Factors", fontsize=14, pad=15)
    plt.xlabel("Factors", fontsize=12)
    plt.ylabel("Factors", fontsize=12)

    # Add textual annotations (in the streamlit app) to explain correlation
    st.markdown("""
    #### How to Interpret the Heatmap:
    - **What is Correlation?**: Correlation measures the strength and direction of the relationship between two variables, ranging from **-1 (strong negative)** to **+1 (strong positive)**. 
    - **Positive Correlation (Red)**: As one factor increases, the other tends to increase (e.g., higher dew point correlates with higher PM2.5).
    - **Negative Correlation (Blue)**: As one factor increases, the other tends to decrease (e.g., higher wind speed correlates with lower PM2.5).
    - **Closer to 0**: Weak or no correlation between the variables.
    """)

    # Display the updated heatmap
    st.pyplot(fig)

    
    st.subheader("📌 PM2.5 Levels by Hour of the Day")
    if "hour" in df.columns:
        hourly_avg = df.groupby(df["datetime"].dt.hour)["PM2.5"].mean()
        fig, ax = plt.subplots()
        plt.plot(hourly_avg, marker="o", linestyle="-")
        plt.axhline(y=75, color='r', linestyle='--', label="Unhealthy Level")
        plt.xlabel("Hour of the Day")
        plt.ylabel("PM2.5 Level")
        plt.title(f"Average PM2.5 Levels in {selected_district}")
        st.pyplot(fig)
    
    
    st.markdown(f'<p style="color:{aqi_color}; font-size:20px;">AQI Level: {avg_pm25:.2f} µg/m³</p>', unsafe_allow_html=True)
