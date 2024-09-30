import sys
import subprocess

# Function to install a package
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install necessary libraries
install("streamlit")
install("pandas")
install("geopandas")
install("shapely")
install("matplotlib")
install("contextily")
install("folium")
install("streamlit-folium")
install("seaborn")
install("numpy<2")
# import libraries
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import contextily as ctx
import folium
import streamlit_folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import seaborn as sns
import time

# Streamlit app
st.title('Interactive Environment for Seattle Traffic Crashes')
# loading datasets
start_time = time.time()
progress_bar = st.sidebar.progress(0)
progress_text = st.sidebar.text('Loading Data... 0%')
df = pd.read_csv('final_df1.csv')
progress_bar.progress(25)
progress_text.text('Loading Data... 25%')
seattle_gdf = gpd.read_file('tract20_king_county1.shp')
progress_bar.progress(50)
progress_text.text('Loading Data... 50%')
end_time = time.time()
st.write(f"Data loaded in {end_time - start_time:.2f} seconds.")

# pre-processing
start_time = time.time()
geometry = [Point(xy) for xy in zip(df['x'], df['y'])]
crash_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:2926")
progress_bar.progress(75)
progress_text.text('Preparing Visualizations... 75%')
merged_gdf = gpd.sjoin(crash_gdf, seattle_gdf, how="inner", predicate="within")
end_time = time.time()
progress_bar.progress(100)
progress_text.text('Data Loaded and Processed Successfully')
st.write(f"Preprocessing: {end_time - start_time:.2f} seconds.")

progress_bar.progress(0)
progress_text.text('')

# Sidebar for selecting severity, collision type, and year
severity_options = merged_gdf['SEVERITYDESC'].unique().tolist()
severity_options.append("Total")  
selected_severity = st.sidebar.selectbox('Select Severity', severity_options)

collision_type_options = merged_gdf['COLLISIONTYPE'].unique().tolist()
collision_type_options.append("All")  
selected_collision_type = st.sidebar.selectbox('Select Collision Type', collision_type_options)

# Add a range slider for selecting years
year_range = st.sidebar.slider('Select Year Range', min_value=int(merged_gdf['Year'].min()),
                               max_value=int(merged_gdf['Year'].max()),
                               value=(int(merged_gdf['Year'].min()), int(merged_gdf['Year'].max())))

# Add dropdown for normalization of the first map
normalization_options = ["Count", "Normalized by Population", "Normalized by Area"]
selected_normalization = st.sidebar.selectbox('Select Normalization for the First Map', normalization_options)

fig, ax = plt.subplots(figsize=(12, 12))

st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>1. Traffic Crashes Aggregated on Census Tracts</h3>", unsafe_allow_html=True)

progress_text.text('Updating maps and plots...')
for i in range(5):
    progress_bar.progress((i+1) * 20)  
    time.sleep(0.5)  
