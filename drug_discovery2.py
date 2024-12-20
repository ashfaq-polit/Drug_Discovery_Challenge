# -*- coding: utf-8 -*-
"""Drug_Discovery2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WJKHLiSp7_aNLl_eZqV9KE7iHNOVC6GY

**Install Relevant Packages**
"""

!pip install rdkit
!pip install pubchempy
!pip install bioservices
!pip install biopython

"""**Import Relevant Libraries**"""

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

"""**Import Data**"""

df = pd.read_csv('Deloitte_DrugDiscovery_dataset.csv')

# Display basic information about the dataset
print("Dataset Summary:")
print(df.info())

"""**Little Bit of Exploratory Data Analysis**"""

unique_protein = df['UniProt_ID'].unique()
print(unique_protein)

unique_drug = df['pubchem_cid'].nunique()
print(unique_drug)

unique_protein_drug = pd.concat([df['UniProt_ID'], df['pubchem_cid']]).nunique()
print(unique_protein_drug)

df['kiba_score_estimated'].value_counts()

"""**Sample the Dataset**"""

# Randomly sample 1000 rows
sampled_df = df.sample(n=10000, random_state=42).reset_index(drop=True)
# Set random_state for reproducibility (alternate: df[:1000])
# print(sampled_df)

# Handle missing values if any
sampled_df.dropna(inplace=True)

print(sampled_df.info())
print(sampled_df.head())

"""**Retrieve SMILES strings from the Pubchem IDs**




"""

import pubchempy as pcp

def get_smiles_from_pubchem(pubchem_cid):
    """
    Retrieve SMILES representation for a given PubChem CID using PubChemPy.
    https://pubchempy.readthedocs.io/en/latest/api.html
    """
    try:
        compound = pcp.Compound.from_cid(pubchem_cid)
        return compound.isomeric_smiles
    except Exception as e:
        print(f"Error retrieving SMILES for CID {pubchem_cid}: {e}")
        return None

# import pubchempy as pcp

# def get_smiles_from_pubchem(pubchem_cid, retries=3, delay=0.2):
#     """
#     Retrieve SMILES representation for a compound given its PubChem CID.
#     Retries if the server is busy.
#     """
#     for attempt in range(retries):
#         try:
#             compound = pcp.Compound.from_cid(pubchem_cid)
#             return compound.isomeric_smiles
#         except Exception as e:
#             print(f"Attempt {attempt + 1} failed for CID {pubchem_cid}: {e}")
#             time.sleep(delay)
#     print(f"All retries failed for CID {pubchem_cid}")
#     return None

# def compute_molecular_descriptors_batch(pubchem_cids, batch_size=100):
#     """
#     Compute molecular descriptors in batches to reduce load on PubChem's servers.
#     """
#     results = []
#     for i in range(0, len(pubchem_cids), batch_size):
#         batch = pubchem_cids[i:i + batch_size]
#         batch_results = []
#         for cid in batch:
#             batch_results.append(compute_molecular_descriptors(cid))
#         results.extend(batch_results)
#         print(f"Processed batch {i // batch_size + 1}")
#         time.sleep(1)  # Add a delay between batches
#     return results


# compute_molecular_descriptors_batch(df['pubchem_cid'], batch_size=100)

# # pip install chemspipy
# from chemspipy import ChemSpider
# import pandas as pd

# # Initialize ChemSpider with your API key
# # You can register at https://developer.rsc.org to get an API key
# cs = ChemSpider('FZauBOVA0o1fUZAlcmLTm9vdZogIYJPw2SU3B427')

# def get_smiles_from_chemspider(pubchem_cid):
#     try:
#         compound = cs.get_compound(pubchem_cid)
#         return compound.smiles
#     except Exception as e:
#         print(f"Error retrieving SMILES for CID {pubchem_cid}: {e}")
#         return None

# # Example PubChem CIDs
# sampled_df['pubchem_cid'] = sampled_df['pubchem_cid'].astype(int)
# column_as_list = sampled_df['pubchem_cid'].tolist()
# pubchem_cids = column_as_list #[7428, 65303, 96506] # Replace with your list


# # Fetch SMILES
# pubchem_to_smiles = {cid: get_smiles_from_chemspider(cid) for cid in pubchem_cids}

# # Save to a DataFrame and CSV
# pubchem_cid_smiles = pd.DataFrame(list(pubchem_to_smiles.items()), columns=['pubchem_cid', 'smiles'])
# pubchem_cid_smiles.to_csv('pubchem_cid_smiles.csv', index=False)

# print("SMILES mapping saved!")

