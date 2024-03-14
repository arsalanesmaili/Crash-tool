import streamlit as st
st.title("Data")
st.markdown("""In this research we used SDOT crash records as the main source of data for analysis. The Seattle Department of Transportation (SDOT) maintains a comprehensive dataset that captures all types of vehicular collisions within the city. This data is collected by the Seattle Police Department (SPD) and recorded by Traffic Records. The SDOT crash data includes collisions that occur at intersections as well as mid-block on a roadway segment. The information is updated daily, ensuring that the dataset is current and reflects the most recent collision events. 
The main attributes of the SDOT crash data include information on the location of the collision, the types of vehicles involved, the nature of the collision (such as angle, rear-end, sideswipe, etc.), and any resultant injuries or fatalities. The SDOT crash data is a vital resource for various stakeholders, including city planners, researchers, and the public, who are interested in understanding traffic safety and collision trends within Seattle. The data is made accessible through platforms like the City of Seattle Open Data portal, which aims to foster transparency and open access to city data for enhancing civic engagement and informed decision-making. 
Types of data provided by SDOT encompass a wide range of transportation-related information beyond just collision data. This includes data on parking, transit, pedestrian and bicycle infrastructure, and roadway assets. The open access to this GIS data through platforms like the City of Seattle's Open Data portal aims to enhance civic engagement and support informed decision-making. 
The data has important attributes including: 
• X and Y as coordinates of the crash location, used for plotting the data on the map and providing geographical distribution information. 
• INCKEY, COLDETKEY, REPORTNO as specific identifiers and keys for each crash. 
• ADDRTYPE to specify the type of location (intersection or midblock). 
• LOCATION, JUNCTIONTYPE which provides the address of the crash location. 
• SEVERITYCODE and SEVERITYDESC to provide information about the severity of each recorded crash. 
• PERSONCOUNT, PEDCOUNT, PEDCYLCOUNT, VEHCOUNT, INJURIES, SERIOUSINJURIES, and FATALITIES to provide information about the people involved in the crash and number of injures or fatalities. 
• INCDATE and INCDTTM to provide information about the time of crash. 
• INATTENTIONIND, UNDERINFL, and SPEEDING to provide information about violations including distraction, being under influence and speeding. 
• WEATHER with information about the weather conditions at the time of crash occurrence. 
• ROADCOND with information about the road surface conditions at the time of crash. 
• LIGHTCOND with information about the lighting conditions at the time of crash.""",unsafe_allow_html=True)