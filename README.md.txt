# Google Play Store Data Analytics Dashboard

## Project Overview

An interactive data analytics dashboard built using Python, Pandas, Plotly, and Streamlit to explore Google Play Store applications, ratings, categories, installs, app sizes, and pricing.

## Features

* **Density Analysis:** Explore app size, ratings, distributions, and outliers.
* **Sunburst Analysis:** Visualize app categories, app types, and rating groups.
* **Calendar Heatmap:** Explore app update activity over time.
* **Monthly Trends:** Analyze monthly app update activity and trends.
* **Category Heatmap:** Compare app categories using multiple metrics.
* **Free vs Paid Analysis:** Compare free and paid applications.

## Technologies Used

* Python
* Pandas
* NumPy
* Plotly
* Streamlit
* Excel/CSV dataset

## Dataset

The project uses Google Play Store application data containing app names, categories, ratings, reviews, sizes, installs, prices, content ratings, genres, and update dates.

## Installation and Setup

1. Install Python on your computer.

2. Download or clone this project.

3. Open a terminal inside the project folder.

4. Install the required libraries:

   `pip install -r requirements.txt`

5. Run the dashboard:

   `python -m streamlit run app.py`

6. Open the local URL displayed in the terminal.

## Project Limitations

The dataset does not contain country-level information or historical monthly install records. Therefore, monthly trend charts represent app update activity rather than actual monthly installs. Revenue figures are estimates based on available install and price values, not verified company revenue.

## Conclusion

This project demonstrates how Python-based data cleaning, exploratory data analysis, interactive visualizations, and Streamlit can be combined to build an application analytics dashboard.