# from concurrent.futures import ThreadPoolExecutor
# import time


# def compute_molecular_descriptors_parallel(pubchem_cids):
#     """
#     Compute molecular descriptors in parallel for a list of PubChem CIDs.
#     """
#     with ThreadPoolExecutor() as executor:
#         results = list(executor.map(compute_molecular_descriptors, pubchem_cids))
#     return results


# # Start timing
# start_time = time.time()

# # Compute molecular descriptors in parallel
# sampled_df['pubchem_cid'] = sampled_df['pubchem_cid'].astype(int)
# compound_features = compute_molecular_descriptors_parallel(sampled_df['pubchem_cid'])

# # Convert to DataFrame
# compound_features_df = pd.DataFrame(
#     compound_features,
#     columns=['MolWt', 'MolLogP', 'NumHDonors', 'NumHAcceptors']
# )

# # Stop timing
# end_time = time.time()

# print(f"Time taken for molecular descriptor computation: {end_time - start_time:.2f} seconds")

# print(compound_features_df)

"""**Compute Molecular features of the Drug Molecules from
SMILES Strings**
"""

def compute_molecular_descriptors(pubchem_cid):
    """
    Compute molecular descriptors for a given PubChem CID.
    https://www.rdkit.org/docs/source/rdkit.Chem.Descriptors.html
    """
    # Retrieve the SMILES representation for the compound
    smiles = get_smiles_from_pubchem(pubchem_cid)  # Assumes this function is defined elsewhere
    if smiles:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            # Compute molecular descriptors
            return [
                Descriptors.MolWt(mol),
                Descriptors.MolLogP(mol),
                Descriptors.NumHDonors(mol),
                Descriptors.NumHAcceptors(mol),
                Descriptors.TPSA(mol),  # Topological polar surface area
                Descriptors.FractionCSP3(mol),  # Fraction of sp3 carbons
                Descriptors.NumRotatableBonds(mol),  # Number of rotatable bonds
                Descriptors.NumAromaticRings(mol),  # Number of aromatic rings
                Descriptors.HeavyAtomCount(mol)  # Number of heavy atoms
            ]
    # Return NaN if SMILES is invalid or not found
    return [np.nan] * 9

"""**Create Dataframe for the Molecular Descriptors of the Drugs**



"""

# Assuming 'pubchem_cid' column exists in the DataFrame
sampled_df['pubchem_cid'] = sampled_df['pubchem_cid'].astype(int)

# Apply the function to compute molecular descriptors
compound_features = sampled_df['pubchem_cid'].apply(compute_molecular_descriptors)

# Convert the results to a DataFrame with appropriate column names
compound_features_df = pd.DataFrame(compound_features.tolist(), columns=[
    'MolWt', 'MolLogP', 'NumHDonors', 'NumHAcceptors',
    'TPSA', 'FractionCSP3', 'NumRotatableBonds',
    'NumAromaticRings', 'HeavyAtomCount'
])

print(compound_features_df)

# compound_features_df.to_csv('compound_features_df')

"""**Retrieve Amino Acid Sequence of the Proteins from the UniProt IDs**

"""

# Initialize UniProt service
from bioservices import UniProt
uniprot_service = UniProt()

# Function to retrieve protein sequences from UniProt
def get_protein_sequence(uniprot_id):
    """
    Retrieve the protein sequence for a given UniProt ID using the UniProt service.
    https://bioservices.readthedocs.io/en/latest/_modules/bioservices/uniprot.html
    """
    try:
        result = uniprot_service.retrieve(uniprot_id, frmt="fasta")
        sequence = ''.join(result.split('\n')[1:])  # Extract the sequence
        return sequence
    except Exception as e:
        print(f"Error retrieving sequence for UniProt ID {uniprot_id}: {e}")
        return None

"""**Compute Protein features Relevant to Drug-Protein Binding from Corresponding Amino Acid Sequences**"""

from Bio.SeqUtils.ProtParam import ProteinAnalysis