# Function to update the map based on selected severity, collision type, and year
def update_map_matplotlib(selected_severity, selected_collision_type, year_range, selected_normalization, ax):
    
    start_time = time.time()

    if selected_severity == "Total":
       
        filtered_gdf = merged_gdf
    else:
        
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
        
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]
   
    crash_count = filtered_gdf['GEOID20'].value_counts()

    seattle_gdf_filtered = seattle_gdf.merge(crash_count, left_on='GEOID20', right_index=True, how='left')

     # Normalization based on selected option
    if selected_normalization == "Normalized by Population":
        seattle_gdf_filtered['normalized_count'] = seattle_gdf_filtered['count']*100000 / seattle_gdf_filtered['2020 PL da']
        column_to_plot = 'normalized_count'
    elif selected_normalization == "Normalized by Area":
        seattle_gdf_filtered['normalized_count'] = seattle_gdf_filtered['count'] / seattle_gdf_filtered['areasqmile']  
        column_to_plot = 'normalized_count'
    else:
        column_to_plot = 'count'

    # Plot the map
    seattle_gdf_filtered.plot(ax=ax, column=column_to_plot, cmap='Oranges', linewidth=0.25, edgecolor='black', alpha=0.7, legend=True, vmin=seattle_gdf_filtered[column_to_plot].min(), vmax=seattle_gdf_filtered[column_to_plot].max())


    ctx.add_basemap(ax, crs=seattle_gdf_filtered.crs, source=ctx.providers.CartoDB.Positron)

    plt.xlim(1240000, 1300000)
    plt.ylim(180000, 275000)

    if selected_normalization == "Normalized by Population":
        colorbar_label = 'Number of Crashes Normalized by Population (crash per 100,000 people)'
    elif selected_normalization == "Normalized by Area":
        colorbar_label = 'Number of Crashes Normalized by Area (crash per square mile)'
    else:
        colorbar_label = 'Number of Crashes'

    cbar = ax.get_figure().get_axes()[1]
    cbar.set_ylabel(colorbar_label, rotation=270, labelpad=15)

    ax.set_xticks([])
    ax.set_yticks([])

    legend = ax.get_legend()
    if legend:
        legend.set_title('Count of Crashes')

    st.pyplot(fig)

    end_time = time.time() 
    duration = end_time - start_time 
    st.write(f"Census tract level map updated in {duration:.2f} seconds.") 



# Function to update the Folium map based on selected severity, collision type, and year
def update_map_folium(selected_severity, selected_collision_type, year_range):
    start_time = time.time()

    if selected_severity == "Total":
        
        filtered_gdf = merged_gdf
    else:
        
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
       
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    folium_map = folium.Map(location=[47.6062, -122.3321], zoom_start=15, control_scale=True)

    heat_data = [[row['latitude'], row['longitude']] for index, row in filtered_gdf.iterrows()]

    HeatMap(heat_data).add_to(folium_map)

    folium_static(folium_map)

    end_time = time.time() 
    duration = end_time - start_time 
    st.write(f"Interactive map updated in {duration:.2f} seconds.") 


# Function to update the monthly distribution plot based on selected severity, collision type, and year
def update_monthly_distribution(selected_severity, selected_collision_type, year_range):
    start_time = time.time()
    if selected_severity == "Total":

        filtered_gdf = merged_gdf
    else:
       
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
        
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    plt.figure(figsize=(10, 6))
    sns.countplot(x='Month', data=filtered_gdf, palette='viridis', order=range(1, 13))
    plt.xlabel('Month')
    plt.ylabel('Number of Crashes')
    plt.title('Monthly Distribution of Crashes')

    st.bar_chart(filtered_gdf['Month'].value_counts())


# Function to update the day of week distribution plot based on selected severity, collision type, and year
def update_daily_distribution(selected_severity, selected_collision_type, year_range):
    if selected_severity == "Total":
      
        filtered_gdf = merged_gdf
    else:
       
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
       
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]


    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    filtered_gdf['DayOfWeek'] = pd.Categorical(filtered_gdf['DayOfWeek'], categories=day_order, ordered=True)

    plt.figure(figsize=(10, 6))
    sns.countplot(x='DayOfWeek', data=filtered_gdf, palette='viridis')
    plt.xlabel('Day of Week')
    plt.ylabel('Number of Crashes')
    plt.title('Daily Distribution of Crashes')

    st.bar_chart(filtered_gdf['DayOfWeek'].value_counts())


# Function to update the day of week distribution plot based on selected severity, collision type, and year
def update_time_distribution(selected_severity, selected_collision_type, year_range):
    if selected_severity == "Total":
    
        filtered_gdf = merged_gdf
    else:
    
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
       
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    Time_order = ['7 to 10', '10 to 14', '14 to 18', '18 to 22', '22 to 7']
    filtered_gdf['Time Category'] = pd.Categorical(filtered_gdf['Time Category'], categories=Time_order, ordered=True)

    plt.figure(figsize=(10, 6))
    sns.countplot(x='Time Category', data=filtered_gdf, palette='viridis')
    plt.xlabel('Time of day')
    plt.ylabel('Number of Crashes')
    plt.title('Time Distribution of Crashes')

    st.bar_chart(filtered_gdf['Time Category'].value_counts())



