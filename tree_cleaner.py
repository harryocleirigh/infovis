import pandas as pd
import time
import geopandas as gpd
from shapely.geometry import Point

# Read the CSV file into a DataFrame
df = pd.read_csv('sf_trees.csv')

# Parse [species] string before and after :: to extract the species name
df['species_latin'] = df['species'].str.split('::').str[0].str.strip()
df['species_english'] = df['species'].str.split('::').str[1].str.strip()

# Drop rows where 'species_latin' is 'Tree(s)'
df = df[df['species_latin'] != 'Tree(s)']

# Create a year feature from the date column
df['year'] = pd.to_datetime(df['date']).dt.year

# Drop any trees planted before 2000
df = df[(df['year'] >= 2000) & (df['year'] <= 2019)]

# Replace empty strings in 'species_english' with NaN
df['species_english'].replace('', pd.NA, inplace=True)

# Drop rows with NaN in 'species_english'
df = df.dropna(subset=['species_english'])

# Drop original species column
df = df.drop(columns=['species'])

# List of values to be replaced with 'Public'
public_caretakers = ['DPW', 'Rec/Park', 'PUC', 'Port', 'SFUSD', 'Dept of Real Estate', 
                     'Fire Dept', 'MTA', 'DPW for City Agency', 'Public Library', 
                     'Police Dept', 'Office of Mayor', 'Purchasing Dept', 'Health Dept', 
                     'Housing Authority', 'Mayor Office of Housing', 'Arts Commission', 
                     'City College']

# Replace the values
df['caretaker'].replace(public_caretakers, 'Public Office', inplace=True)

# For 'PRIVATE', replace with 'Private'
df['caretaker'].replace('Private', 'Residential', inplace=True)

# Drop items not in use to minmise the size of the dataset
df.drop(columns=['legal_status'], inplace=True)
df.drop(columns=['address'], inplace=True)
df.drop(columns=['site_info'], inplace=True)

# Drop rows with NaN in 'dbh', 'latitude' and 'longitude'
df = df[df['dbh'].notnull()]
df = df[df['latitude'].notnull()]
df = df[df['longitude'].notnull()]
df = df[df['site_order'].notnull()]
df = df[df['plot_size'].notnull()]

# Save the cleaned data to a new CSV file
df.to_csv('cleaned_trees.csv', index=False)


print('Cleaning complete')

print()

print('Starting spatial join')

# Load your tree data into a GeoDataFrame to find associated neighbourhoods
neighbourhoods = gpd.read_file('SanFrancisco.Neighborhoods.json')

# Load your tree data into a GeoDataFrame
trees = gpd.read_file('cleaned_trees.csv')

# Convert the tree data points to GeoSeries
trees['geometry'] = trees.apply(lambda row: Point(row.longitude, row.latitude), axis=1)
trees = gpd.GeoDataFrame(trees, geometry='geometry')

# Ensure both GeoDataFrames use the same coordinate reference system
trees = trees.set_crs(neighbourhoods.crs)

# Perform the spatial join
trees_with_neighborhood = gpd.sjoin(trees, neighbourhoods, how="left", op='within')

# Drop all other columns except the ones specified
# trees_with_neighborhood = trees_with_neighborhood[columns_to_keep]

trees_with_neighborhood = trees_with_neighborhood.drop(columns=['geometry'])
trees_with_neighborhood = trees_with_neighborhood.drop(columns=['id'])
trees_with_neighborhood = trees_with_neighborhood.drop(columns=['index_right'])

print('Spatial join complete')
print()
print('Starting native tree search...')

# Finding the native trees

trees_of_ca = pd.read_csv('native_trees_of_ca.csv')
trees_of_sf = pd.read_csv('native_trees_of_sf.csv')

# Create a 'Native' column and set all values to 'Not Native'
trees_with_neighborhood['native'] = 'Not Native'

# If the species is in the list of native trees, set the value to 'Native to California'
trees_with_neighborhood.loc[trees_with_neighborhood['species_latin'].isin(trees_of_ca['Species']), 'native'] = 'Native to California'

# If the species is in the list of native trees, set the value to 'Native to San Francisco'
trees_with_neighborhood.loc[trees_with_neighborhood['species_latin'].isin(trees_of_sf['Species']), 'native'] = 'Native to San Francisco'

print()
print('Native tree search complete')
print('Starting CSV write...')

trees_with_neighborhood = trees_with_neighborhood[trees_with_neighborhood['neighborhood'].notnull()]

# Write the neighborhoods to the csv
trees_with_neighborhood.to_csv('cleaned_trees.csv', index=False)

print('CSV write complete')