# Function to encode protein sequence into numerical features
def encode_protein_with_features(uniprot_id):
    """
    Encode the protein sequence into meaningful numerical features.
    https://biopython.org/docs/1.75/api/Bio.SeqUtils.ProtParam.html
    """
    # Retrieve the protein sequence
    sequence = get_protein_sequence(uniprot_id)
    print(f"Protein sequence for {uniprot_id}: {sequence}")

    if sequence:
        try:
            # Remove non-standard amino acids (e.g., 'X') from the sequence
            valid_sequence = ''.join([aa for aa in sequence if aa in "ACDEFGHIKLMNPQRSTVWY"])

            if len(valid_sequence) < len(sequence):
                print(f"Sequence for {uniprot_id} contains non-standard amino acids. Adjusted sequence: {valid_sequence}")

            # Analyze the valid sequence using Biopython
            protein_analysis = ProteinAnalysis(valid_sequence)

            # Extract meaningful features
            features = {
                "length": len(valid_sequence),
                "aromaticity": protein_analysis.aromaticity(),
                "instability_index": protein_analysis.instability_index(),
                "isoelectric_point": protein_analysis.isoelectric_point(),
                "gravy": protein_analysis.gravy(),
                "molecular_weight": protein_analysis.molecular_weight(),
                "flexibility_mean": np.mean(protein_analysis.flexibility()),  # Average flexibility
                "extinction_coeff_reduced": protein_analysis.molar_extinction_coefficient()[0],
                "extinction_coeff_disulfide": protein_analysis.molar_extinction_coefficient()[1],
            }

            # Add secondary structure fractions (helix, sheet, coil)
            secondary_structures = protein_analysis.secondary_structure_fraction()
            features.update({
                "helix_fraction": secondary_structures[0],
                "sheet_fraction": secondary_structures[1],
                "coil_fraction": secondary_structures[2],
            })

            # Include amino acid composition
            aa_composition = protein_analysis.get_amino_acids_percent()
            features.update(aa_composition)

            # Convert features to a list of numerical values
            feature_values = list(features.values())
            return feature_values

        except Exception as e:
            print(f"Error analyzing sequence for UniProt ID {uniprot_id}: {e}")
            # Return NaNs for all features in case of failure
            return [np.nan] * len(features)  # Adjust this based on the actual number of features

    # Return NaNs if the sequence is not found
    return [np.nan] * len(features)  # Adjust this based on the actual number of features

"""**Create Dataframe for the Protein Features**"""

# Apply the function to encode proteins and derive numerical features
protein_features = sampled_df['UniProt_ID'].apply(encode_protein_with_features)

# Define column names for the DataFrame
feature_columns = [
    "length", "aromaticity", "instability_index", "isoelectric_point", "gravy",
    "molecular_weight", "flexibility_mean",
    "extinction_coeff_reduced", "extinction_coeff_disulfide",
    "helix_fraction", "sheet_fraction", "coil_fraction"
] + [f"aa_{aa}" for aa in "ACDEFGHIKLMNPQRSTVWY"]

# Convert extracted features into a DataFrame
protein_features_df = pd.DataFrame(protein_features.tolist(), columns=feature_columns)


print("Protein features successfully extracted and saved!")
print(protein_features_df)

"""**`Combine Drug Features and Protein Features`**"""

# Combine all features
sampled_df['kiba_score_estimated'] = sampled_df['kiba_score_estimated'].map({True: 1, False: 0})
features = pd.concat([compound_features_df, protein_features_df,
                      sampled_df['kiba_score_estimated'].reset_index(drop=True)], axis=1)

# Add kiba_score as the target
target = sampled_df['kiba_score'].reset_index(drop='index')

features

"""**Double-checking if there is any missing value in the Dataframe**"""

# Combine features and target into a single dataframe
data = pd.merge(features, target, left_index = True, right_index = True)

# Remove rows with any NaN or missing values
data = data.dropna()

# Separate features and target
features = data.drop(columns=['kiba_score'])  # Remove the target column to get the features dataframe
target = data['kiba_score']  # Target column

features.columns = features.columns.astype(str)
features

"""**Train-test split**"""

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    features, target, test_size=0.2, random_state=42
)

# Verifying the sizes
print(f"Training set size: {len(X_train)} samples")
print(f"Test set size: {len(X_test)} samples")

"""**Try Different Machine Learning Algorithms for Model Training**"""

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler


# Define a function to train and evaluate models
def train_and_evaluate(model, X_train, y_train, X_test, y_test, model_type=None):
    """
    Train and evaluate a regression model.

    Parameters:
        model: Model instance (e.g., LinearRegression, LGBMRegressor, etc.)
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        model_type: Optional, specify 'DNN' for deep learning models

    Returns:
        A dictionary with RMSE and R2 metrics.
        The trained model is also returned.
    """

    # Train Machine Learning model
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    return {"RMSE": rmse, "R2": r2, "model": model}


# Define all models
models = [
    {"name": "Linear Regression", "model": LinearRegression()},
    {"name": "LightGBM", "model": LGBMRegressor(n_estimators=1000, learning_rate=0.05, random_state=42, verbose=-1)},
    {"name": "Random Forest", "model": RandomForestRegressor(n_estimators=100, random_state=42)},
]

