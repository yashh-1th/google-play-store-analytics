# 📱 Google Play Store Data Analytics Dashboard

An interactive dashboard for exploring Google Play Store application data using Python, Pandas, Plotly, and Streamlit.

## 📌 Project Overview

This project analyzes Google Play Store application data and presents the results through interactive visualizations. Users can explore app ratings, sizes, categories, installation counts, pricing, and update activity.

## ✨ Dashboard Features

### 1. Density Analysis

* Explore app size and rating patterns.
* Identify statistical outliers using the IQR method.
* Examine category distributions.

### 2. Sunburst Analysis

* Explore relationships between categories, app types, and rating groups.
* Compare category-level application metrics.

### 3. Calendar Heatmap

* Visualize application update activity over time.

### 4. Monthly Trends

* Explore monthly update activity and related trends.

### 5. Category Heatmap

* Compare categories using available application metrics.
* Explore category performance using adjustable score weights.

### 6. Free vs Paid Analysis

* Compare free and paid applications.
* Explore available ratings, install estimates, and pricing information.

## 🛠️ Technologies Used

* Python
* Pandas
* NumPy
* Plotly
* Streamlit
* Excel/CSV

## 📂 Dataset

The dataset contains information such as:

* App name and category
* Rating and number of reviews
* App size and installs
* App type and price
* Content rating and genres
* Last updated date
* Current version and Android version

## ⚙️ Run the Project Locally

### Prerequisites

Install Python on your computer.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yashh-1th/google-play-store-analytics.git
   ```

2. Open the project folder:

   ```bash
   cd google-play-store-analytics
   ```

3. Install the required libraries:

   ```bash
   pip install -r requirements.txt
   ```

4. Ensure the dataset file is available in the project folder. The dashboard supports `googleplaystore.csv` or `googleplaystore.csv.xlsx`.

5. Start the dashboard:

   ```bash
   python -m streamlit run app.py
   ```

6. Open the local URL displayed in the terminal.

## 📊 Results

The dashboard provides six analytical modules with interactive charts and filters. Users can explore application characteristics and compare metrics across categories and app types.

## ⚠️ Data Limitations

* The dataset does not include country-level information.
* It does not contain historical monthly installation records.
* Monthly trend visualizations represent app update activity, not actual monthly installs.
* Revenue calculations based on installs and price are estimates, not verified revenue.
* Results depend on the available dataset and selected filters.

## 🔮 Future Improvements

* Integrate updated application data.
* Add additional data-quality checks.
* Include verified historical and country-level data when available.
* Improve dashboard filtering and comparison features.

## 👨‍💻 Author

**Yashwanth Pagidimarri**

GitHub: https://github.com/yashh-1th