# Function to update the monthly distribution plot based on selected severity, collision type, and year
def update_weather_distribution(selected_severity, selected_collision_type, year_range):
    if selected_severity == "Total":
      
        filtered_gdf = merged_gdf
    else:
     
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
    
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    plt.figure(figsize=(10, 6))
    sns.countplot(x='WEATHER', data=filtered_gdf, palette='viridis', order=range(1, 13))
    plt.xlabel('Weather')
    plt.ylabel('Number of Crashes')
    plt.title('Weather type Distribution of Crashes')

    st.bar_chart(filtered_gdf['WEATHER'].value_counts())




# Function to update the monthly distribution plot based on selected severity, collision type, and year
def update_road_distribution(selected_severity, selected_collision_type, year_range):
    if selected_severity == "Total":
    
        filtered_gdf = merged_gdf
    else:
     
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
   
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    plt.figure(figsize=(10, 6))
    sns.countplot(x='ROADCOND', data=filtered_gdf, palette='viridis', order=range(1, 13))
    plt.xlabel('Road Condition')
    plt.ylabel('Number of Crashes')
    plt.title('Road type Distribution of Crashes')

    st.bar_chart(filtered_gdf['ROADCOND'].value_counts())




# Function to update the monthly distribution plot based on selected severity, collision type, and year
def update_light_distribution(selected_severity, selected_collision_type, year_range):
    if selected_severity == "Total":
 
        filtered_gdf = merged_gdf
    else:

        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
    
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

 
    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]


    plt.figure(figsize=(10, 6))
    sns.countplot(x='LIGHTCOND', data=filtered_gdf, palette='viridis', order=range(1, 13))
    plt.xlabel('Light Condition')
    plt.ylabel('Number of Crashes')
    plt.title('Light condition Distribution of Crashes')

    st.bar_chart(filtered_gdf['LIGHTCOND'].value_counts())
    duration = end_time - start_time 
    st.write(f"Plots created in {duration:.2f} seconds.") 
    progress_text.text('Maps and Plots Updated Successfully')


    # Function to update the percentage of underinfluenced crashes based on selected severity, collision type, and year
def update_underinfluence_percentage(selected_severity, selected_collision_type, year_range):
    start_time = time.time()
    if selected_severity == "Total":

        filtered_gdf = merged_gdf
    else:
     
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":
  
        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

 
    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    total_crashes = len(filtered_gdf)
    underinfluenced_crashes = len(filtered_gdf[filtered_gdf['UNDERINFL'] == 1])
    percentage_underinfluence = (underinfluenced_crashes / total_crashes) * 100

    st.markdown(f"<p style='font-size:30px; color:red;'>{percentage_underinfluence:.2f}%</p>", unsafe_allow_html=True)
    end_time = time.time() 
    duration = end_time - start_time 
    st.write(f"Underinfluenced crashes percentage calculated in {duration:.2f} seconds.") 

    
def update_speeding_percentage(selected_severity, selected_collision_type, year_range):
    start_time = time.time()
    if selected_severity == "Total":

        filtered_gdf = merged_gdf
    else:
     
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":

        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    total_crashes = len(filtered_gdf)
    speeding_crashes = len(filtered_gdf[filtered_gdf['SPEEDING'] == 'Y'])
    percentage_speeding = (speeding_crashes / total_crashes) * 100

    # Display the percentage in Streamlit with larger font size and red color using Markdown
    st.markdown(f"<p style='font-size:30px; color:red;'>{percentage_speeding:.2f}%</p>", unsafe_allow_html=True)

    end_time = time.time() 
    duration = end_time - start_time 
    st.write(f"Speeding crashes percentage calculated in {duration:.2f} seconds.") 