# Initialize variables to track the best model
best_model_info = {"name": None, "rmse": float('inf'), "model": None}

# Train and evaluate each model
for model_info in models:
    print(f"Training {model_info['name']}...")
    metrics = train_and_evaluate(
        model_info["model"],
        X_train, y_train,
        X_test, y_test,
        model_type=model_info.get("type")
    )
    print(f"{model_info['name']} - RMSE: {metrics['RMSE']:.4f}, R2: {metrics['R2']:.4f}\n")

    # Check if this model is the best so far
    if metrics["RMSE"] < best_model_info["rmse"]:
        best_model_info["name"] = model_info["name"]
        best_model_info["rmse"] = metrics["RMSE"]
        best_model_info["model"] = metrics["model"]

"""**Save the best Machine Learning Model**"""

# Print and save the best model
print(f"Best Model: {best_model_info['name']} with RMSE: {best_model_info['rmse']:.4f}")

joblib.dump(best_model_info["model"], "best_model.pkl")
print(f"Model saved as best_model.pkl")

"""**Build a Deep Neural Network for Model Training and Save it**"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import StandardScaler

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Build the Deep Neural Network
dnn_model = Sequential([
    Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.2),
    Dense(64, activation='relu'),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(1)  # Output layer for regression
])

# Compile the model
dnn_model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])

# Train the model
history = dnn_model.fit(X_train_scaled, y_train,
                        validation_split=0.2,
                        epochs=50,
                        batch_size=32,
                        verbose=1)

# Evaluate the model
y_pred_dnn = dnn_model.predict(X_test_scaled).flatten()

# Calculate metrics
rmse_dnn = np.sqrt(mean_squared_error(y_test, y_pred_dnn))
r2_dnn = r2_score(y_test, y_pred_dnn)

print(f"DNN RMSE: {rmse_dnn}, R2 Score: {r2_dnn}")

# Save the model
dnn_model.save('dnn_model.h5')  # Saves the model to an HDF5 file

print("Model saved successfully.")

"""**Test the Model with External Dataset**"""

# Load the external test dataset
external_test_data = pd.read_csv('external_test_dataset.csv')  # Replace with the actual file name

# Handle missing values if any
external_test_data.dropna(inplace=True)

# Retrieve and encode molecular descriptors
external_test_data['pubchem_cid'] = external_test_data['pubchem_cid'].astype(int)
external_compound_features = external_test_data['pubchem_cid'].apply(compute_molecular_descriptors)

# Convert the results to a DataFrame
external_compound_features_df = pd.DataFrame(external_compound_features.tolist(), columns=[
    'MolWt', 'MolLogP', 'NumHDonors', 'NumHAcceptors',
    'TPSA', 'FractionCSP3', 'NumRotatableBonds',
    'NumAromaticRings', 'HeavyAtomCount'
])

# Retrieve and encode protein features
external_protein_features = external_test_data['UniProt_ID'].apply(encode_protein_with_features)

# Define protein feature columns
external_feature_columns = [
    "length", "aromaticity", "instability_index", "isoelectric_point", "gravy",
    "molecular_weight", "flexibility_mean",
    "extinction_coeff_reduced", "extinction_coeff_disulfide",
    "helix_fraction", "sheet_fraction", "coil_fraction"
] + [f"aa_{aa}" for aa in "ACDEFGHIKLMNPQRSTVWY"]

# Convert protein features to DataFrame
external_protein_features_df = pd.DataFrame(external_protein_features.tolist(), columns=external_feature_columns)

# Combine all features
external_features = pd.concat([external_compound_features_df, external_protein_features_df,
                               external_test_data[['kiba_score_estimated']].reset_index(drop=True)], axis=1)

# Remove rows with any missing features
external_features.dropna(inplace=True)

# Standardize features for the deep learning model
external_features_scaled = scaler.transform(external_features)  # Use the scaler fitted on the training data

# Load the saved machine learning model
best_ml_model = joblib.load("best_model.pkl")

# Predict using the best ML model
ml_predictions = best_ml_model.predict(external_features)

# Load the saved deep learning model
from tensorflow.keras.models import load_model
dnn_model = load_model('dnn_model.h5')

# Predict using the DNN model
dnn_predictions = dnn_model.predict(external_features_scaled).flatten()

# Combine predictions with the original test data
external_test_data['kiba_score_pred_ml'] = ml_predictions
external_test_data['kiba_score_pred_dnn'] = dnn_predictions

# Save the predictions to a CSV file
external_test_data.to_csv('external_test_predictions.csv', index=False)

print("Predictions for the external test dataset saved successfully!")