def update_addrtype_percentage(selected_severity, selected_collision_type, year_range):
    start_time = time.time()
    if selected_severity == "Total":

        filtered_gdf = merged_gdf
    else:
  
        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":

        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    total_crashes = len(filtered_gdf)

    block_crashes = len(filtered_gdf[filtered_gdf['ADDRTYPE'] == 'Block'])
    intersection_crashes = len(filtered_gdf[filtered_gdf['ADDRTYPE'] == 'Intersection'])

    percentage_block = (block_crashes / total_crashes) * 100
    percentage_intersection = (intersection_crashes / total_crashes) * 100

    st.markdown(f"<p style='font-size:20px;'>Percentage of crashes at Midblocks: {percentage_block:.2f}%</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:20px;'>Percentage of crashes at Intersections: {percentage_intersection:.2f}%</p>", unsafe_allow_html=True)

    end_time = time.time() 
    duration = end_time - start_time 
    st.write(f"Address type percentages calculated in {duration:.2f} seconds.") 


def update_crash_count(selected_severity, selected_collision_type, year_range):
    if selected_severity == "Total":
        filtered_gdf = merged_gdf
    else:

        filtered_gdf = merged_gdf[merged_gdf['SEVERITYDESC'] == selected_severity]

    if selected_collision_type != "All":

        filtered_gdf = filtered_gdf[filtered_gdf['COLLISIONTYPE'] == selected_collision_type]

    filtered_gdf = filtered_gdf[(filtered_gdf['Year'] >= year_range[0]) & (filtered_gdf['Year'] <= year_range[1])]

    total_crashes = len(filtered_gdf)

    st.markdown(f"<p style='font-size:20px;'>Total Number of Crashes: {total_crashes}</p>", unsafe_allow_html=True)

# Update the total number of crashes based on the selected severity, collision type, and year
update_crash_count(selected_severity, selected_collision_type, year_range)



# Update the matplotlib map based on the selected severity, collision type, and year
update_map_matplotlib(selected_severity, selected_collision_type, year_range, selected_normalization, ax)
# Add text before the second map
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>2. Traffic crashes interactive map</h3>", unsafe_allow_html=True)

# Update the Folium map based on the selected severity, collision type, and year
update_map_folium(selected_severity, selected_collision_type, year_range)
# Add text before the monthly distribution plot
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>3. Traffic crashes monthly distribution</h3>", unsafe_allow_html=True)
# Update the monthly distribution plot based on the selected severity, collision type, and year
update_monthly_distribution(selected_severity, selected_collision_type, year_range)

# Add text before the daily distribution plot
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>4. Traffic crashes daily distribution</h3>", unsafe_allow_html=True)
update_daily_distribution(selected_severity, selected_collision_type, year_range)

# Add text before the daily distribution plot
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>5. Traffic crashes time distribution</h3>", unsafe_allow_html=True)
update_time_distribution(selected_severity, selected_collision_type, year_range)

# Add text before the daily distribution plot
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>6. Traffic crashes and weather distribution</h3>", unsafe_allow_html=True)
update_weather_distribution(selected_severity, selected_collision_type, year_range)


# Add text before the daily distribution plot
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>7. Traffic crashes road condition distribution</h3>", unsafe_allow_html=True)
update_road_distribution(selected_severity, selected_collision_type, year_range)


# Add text before the daily distribution plot
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>8. Traffic crashes light condition distribution</h3>", unsafe_allow_html=True)
update_light_distribution(selected_severity, selected_collision_type, year_range)


# Add text before the underinfluence percentage display
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>9. Percentage of underinfluenced crashes</h3>", unsafe_allow_html=True)

# Update the underinfluence percentage display based on the selected severity, collision type, and year
update_underinfluence_percentage(selected_severity, selected_collision_type, year_range)

# Add text before the speeding percentage display
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>10. Percentage of crashes involving speeding</h3>", unsafe_allow_html=True)
update_speeding_percentage(selected_severity, selected_collision_type, year_range)

# Add text before the address type percentage display
st.markdown("<h3 style='color: #3498db; font-family: Arial, sans-serif;'>11. Percentage of crashes by Location Type</h3>", unsafe_allow_html=True)
update_addrtype_percentage(selected_severity, selected_collision_type, year_range)